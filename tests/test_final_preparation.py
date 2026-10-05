from dataclasses import replace
from indexpilot_us100.evaluation.final.preparation import prepare_models
from indexpilot_us100.evaluation.final.source import validate_source
from indexpilot_us100.portfolio.market import load_market_data
from indexpilot_us100.evaluation.export import file_hash
from final_helpers import source_fixture


def test_primary_copied_additional_seed_training_only(tmp_path,monkeypatch):
    data,root,config=source_fixture(tmp_path)
    source=validate_source(data,root,config)
    config=replace(config,seeds=(42,7))
    from indexpilot_us100.evaluation.final import preparation
    original=preparation.train_agent
    observed=[]
    def guarded(market,simulation,learning,progress):
        assert market.dates[-1].isoformat()<=learning.train_end
        observed.append(simulation.seed)
        return original(market,simulation,learning,progress)
    monkeypatch.setattr(preparation,'train_agent',guarded)
    inventory=prepare_models(load_market_data(data),source,config,tmp_path/'prepared')
    assert len(inventory)==4 and observed==[7,7]
    for row in inventory[:2]:
        assert row['reused_stage3']
        assert row['sha256']==file_hash(source.models[row['risk_lambda']])
