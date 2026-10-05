"""Calendar attribution of one continuous episode, including terminal fees."""
from datetime import date
from collections import defaultdict
import numpy as np


def yearly_summary(scenario,intervals,decisions,events,trades,protocol):
    if len(intervals)!=len(decisions) or len(events)!=len(intervals):
        raise ValueError('Yearly interval/decision alignment failed')
    groups=defaultdict(list)
    for interval,decision,event in zip(intervals,decisions,events):
        groups[interval['end_date'].year].append((interval,decision,event))
    start=date.fromisoformat(protocol['evaluation_config']['test_start'])
    end=date.fromisoformat(protocol['evaluation_config']['test_end'])
    output=[]
    for year,records in sorted(groups.items()):
        first,last=records[0][0]['date'],records[-1][0]['end_date']
        counts={str(action):0 for action in (-1.,-.5,0.,.5,1.)}
        counts['hold']=0
        for _,decision,_ in records:
            target='hold' if decision['target'] is None else str(decision['target'])
            counts[target]=counts.get(target,0)+1
        output.append(dict(scenario_id=scenario['scenario_id'],year=year,start_date=first.isoformat(),end_date=last.isoformat(),interval_count=len(records),net_return=float(np.prod([1+row['net_return'] for row,_,_ in records])-1),fees=sum(row['fees'] for row,_,_ in records),active_intervals=sum(event['holdings']!=0 for _,_,event in records),closed_trades=sum(row['exit_date'].year==year for row in trades),partial_year=(year==start.year and start>date(year,1,1)) or (year==end.year and end<date(year,12,31)) or last.month<12,**{'action_'+key+'_fraction':value/len(records) for key,value in counts.items()}))
    return output
