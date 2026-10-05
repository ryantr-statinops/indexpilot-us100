"""Predeclared paired lambda comparisons; no ranking or model selection."""
import math

PAIR_METRICS=('net_return','sharpe','max_drawdown','total_fees','trade_count','active_intervals')


def paired_comparison(rows,primary_lambda=2.,reference_lambda=0.):
    groups={}
    for row in rows:
        if row['kind']=='rl':
            key=(row['seed'],row['cost_bps'])
            group=groups.setdefault(key,{})
            if row['risk_lambda'] in group: raise ValueError('Duplicate paired model')
            group[row['risk_lambda']]=row
    output=[]
    for (seed,cost),group in sorted(groups.items()):
        if primary_lambda not in group or reference_lambda not in group:
            raise ValueError('Missing paired lambda result')
        primary,reference=group[primary_lambda],group[reference_lambda]
        row=dict(seed=seed,cost_bps=cost,primary_status=primary['status'],reference_status=reference['status'])
        for key in PAIR_METRICS:
            a,b=primary[key],reference[key]
            row[key+'_delta']=a-b if a is not None and b is not None and math.isfinite(a) and math.isfinite(b) else None
        output.append(row)
    return output
