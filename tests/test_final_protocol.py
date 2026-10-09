from dataclasses import replace
import json
import pytest
from indexpilot_us100.evaluation.final.protocol import prepare_protocol,validate_protocol
from final_helpers import source_fixture


def test_freeze_and_tampering(tmp_path):
    data,source,config=source_fixture(tmp_path)
    config=replace(config,seeds=(42,7))
    root=tmp_path/'protocol'
    protocol=prepare_protocol(data,source,config,root)
    assert len(protocol['models'])==4
    assert validate_protocol(root)==protocol
    model=root/protocol['models'][0]['model']
    with model.open('ab') as file:file.write(b'changed')
    with pytest.raises(ValueError,match='model'): validate_protocol(root)


@pytest.mark.parametrize('when',['load','models'])
def test_changed_dataset_aborts_preparation(tmp_path,monkeypatch,when):
    data,source,config=source_fixture(tmp_path)
    from indexpilot_us100.evaluation.final import protocol as module
    function='load_market_data' if when=='load' else 'prepare_models'
    original=getattr(module,function)
    def changed(*args,**kwargs):
        result=original(*args,**kwargs)
        with data.open('ab') as file: file.write(b'changed')
        return result
    monkeypatch.setattr(module,function,changed)
    output=tmp_path/'frozen'
    with pytest.raises(ValueError,match='Data changed'):
        prepare_protocol(data,source,replace(config,seeds=(42,)),output)
    assert not output.exists()
    assert not list(tmp_path.glob('.prepare-*'))


@pytest.mark.parametrize('name',['run_manifest.json','selection.json','lambda_2/model.npz','lambda_2/training.csv'])
def test_changed_source_aborts_publication(tmp_path,monkeypatch,name):
    data,source,config=source_fixture(tmp_path)
    from indexpilot_us100.evaluation.final import protocol as module
    original=module.prepare_models
    def changed(*args,**kwargs):
        result=original(*args,**kwargs)
        with (source/name).open('ab') as file: file.write(b'changed')
        return result
    monkeypatch.setattr(module,'prepare_models',changed)
    output=tmp_path/'frozen'
    with pytest.raises(ValueError,match='Source artifact changed'):
        prepare_protocol(data,source,replace(config,seeds=(42,)),output)
    assert not output.exists()
    assert not list(tmp_path.glob('.prepare-*'))


def test_protocol_records_instrument_label(tmp_path):
    from dataclasses import replace
    data, source, config = source_fixture(tmp_path)
    root = tmp_path / "labeled"
    protocol = prepare_protocol(data, source, replace(config, instrument_label="QQQ / Nasdaq-100 ETF"), root)
    assert protocol["evaluation_config"]["instrument_label"] == "QQQ / Nasdaq-100 ETF"
    assert validate_protocol(root)["evaluation_config"]["instrument_label"] == "QQQ / Nasdaq-100 ETF"
