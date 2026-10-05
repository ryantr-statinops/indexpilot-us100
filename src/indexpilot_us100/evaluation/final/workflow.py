"""Frozen evaluation, resumable scenario execution and independent replay."""
from datetime import datetime,timezone
import json
from pathlib import Path
import tempfile
import polars as pl
from indexpilot_us100.portfolio.market import load_market_data
from indexpilot_us100.portfolio.config import SimulationConfig
from ..export import file_hash,write_json,git_revision
from .aggregation import aggregate_seed_results
from .artifacts import check_run,store_run,write_table
from .comparison import paired_comparison
from .config import EvaluationConfig
from .history import ExperimentLedger,run_lock
from .matrix import scenarios,evaluate_scenario
from .protocol import validate_protocol,environment,frozen_path
from .windows import build_test_segment
from .yearly import yearly_summary

SUMMARY_FILES=('primary_summary.csv','primary_summary.json','scenario_summary.csv','scenario_summary.json','seed_summary.csv','seed_summary.json','paired_comparison.csv','paired_comparison.json','yearly_summary.csv','yearly_summary.json','diagnostics.json')


def evaluation_config(protocol):
    values=dict(protocol['evaluation_config'])
    values['seeds']=tuple(values['seeds']);values['costs_bps']=tuple(values['costs_bps'])
    return EvaluationConfig(**values)


def ledger_for(root):
    return ExperimentLedger(Path(root).parent/'experiment-ledger.jsonl')


def checked_scores(root,protocol):
    return [check_run(frozen_path(root,'runs/'+row['scenario_id']),protocol['protocol_id']) for row in scenarios(protocol)]


def check_complete(root,protocol):
    root=Path(root); manifest=json.loads((root/'run_manifest.json').read_text())
    if manifest.get('protocol_id')!=protocol['protocol_id'] or manifest.get('artifact_type')!='indexpilot-stage-4':
        raise ValueError('Completed run protocol mismatch')
    actual={name:file_hash(root/name) for name in SUMMARY_FILES}
    if manifest.get('summary_hashes')!=actual: raise ValueError('Completed summary integrity failed')
    scores=checked_scores(root,protocol)
    if manifest.get('scenarios')!=scores: raise ValueError('Completed scenario inventory mismatch')
    return manifest


def summarize(root,protocol,scores):
    root=Path(root);config=protocol['evaluation_config']
    primary=[row for row in scores if row['seed']==config['primary_seed'] and row['cost_bps']==config['primary_cost_bps']]
    write_table(root,'scenario_summary',scores)
    write_table(root,'primary_summary',primary)
    write_table(root,'seed_summary',aggregate_seed_results(scores))
    write_table(root,'paired_comparison',paired_comparison(scores,config['primary_lambda'],config['reference_lambda']))
    diagnostics={};years=[]
    for row in scores:
        directory=frozen_path(root,'runs/'+row['scenario_id'])
        diagnostics[row['scenario_id']]=json.loads((directory/'diagnostics.json').read_text())
        accounting=directory/'accounting'/row['baseline']
        intervals=pl.read_parquet(accounting/'intervals.parquet').to_dicts()
        decisions=pl.read_parquet(directory/'decisions.parquet').to_dicts()
        events=[event for event in pl.read_parquet(accounting/'ledger.parquet').to_dicts() if event['kind'] in ('execution','hold')]
        trades=pl.read_parquet(accounting/'trades.parquet').to_dicts()
        years+=yearly_summary(row,intervals,decisions,events,trades,protocol)
    write_table(root,'yearly_summary',years)
    write_json(root/'diagnostics.json',diagnostics)
    manifest=dict(artifact_type='indexpilot-stage-4',schema_version=1,protocol_id=protocol['protocol_id'],created_at=datetime.now(timezone.utc).isoformat(),git_revision=git_revision(),environment=environment(),input_sha256=protocol['input_sha256'],effective_input_file=protocol['input_file'],intended_coverage=protocol['intended_coverage'],scenarios=scores,summary_hashes={name:file_hash(root/name) for name in SUMMARY_FILES})
    write_json(root/'run_manifest.json',manifest)
    return manifest


def run_evaluation(protocol_dir,input_path=None,progress=None):
    root=Path(protocol_dir);protocol=validate_protocol(root,input_path)
    history=ledger_for(root)
    with run_lock(root):
        if (root/'run_manifest.json').exists(): return check_complete(root,protocol)
        completed=[]
        history.append('started',protocol['protocol_id'],input_sha256=protocol['input_sha256'],model_hashes=[row['sha256'] for row in protocol['models']])
        try:
            segment=build_test_segment(load_market_data(protocol['input_file']),evaluation_config(protocol),SimulationConfig(**protocol['simulation_config']))
            scores=[]
            for scenario in scenarios(protocol):
                directory=frozen_path(root,'runs/'+scenario['scenario_id'])
                if directory.exists(): score=check_run(directory,protocol['protocol_id'])
                else:
                    score=store_run(root,protocol,evaluate_scenario(root,protocol,segment,scenario))
                    history.append('scenario_completed',protocol['protocol_id'],scenario_id=scenario['scenario_id'],status=score['status'])
                scores.append(score);completed.append(scenario['scenario_id'])
                if progress: progress(scenario['scenario_id'])
            validate_protocol(root,input_path)
            manifest=summarize(root,protocol,scores)
            check_complete(root,protocol)
            history.append('completed',protocol['protocol_id'],scenarios=completed,summary_hashes=manifest['summary_hashes'])
            return manifest
        except Exception as error:
            history.append('failed',protocol['protocol_id'],completed_scenarios=completed,error=str(error))
            raise


def compare_replay(original,replay,protocol):
    original=Path(original);replay=Path(replay)
    for name in SUMMARY_FILES:
        if file_hash(original/name)!=file_hash(replay/name): raise ValueError('Replay summary differs: '+name)
    for scenario in scenarios(protocol):
        left=frozen_path(original,'runs/'+scenario['scenario_id'])
        right=frozen_path(replay,'runs/'+scenario['scenario_id'])
        for path in left.rglob('*'):
            if not path.is_file() or path.name in ('completion.json','run_manifest.json'): continue
            counterpart=right/path.relative_to(left)
            if path.suffix=='.parquet': equal=pl.read_parquet(path).equals(pl.read_parquet(counterpart))
            else: equal=path.read_bytes()==counterpart.read_bytes()
            if not equal: raise ValueError('Replay artifact differs: '+str(path.relative_to(original)))


def verify_evaluation(protocol_dir,input_path=None,progress=None):
    root=Path(protocol_dir);protocol=validate_protocol(root,input_path)
    with run_lock(root):
        check_complete(root,protocol)
        replay=Path(tempfile.mkdtemp(prefix='verification-',dir=root))
        try:
            segment=build_test_segment(load_market_data(protocol['input_file']),evaluation_config(protocol),SimulationConfig(**protocol['simulation_config']))
            scores=[]
            for scenario in scenarios(protocol):
                scores.append(store_run(replay,protocol,evaluate_scenario(root,protocol,segment,scenario)))
                if progress: progress(scenario['scenario_id'])
            summarize(replay,protocol,scores)
            compare_replay(root,replay,protocol)
            validate_protocol(root,input_path)
            write_json(replay/'verification.json',dict(protocol_id=protocol['protocol_id'],status='verified',scenario_count=len(scores)))
            ledger_for(root).append('verified',protocol['protocol_id'],replay_directory=str(replay),scenario_count=len(scores))
            return replay
        except Exception as error:
            ledger_for(root).append('verification_failed',protocol['protocol_id'],replay_directory=str(replay),error=str(error))
            raise
