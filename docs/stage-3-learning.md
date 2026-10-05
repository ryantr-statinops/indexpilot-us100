# Stage 3 — học Q-learning trên simulator

## Chạy training và xem kết quả

```bash
uv sync --extra dev
uv run pytest -q
uv run indexpilot-train \
  --data data/raw/aapl_daily_2015-01-01_to_2026-10-06_processed.parquet \
  --config configs/stage-3.toml \
  --output-dir outputs/stage-3/aapl-default
```

Output đã có thì chọn thư mục mới hoặc `--overwrite`; chỉ ghi đè thư mục có manifest Stage3. `--quiet` bỏ progress từng10 episode. Data/models/outputs được giữ local ngoài Git. Chưa cần PyTorch hoặc Gymnasium; agent dùng Python/NumPy.

Xem policy được chọn với sáu baseline:

```bash
uv sync --extra dev --extra charts
uv run indexpilot-chart --run-dir outputs/stage-3/aapl-default
```

Chart tự đọc selection và mở validation của model đó. Muốn xem lambda khác: truyền `--run-dir outputs/stage-3/aapl-default/lambda_0/validation`. Viewer vẫn hỗ trợ outputs Stage2.

## Vòng học đang làm gì?

MDP contract: [state, actions, timing, reward và boundaries](stage-3-mdp.md).

1. Reset tài khoản flat, reset RNG theo `seed + episode_index`; giữ Q table đã học.
2. Đặt epsilon của episode: `max(0.05, 1*0.97**episode_index)`.
3. Với xác suất epsilon, chọn một trong5 actions; còn lại chọn action có Q lớn nhất.
4. Chạy simulator Stage2 trọn đoạn training, với Q table giữ nguyên trong rollout.
5. Nhận các transitions đã hoàn tất và đã đối soát phí cuối.
6. Duyệt transitions theo thứ tự thời gian và cập nhật Q-learning.
7. Sang episode mới; sau100 episode chuyển epsilon về0 để đánh giá greedy.

Đây là **off-policy Q-learning cập nhật sau mỗi rollout**, không phải cập nhật ngay trong từng bước giao dịch. Cách này dùng nguyên engine Stage2 và xử lý chính xác trường hợp rare closing-fee insolvency sửa reward cuối. Một action cuối không thực hiện được không tạo thêm financial interval hoặc transition giả.

```text
nonterminal target = reward + gamma * max(Q[next_state])
terminal target = reward
Q[state, action] += alpha * (target - Q[state, action])
```

Mặc định alpha0,1; gamma0,99. Gamma chiết khấu reward ở các intervals sau trong episode hữu hạn; không dùng nó để chiết khấu equity. Toy test kiểm tra target `1+0.9*2=2.8`, với alpha0,5 từ Q0 →1,4. Terminal update tiếp theo với reward1 →1,2, không bootstrap. Một terminal bandit có reward biết trước cũng học đúng action tốt nhất.

## State và actions

| Feature | Bin edges |
|---|---|
| Lagged return1 | −0,02;0;0,02 |
| Lagged return5 | −0,05;0;0,05 |
| Lagged return20 | −0,1;0;0,1 |
| Causal volatility | 0,01;0,02;0,04 |
| Current marked exposure | −0,75;−0,25;0,25;0,75 |
| Portfolio drawdown | 0,1;0,25 |

`searchsorted(side='right')` giữ cả bins dưới/trên ngưỡng:4×4×4×4×5×3 =3.840 states. Q có shape `(3840,5)`, float64; visits cùng shape, int64. Không fit thresholds hoặc scaler trên validation.

Actions theo ID0→4: `[-1,-0.5,0,0.5,1]`. Target là exposure sau phí, dùng holdings/cash của Stage2. Ties ưu tiên flat, rồi small long, small short, full long, full short. Unvisited states có Q0 nên greedy chọn flat.

Portfolio exposure hiện tại được đưa vào state vì tỷ trọng trôi sẽ ảnh hưởng lượng mua/bán và phí. Bins gom nhiều trạng thái khác nhau; market history cũng chỉ được tóm tắt. Đây là biểu diễn trạng thái xấp xỉ, không chứng minh quá trình giá là Markov. Dates/index không thuộc learned state.

Raw Observation giữ features và account variables của Stage2. Market features chỉ dùng lịch sử trước decision session; tài khoản mark ở current quote; không có next open. State vector hữu hạn; volatility>=0 và live drawdown trong[0,1); exposure được phép trôi ngoài[-1,1]. Nonfinite states bị từ chối.

Environment là adapter theo episode: `reset(seed)` và `rollout(policy)`. End of selected segment hoặc insolvency là terminal của bài toán hữu hạn, có liquidation. Không có artificial time limit/truncation; chưa thêm Gymnasium step API.

## Training, validation và lựa chọn lambda

Config prototype đã lưu trước khi chạy:

- Train: lịch sử đầu vào đến2020-12-31; warm-up bị loại khỏi evaluation.
- Validation:2021-01-01 đến2022-12-31. Chỉ dùng các dòng trước đó làm warm-up; tài khoản bắt đầu lại flat.
- RL test: từ2023-01-01, chưa chạy policy hoặc lựa chọn tham số trên đoạn này.
- Lambda `[0,0.5,1,2]`;100 episode/model, seed42; giữ alpha, gamma, bins, phí và epsilon schedule giống nhau.
- Greedy validation không update Q/visits. Baselines dùng cùng dates và execution engine, reset account giống policy RL.
- Chọn lambda có Sharpe validation hữu hạn cao nhất; insolvent không được chọn. Ties giữ thứ tự grid. Tất cả undefined thì giữ reference lambda0 và ghi rõ fallback, không bịa winner.

Reward vẫn là `gross_return - lambda*risk - cost`. Risk penalty không trừ vào equity. Reward training là **tổng reward theo interval**, không phải cumulative return hoặc CAGR. Exploratory training metrics, greedy train và greedy validation được ghi riêng.

Selection dùng validation nên kết quả validation chưa phải kết luận cuối về generalization. Stage4 tiếp tục với model/protocol đã freeze và đoạn RL test chưa đánh giá. Không tự đổi bins/lambda sau khi xem test.

## Đọc artifacts

```text
run_manifest.json             # config, boundaries, bins/actions, hash data, Git version
selection.json                # lambda được chọn, tiêu chí, trạng thái, test_evaluated=false
validation_summary.csv/json   # metrics RL + baselines theo lambda
 diagnostics.json             # action frequencies, flat rate, unseen-state rate
lambda_0/                     # tương tự lambda_0_5, lambda_1, lambda_2
  model.npz                   # Q, state-action visits, versioned bin/action metadata
  training.csv                # reward, epsilon, TD error, fees, visits, actions/episode
  train_greedy_transitions.parquet
  validation_transitions.parquet
  train_greedy/                # Stage2 accounting exports cho greedy train
  validation/                 # Stage2 accounting exports cho RL + sáu baselines
```

Model loading không dùng pickle và kiểm tra shape, dtype, finite values, bins/actions tương thích. RNG cho evaluation được reset từ config; evaluation epsilon0. Nếu muốn tiếp tục training, cần dùng learning config đã lưu trong manifest, không mặc nhiên coi default config là config cũ.

```python
from indexpilot_us100.agents.qlearning import QLearningAgent
agent = QLearningAgent.load('outputs/stage-3/aapl-default/lambda_2/model.npz')
print(agent.q.shape, agent.visits.sum())
```

## Kiểm chứng

129 tests pass, gồm toàn bộ Stage2 và:

- Bellman update tính tay, terminal không bootstrap, toy bandit.
- Seed/exploration/tie behavior và model roundtrip.
- Exact parity của RL adapter với event ledger Stage2, kể cả terminal fee.
- Split warm-up và coverage; changing validation/test prices không đổi Q đã train.
- Greedy evaluation không thay đổi visits; cùng seed/config cho cùng tables/logs/results.
- Undefined validation, output guards, installed CLI, selected-model chart adapter.

Full AAPL chạy hai lần: Q arrays, visits, training CSV và validation summary giống nhau; restore model cho cùng equity curve; trade P&L và phí đối soát ở mọi phase. FinPlot đã render policy được chọn và sáu baseline.

## Kết quả AAPL

Snapshot SHA256: `042605225d9f9dc91ac983ceb13079f09077a569bd485dd06774263f994db3cc`. Run đầu dùng code commit `8a86c4d`.

Coverage thực tế: train **2015-02-03 → 2020-12-31**,1.489 intervals; validation **2021-01-04 → 2022-12-30**,502 intervals. Vốn mỗi phase $100.000, phí10bps.

| Lambda | Greedy train equity | Validation equity | Sharpe val | MDD val | CAGR val | Trades val | Flat actions val |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 | $8,814,654.77 | $88,470.96 | -0.162 | 32.56% | -5.98% | 174 | 20.92% |
| 0.5 | $293,280.22 | $103,386.52 | 0.297 | 8.23% | 1.69% | 34 | 92.23% |
| 1 | $121,442.96 | $103,687.96 | 0.595 | 2.05% | 1.84% | 4 | 99.20% |
| 2 | $101,486.83 | $103,584.38 | 0.698 | 0.05% | 1.79% | 1 | 99.80% |

### Baseline validation

| Baseline | Equity cuối | Sharpe | MDD | CAGR |
|---|---:|---:|---:|---:|
| cash | $100,000.00 | N/A | 0.00% | 0.00% |
| buy_hold | $97,132.91 | 0.108 | 29.51% | -1.45% |
| fixed_long_50 | $100,766.76 | 0.102 | 14.85% | 0.39% |
| fixed_short_50 | $93,714.14 | -0.133 | 21.65% | -3.22% |
| sma20_long_flat | $110,003.96 | 0.339 | 17.97% | 4.92% |
| random_discrete | $83,082.32 | -0.345 | 34.69% | -8.91% |

### Những gì cần hiểu từ kết quả

- Lambda0 ghi nhận greedy train equity rất lớn trên đoạn được lặp100 lần, nhưng validation lỗ. Kết quả fit training không chứng minh khả năng generalize.
- Khi lambda tăng, daily volatility penalty khuyến khích flat. Lambda2 flat501/502 decisions, chỉ target+0,5 một lần. Trade duy nhất:2022-02-24→2022-02-25, net P&L $3.584,38.
- Sharpe validation chọn lambda2, nhưng kết quả dựa vào **một trade**; PF vô hạn và Calmar cao đi cùng rất ít exposure và drawdown nhỏ. Đây là dấu hiệu cần xem inactivity/độ tin cậy, không kết luận RL tốt hơn thị trường.
- Lambda0 giao dịch174 trades, phí khoảng$29.200; lambda0,5 có34 trades; lambda1 có4. Reward thay đổi cả mức độ hoạt động và chi phí.
- Khoảng3,39% validation states chưa được train ghé qua; greedy fallback ở đó là flat. Tỷ lệ flat cao của lambda2 không chỉ do unseen states.
- Mỗi lambda vẫn có cùng dates, phí và accounting; financial metrics của baseline không đổi khi chỉ thay reward penalty.

Không thay grid sau kết quả này. Stage4 nên đánh giá model đã chọn trên đoạn reserved, xem nhiều seeds và báo cả exposure/trade counts bên cạnh Sharpe. Tiêu chí hoàn thành Stage3 là hiểu và kiểm chứng vòng học; không bắt buộc vượt baseline.
