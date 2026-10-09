# 05 — Q-learning in the Project

## Contents

- [MDP and observation](#mdp-and-observation)
- [State bins and actions](#state-bins-and-actions)
- [Q table and action selection](#q-table-and-action-selection)
- [Bellman update](#bellman-update)
- [Training after rollout](#training-after-rollout)
- [Validation and checkpoint](#validation-and-checkpoint)

## MDP and observation

Q-learning learns the future reward value of each action in each state. It does not directly predict AAPL prices or fit a supervised return-prediction model.

| Component | In this project |
|---|---|
| Agent | `QLearningAgent` selects a target exposure |
| Environment | AAPL history and an account with holdings/cash |
| Observation | Lagged market features, cash, holdings, equity, exposure, and drawdown |
| State | Six features converted to an integer with fixed bins |
| Action | One of five signed exposure targets |
| Transition | Simulator executes the action and advances to the next open |
| Reward | Gross return − lambda × risk − cost fraction |
| Terminal | Segment ends or the account becomes insolvent, with liquidation |

`TradingEnvironment` is an episode adapter around the [simulator](04-simulator.md). It creates a trajectory containing a `SimulationResult` and finalized transitions; it does not implement a second accounting engine.

Market features use only history before the decision session. The account is marked at the current open; the next open is not part of the observation. Date/index is not part of the learned state.

## State bins and actions

| Feature | Bin edges |
|---|---|
| One-session lagged adjusted-close return | −0.02; 0; 0.02 |
| Five-session return | −0.05; 0; 0.05 |
| 20-session return | −0.1; 0; 0.1 |
| Causal open-return volatility | 0.01; 0.02; 0.04 |
| Current marked exposure | −0.75; −0.25; 0.25; 0.75 |
| Portfolio drawdown | 0.1; 0.25 |

Each dimension has bins beyond both outer thresholds: 4 × 4 × 4 × 4 × 5 × 3 = **3,840 states**. The code uses `searchsorted(side="right")` and then `ravel_multi_index`. A value exactly on a threshold goes into the bin to its right.

For example, `return_1 = +0.01` is in [0, 0.02); `return_1 = 0.02` is in the bin starting at 0.02. Exposure is the actual marked fraction before the action, not the last target that was set.

| Action ID | Target |
|---:|---:|
| 0 | −1 |
| 1 | −0.5 |
| 2 | 0 |
| 3 | +0.5 |
| 4 | +1 |

Features/bins are fixed in [state.py](../src/indexpilot_us100/agents/state.py). Thresholds/scalers are not fit on validation/test data. A state may combine distinct market/account situations; this representation is an approximation and does not prove that the price process is Markov.

## Q table and action selection

Q has shape (3840, 5), dtype float64; the visit-count array has the same shape and dtype int64. Q starts at zero.

Epsilon-greedy selection:

- With probability epsilon, choose a random action ID.
- Otherwise, choose the action with the largest Q value.
- On a tie, prefer flat, small long, small short, full long, then full short.

Unvisited states have Q = 0, so the greedy fallback is flat. During evaluation epsilon is 0 and Q/visits are read-only. The RNG is still reset, but there is no exploration.

Example row of Q values by action ID:

```text
Q[state] = [-0.03; -0.01; 0; 0.02; 0.01]
greedy action = ID 3 → target +0.5
```

## Bellman update

```text
If nonterminal:
    target = reward + gamma * max(Q[next_state])
If terminal:
    target = reward

Q[state, action] += alpha * (target - Q[state, action])
visits[state, action] += 1
```

Gamma discounts reward across intervals; it does not discount cash/equity.

Example: alpha = 0.5, gamma = 0.9, current Q = 0, reward = 1, max Q[next] = 2:

```text
target = 1 + 0.9*2 = 2.8
new Q = 0 + 0.5*(2.8-0) = 1.4
```

If the next update is terminal with reward = 1:

```text
target = 1
new Q = 1.4 + 0.5*(1-1.4) = 1.2
```

A terminal transition does not bootstrap from a fictitious next state.

## Training after rollout

The project uses **off-policy Q-learning updates after each rollout**:

1. Reset the account to flat; reset the policy RNG with seed + episode index.
2. Set epsilon for the episode; retain Q learned in previous episodes.
3. Roll out the full training segment while Q remains unchanged during that rollout.
4. The simulator finalizes terminal fees and accounting.
5. Process transitions in chronological order to update Q.
6. Repeat the same training segment in the next episode.

This ensures the final reward includes liquidation; a decision that cannot execute because of closing-fee insolvency does not create a fictitious financial interval/transition.

Settings in [stage-3.toml](../configs/stage-3.toml):

| Setting | Value |
|---|---:|
| Episodes per model | 100 |
| Alpha | 0.1 |
| Gamma | 0.99 |
| Epsilon start | 1 |
| Epsilon decay | 0.97 |
| Epsilon floor | 0.05 |
| Primary seed | 42 |
| Training fees | 10 bps |
| Validation lambda grid | 0; 0.5; 1; 2 |

Epsilon for episode e, starting at 0, is `max(0.05; 1 × 0.97^e)`. Episodes are repeated learning passes over the **same history**, not 100 independent market samples.

Exploratory training reward, greedy training, and greedy validation are saved separately. Strong performance on repeated historical data does not prove generalization.

## Validation and checkpoint

Training uses data through 2020. Validation on 2021–2022 resets the account and evaluates greedily; it does not update Q/visits. The selected lambda has the highest finite validation Sharpe; insolvent runs are excluded. Ties retain the grid order. If all values are undefined, lambda 0 is the fallback and the status is recorded.

Lambda 2 was selected on the locked snapshot. Validation had one trade and 99.8% flat decisions, so its Sharpe must be read alongside activity. The test from 2023 evaluates this choice; it is not used to change bins, lambda, or seed.

The NPZ checkpoint contains Q, visits, and versioned feature/bin/action metadata. Loading does not use pickle and checks shape/dtype/finite values/state compatibility. Learning settings must come from the manifest/protocol; the NPZ does not contain enough configuration to infer the training setup.

Local learning artifacts:

```text
run_manifest.json
selection.json
validation_summary.csv/json
diagnostics.json
lambda_2/
    model.npz
    training.csv
    train_greedy/
    validation/
    train_greedy_transitions.parquet
    validation_transitions.parquet
```

Other lambda directories have the same structure. The source run's `selection.json` still records `test_evaluated=false` because a learning run only trains/validates; final evaluation has a separate protocol/manifest.

**Next:** the [project README](../README.md) links to frozen evaluation and the results.
