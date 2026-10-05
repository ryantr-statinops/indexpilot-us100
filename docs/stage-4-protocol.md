# Stage 4 — frozen evaluation contract

The primary result uses Stage 3 lambda2/seed42 at10bps. Reference is lambda0/seed42. Do not retrain these checkpoints on validation. Additional seeds [7,21,84,123] train lambda0/2 on the original training segment with unchanged settings. All models are frozen before evaluating test.

- Data: same hashed Stage3 snapshot, test from2023-01-01 through2026-10-02. Prior21 sessions provide warm-up only; reset flat/$100,000 at test start.
- Matrix:30 RL runs (5seeds ×2lambdas ×3costs),15 deterministic baselines (5 ×3costs),15 random baselines (5seeds ×3costs). Costs0/10/20bps;10bps primary. No best-seed/cost selection on test.
- Preparation records source/data/config/model/code/lock/environment hashes and protocol ID. Test requires intact frozen inputs. Q/visits are read-only, epsilon0, and accounting/metrics use Stage2 unchanged.
- Append-only experiment ledger records prepare/start/scenario/complete/failure/verify. Completed results are reused only after integrity checks. Verification recomputes separately; no silent overwrites. New protocols after completed tests require an explicit reason.
- Report every run/status/coverage. Finite-only seed summaries include undefined/infinite/insolvent counts. Seed variation describes training randomness on one history, not future-market confidence.
- Report flat/active/long/short/exposure, unseen states, sparse trades, reward components, drawdown events and continuous yearly performance. No year-end reset. Sensitivity freezes Q, not action sequences: changed fees can change account state.
- Models and detailed data/artifacts stay local. Reproduction requires the archived matching snapshot/checkpoints. New Yahoo downloads are not assumed byte-identical.
- Implement and test checkpoints01–20 using synthetic fixtures before opening AAPL test results. Publish real results and close the four-stage prototype only after audit/verification/clean-environment reproduction.
