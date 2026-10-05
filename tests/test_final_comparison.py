import pytest
from indexpilot_us100.evaluation.final.comparison import paired_comparison,PAIR_METRICS


def test_paired_results_use_same_seed_and_cost():
    rows=[dict(kind='rl',risk_lambda=lam,seed=seed,cost_bps=10.,status='completed',**{key:lam+seed for key in PAIR_METRICS}) for seed in (42,7) for lam in (0.,2.)]
    rows[0]['sharpe']=None
    result=paired_comparison(rows)
    assert len(result)==2 and result[0]['net_return_delta']==2
    assert result[1]['sharpe_delta'] is None
    with pytest.raises(ValueError,match='Missing'): paired_comparison(rows[:1])
