"""Reuse primary checkpoints and train only predeclared additional seeds."""
from bisect import bisect_right
from dataclasses import replace
from datetime import date
from pathlib import Path
import shutil
import polars as pl
from indexpilot_us100.agents.training import train_agent
from indexpilot_us100.portfolio.market import MarketData
from ..export import file_hash


def prepare_models(market,source,config,output,progress=None):
    root=Path(output); (root/'frozen_models').mkdir(parents=True)
    (root/'preparation').mkdir()
    stop=bisect_right(market.dates,date.fromisoformat(source.learning.train_end))
    train=MarketData(market.dates[:stop],market.opens[:stop],market.closes[:stop],market.warnings)
    inventory=[]
    for seed in config.seeds:
        for risk_lambda in (config.reference_lambda,config.primary_lambda):
            name=f'seed_{seed}_lambda_{risk_lambda:g}'.replace('.','_')
            model=root/'frozen_models'/f'{name}.npz'
            log=root/'preparation'/f'{name}.csv'
            reused=seed==config.primary_seed
            if reused:
                shutil.copy2(source.models[risk_lambda],model)
                shutil.copy2(source.models[risk_lambda].parent/'training.csv',log)
            else:
                simulation=replace(source.simulation,seed=seed,risk_lambda=risk_lambda)
                agent,logs=train_agent(train,simulation,source.learning,progress)
                agent.save(model); pl.DataFrame(logs).write_csv(log)
            inventory.append(dict(seed=seed,risk_lambda=risk_lambda,model=str(model.relative_to(root)),sha256=file_hash(model),training_log=str(log.relative_to(root)),training_log_sha256=file_hash(log),reused_stage3=reused))
    return inventory
