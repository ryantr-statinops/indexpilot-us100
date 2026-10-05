"""Frozen policy evaluation through the existing simulation engine."""
from dataclasses import dataclass,replace,field
from indexpilot_us100.agents.config import LearningConfig
from indexpilot_us100.agents.qlearning import QLearningAgent
from indexpilot_us100.environment.trading import TradingEnvironment
from indexpilot_us100.portfolio.config import SimulationConfig
from .protocol import frozen_path


@dataclass
class EvaluatedRun:
    scenario: dict
    result: object
    trajectory: object = None
    agent: object = None
    decisions: list = field(default_factory=list)


def learning_config(protocol):
    values=dict(protocol['learning_config']); values['lambdas']=tuple(values['lambdas'])
    return LearningConfig(**values)


def simulation_config(protocol,scenario):
    return replace(SimulationConfig(**protocol['simulation_config']),seed=scenario['seed'],cost_bps=scenario['cost_bps'],risk_lambda=scenario['risk_lambda'])


def evaluate_frozen_policy(root,protocol,segment,scenario):
    matches=[row for row in protocol['models'] if row['seed']==scenario['seed'] and row['risk_lambda']==scenario['risk_lambda']]
    if len(matches)!=1: raise ValueError('Required frozen model missing or duplicated')
    name=f"q_lambda_{scenario['risk_lambda']:g}_seed_{scenario['seed']}".replace('.','_')
    agent=QLearningAgent.load(frozen_path(root,matches[0]['model']),learning_config(protocol),name)
    agent.epsilon=0.; agent.q.setflags(write=False); agent.visits.setflags(write=False)
    recorded=RecordingPolicy(agent)
    trajectory=TradingEnvironment(segment,simulation_config(protocol,scenario)).rollout(recorded)
    if agent.q.flags.writeable or agent.visits.flags.writeable: raise ValueError('Evaluation unlocked learning arrays')
    return EvaluatedRun(scenario,trajectory.result,trajectory,agent,recorded.decisions[:len(trajectory.result.intervals)])


def baseline_scenarios(protocol,cost_bps):
    from indexpilot_us100.portfolio.baselines import baseline_policies
    config=protocol['evaluation_config']
    rows=[]
    for policy in baseline_policies():
        seeds=config['seeds'] if policy.name=='random_discrete' else [config['primary_seed']]
        for seed in seeds:
            rows.append(dict(kind='random' if policy.name=='random_discrete' else 'deterministic',policy=policy.name,seed=seed,risk_lambda=config['primary_lambda'],cost_bps=cost_bps))
    return rows


def evaluate_baseline(protocol,segment,scenario):
    from indexpilot_us100.portfolio.baselines import baseline_policies
    from indexpilot_us100.portfolio.simulator import run_episode
    matches=[policy for policy in baseline_policies() if policy.name==scenario['policy']]
    if len(matches)!=1: raise ValueError('Unknown baseline')
    recorded=RecordingPolicy(matches[0])
    result=run_episode(segment,recorded,simulation_config(protocol,scenario))
    return EvaluatedRun(scenario,result,decisions=recorded.decisions[:len(result.intervals)])


class RecordingPolicy:
    def __init__(self,policy):
        self.policy=policy; self.name=policy.name; self.decisions=[]

    def reset(self,seed): self.policy.reset(seed)

    def decide(self,observation):
        from indexpilot_us100.agents.state import encode_state
        from indexpilot_us100.portfolio.account import TargetExposure
        action=self.policy.decide(observation)
        self.decisions.append(dict(date=observation.date,state=encode_state(observation),target=action.value if isinstance(action,TargetExposure) else None,exposure_before=observation.exposure,holdings_before=observation.holdings,equity_before=observation.equity))
        return action
