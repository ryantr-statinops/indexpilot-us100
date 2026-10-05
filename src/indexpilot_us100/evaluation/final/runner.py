"""Frozen policy evaluation through the existing simulation engine."""
from dataclasses import dataclass,replace
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
    trajectory=TradingEnvironment(segment,simulation_config(protocol,scenario)).rollout(agent)
    if agent.q.flags.writeable or agent.visits.flags.writeable: raise ValueError('Evaluation unlocked learning arrays')
    return EvaluatedRun(scenario,trajectory.result,trajectory,agent)
