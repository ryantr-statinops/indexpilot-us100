"""Freeze and verify data, checkpoints, code and runtime provenance."""
from dataclasses import asdict
from datetime import datetime,timezone
import hashlib
from importlib.metadata import version,PackageNotFoundError
import json
from pathlib import Path
import platform
import shutil
import tempfile
from indexpilot_us100.agents.state import ACTIONS,BIN_EDGES,FEATURE_NAMES,STATE_COUNT
from indexpilot_us100.portfolio.market import load_market_data,decision_indices
from ..export import file_hash,git_revision,write_json
from .config import EvaluationConfig
from .preparation import prepare_models
from .source import validate_source
from .windows import build_test_segment

CORE_PACKAGES=('indexpilot-us100','numpy','polars','pandas','statsmodels','yfinance')


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def environment():
    versions={}
    for name in (*CORE_PACKAGES,'pytest','finplot','PyQt6','pyqtgraph'):
        try: versions[name]=version(name)
        except PackageNotFoundError: versions[name]=None
    return dict(python=platform.python_version(),implementation=platform.python_implementation(),platform=platform.platform(),packages=versions)


def code_fingerprints():
    package=Path(__file__).resolve().parents[2]
    return {str(path.relative_to(package)):file_hash(path) for path in sorted(package.rglob('*.py'))}


def lock_hash():
    return file_hash(Path(__file__).resolve().parents[4]/'uv.lock')


def frozen_path(root,relative):
    path=(Path(root)/relative).resolve()
    if Path(root).resolve() not in path.parents:
        raise ValueError('Frozen artifact path escapes protocol directory')
    return path


def prepare_protocol(input_path,source_run,config,output_dir,progress=None):
    output=Path(output_dir).resolve(); data=Path(input_path).resolve()
    source_root=Path(source_run).resolve()
    if output.exists(): raise ValueError('Preparation output already exists; choose a new protocol directory')
    if output==data or output in data.parents or output==source_root or output in source_root.parents:
        raise ValueError('Preparation output cannot contain source data/artifacts')
    source=validate_source(data,source_root,config)
    market=load_market_data(data)
    segment=build_test_segment(market,config,source.simulation)
    first=decision_indices(segment,source.simulation.risk_window).start
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.prepare-',dir=output.parent) as temporary:
        root=Path(temporary)
        models=prepare_models(market,source,config,root,progress)
        shutil.copy2(source_root/'run_manifest.json',root/'preparation/source_manifest.json')
        shutil.copy2(source_root/'selection.json',root/'preparation/source_selection.json')
        protocol=dict(artifact_type='indexpilot-stage-4-protocol',schema_version=1,created_at=datetime.now(timezone.utc).isoformat(),input_file=str(data),input_sha256=file_hash(data),source_manifest_sha256=file_hash(root/'preparation/source_manifest.json'),source_selection_sha256=file_hash(root/'preparation/source_selection.json'),evaluation_config=asdict(config),simulation_config=asdict(source.simulation),learning_config=asdict(source.learning),state_definition=dict(features=FEATURE_NAMES,bin_edges=BIN_EDGES,state_count=STATE_COUNT,actions=ACTIONS),models=models,intended_coverage=dict(start_date=segment.dates[first].isoformat(),end_date=segment.dates[-1].isoformat(),interval_count=len(segment.dates)-1-first),environment=environment(),code_fingerprints=code_fingerprints(),lock_sha256=lock_hash(),git_revision=git_revision())
        protocol=json.loads(json.dumps(protocol,allow_nan=False))
        protocol['protocol_id']=digest(protocol)
        write_json(root/'protocol.json',protocol)
        shutil.move(str(root),str(output))
    return protocol


def validate_protocol(root,input_path=None):
    root=Path(root)
    protocol=json.loads((root/'protocol.json').read_text())
    identifier=protocol.get('protocol_id'); payload={key:value for key,value in protocol.items() if key!='protocol_id'}
    if protocol.get('artifact_type')!='indexpilot-stage-4-protocol' or identifier!=digest(payload):
        raise ValueError('Protocol hash/schema integrity failed')
    candidate=Path(input_path).resolve() if input_path is not None else Path(protocol['input_file'])
    if file_hash(candidate)!=protocol['input_sha256']:
        raise ValueError('Frozen input data hash changed')
    if protocol['code_fingerprints']!=code_fingerprints() or protocol['lock_sha256']!=lock_hash():
        raise ValueError('Frozen calculation code or dependency lock changed')
    current=environment(); expected=protocol['environment']
    if current['python']!=expected['python'] or current['implementation']!=expected['implementation'] or any(current['packages'][name]!=expected['packages'][name] for name in CORE_PACKAGES):
        raise ValueError('Numerical runtime differs from frozen environment')
    for filename,key in [('preparation/source_manifest.json','source_manifest_sha256'),('preparation/source_selection.json','source_selection_sha256')]:
        if file_hash(frozen_path(root,filename))!=protocol[key]: raise ValueError('Frozen source provenance changed')
    for model in protocol['models']:
        for filename,key in [('model','sha256'),('training_log','training_log_sha256')]:
            if file_hash(frozen_path(root,model[filename]))!=model[key]:
                raise ValueError('Frozen model/training log hash changed')
    return {**protocol,'input_file':str(candidate)}
