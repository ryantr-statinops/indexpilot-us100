"""Persist models, learning diagnostics and standard accounting artifacts."""
from dataclasses import asdict
from datetime import datetime, timezone
from importlib.metadata import version
import json
from pathlib import Path
import shutil
import tempfile
import numpy as np
import polars as pl
from indexpilot_us100.agents.state import ACTIONS, BIN_EDGES, FEATURE_NAMES, STATE_COUNT
from indexpilot_us100.metrics import compute_metrics
from .export import export_results, file_hash, git_revision, write_json


def trajectory_records(trajectory):
    return [{**asdict(transition), 'date': interval['date'], 'end_date': interval['end_date']} for transition,interval in zip(trajectory.transitions,trajectory.result.intervals)]


def trajectory_diagnostics(trajectory, agent):
    counts = np.bincount([t.action for t in trajectory.transitions],minlength=len(ACTIONS))
    count = len(trajectory.transitions)
    return dict(action_counts={str(action):int(number) for action,number in zip(ACTIONS,counts)}, action_fractions={str(action):float(number/count) for action,number in zip(ACTIONS,counts)}, unseen_state_fraction=sum(agent.visits[t.state].sum()==0 for t in trajectory.transitions)/count, flat_fraction=float(counts[2]/count), total_reward=sum(t.reward for t in trajectory.transitions), interval_count=count, order_count=len(trajectory.result.orders), status=trajectory.result.status)


def validate_learning_destination(input_path, output_dir, overwrite=False):
    output=Path(output_dir)
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        if not overwrite:
            raise ValueError(f'Output exists: {output}; choose another directory or --overwrite')
        marker=output/'run_manifest.json'
        if output.is_symlink() or not marker.is_file() or json.loads(marker.read_text()).get('artifact_type')!='indexpilot-stage-3':
            raise ValueError('Refusing to overwrite a directory without a Stage 3 manifest')
    source=Path(input_path).resolve()
    if output.resolve()==source or output.resolve() in source.parents:
        raise ValueError('Output cannot contain input data')
    return output


def export_learning(experiments, selection, simulation, learning, input_path, output_dir, overwrite=False):
    output=validate_learning_destination(input_path,output_dir,overwrite)
    source=Path(input_path).resolve()
    output.parent.mkdir(parents=True,exist_ok=True)
    rows=[]
    schema={'state':pl.Int64,'action':pl.Int64,'reward':pl.Float64,'next_state':pl.Int64,'terminated':pl.Boolean,'date':pl.Date,'end_date':pl.Date}
    with tempfile.TemporaryDirectory(prefix='.stage3-',dir=output.parent) as temporary:
        root=Path(temporary)
        diagnostics={}
        for experiment in experiments:
            name=f'lambda_{experiment.risk_lambda:g}'.replace('.','_')
            directory=root/name
            directory.mkdir()
            experiment.agent.save(directory/'model.npz')
            pl.DataFrame(experiment.training_log).write_csv(directory/'training.csv')
            export_results([experiment.greedy_train.result],source,directory/'train_greedy')
            export_results([*experiment.baselines,experiment.validation.result],source,directory/'validation')
            for phase,trajectory in [('train_greedy',experiment.greedy_train),('validation',experiment.validation)]:
                pl.DataFrame(trajectory_records(trajectory),schema=schema).write_parquet(directory/f'{phase}_transitions.parquet')
                diagnostics[f'{name}/{phase}']=trajectory_diagnostics(trajectory,experiment.agent)
            for report in [compute_metrics(result) for result in [*experiment.baselines,experiment.validation.result]]:
                rows.append({'risk_lambda':experiment.risk_lambda,**report.row()})
        pl.DataFrame(rows,infer_schema_length=None).write_csv(root/'validation_summary.csv')
        write_json(root/'validation_summary.json',rows)
        write_json(root/'selection.json',selection)
        write_json(root/'diagnostics.json',diagnostics)
        manifest=dict(artifact_type='indexpilot-stage-3',schema_version=1,created_at=datetime.now(timezone.utc).isoformat(),input_file=str(source),input_sha256=file_hash(source),simulation_config=asdict(simulation),learning_config=asdict(learning),state_definition=dict(features=FEATURE_NAMES,bin_edges=BIN_EDGES,state_count=STATE_COUNT,actions=ACTIONS),learning_schedule='frozen-table episode rollout then one chronological off-policy Q-learning pass',selection=selection,test_evaluated=False,git_revision=git_revision(),package_version=version('indexpilot-us100'),experiments=[dict(risk_lambda=experiment.risk_lambda,model_directory=f'lambda_{experiment.risk_lambda:g}'.replace('.','_'),train_start=experiment.greedy_train.result.equity[0]['date'].isoformat(),train_end=experiment.greedy_train.result.equity[-1]['date'].isoformat(),validation_start=experiment.validation.result.equity[0]['date'].isoformat(),validation_end=experiment.validation.result.equity[-1]['date'].isoformat()) for experiment in experiments])
        write_json(root/'run_manifest.json',manifest)
        if output.exists(): shutil.rmtree(output)
        shutil.move(str(root),str(output))
