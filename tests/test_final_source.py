from dataclasses import replace
import pytest
from indexpilot_us100.evaluation.final.source import validate_source
from final_helpers import source_fixture


def test_source_provenance(tmp_path):
    data,root,config=source_fixture(tmp_path)
    source=validate_source(data,root,config)
    assert set(source.models)=={0.,2.}
    with pytest.raises(ValueError,match='Selection'):
        validate_source(data,root,replace(config,primary_lambda=1))
    with data.open('ab') as file: file.write(b'changed')
    with pytest.raises(ValueError,match='hash'): validate_source(data,root,config)
