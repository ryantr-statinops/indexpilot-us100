from indexpilot_us100.evaluation.final.aggregation import aggregate_seed_results,METRICS


def test_seed_statistics_keep_statuses_and_skip_deterministic():
    rows=[]
    for seed,status,value in [(42,'finite',1.),(7,'positive_infinity',None),(21,'undefined',None),(84,'not_applicable',None),(123,'finite',3.)]:
        rows.append(dict(kind='rl',policy='q',risk_lambda=2.,cost_bps=10.,seed=seed,status='insolvent' if seed==84 else 'completed',**{key:value for key in METRICS},**{key+'_status':status for key in METRICS}))
    rows.append({**rows[0],'kind':'deterministic'})
    result=aggregate_seed_results(rows)
    assert len(result)==len(METRICS)
    first=result[0]
    assert first['mean']==2 and first['finite_count']==2
    assert first['undefined_count']==first['infinite_count']==first['insolvent_count']==1
    assert first['sample_std']>1
    assert aggregate_seed_results([rows[0]])[0]['sample_std'] is None
