import json
import pytest
from indexpilot_us100.evaluation.final.history import ExperimentLedger,run_lock


def test_ledger_and_reason(tmp_path):
    ledger=ExperimentLedger(tmp_path/'events.jsonl')
    ledger.append('prepared','abc',data_sha256='123')
    ledger.append('completed','abc')
    assert [row['event'] for row in ledger.events()]==['prepared','completed']
    with pytest.raises(ValueError,match='reason'): ledger.require_new_reason(None)
    ledger.require_new_reason('Changed research protocol')
    text=ledger.path.read_text().replace('prepared','tampered')
    ledger.path.write_text(text)
    with pytest.raises(ValueError,match='integrity'): ledger.events()


def test_no_concurrent_run(tmp_path):
    with run_lock(tmp_path):
        with pytest.raises(ValueError,match='already'): 
            with run_lock(tmp_path): pass
