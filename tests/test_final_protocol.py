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
