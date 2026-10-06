# 05 — Q-learning trong dự án

## Mục lục

- [MDP và observation](#mdp-và-observation)
- [State bins và actions](#state-bins-và-actions)
- [Q table và chọn action](#q-table-và-chọn-action)
- [Bellman update](#bellman-update)
- [Training sau rollout](#training-sau-rollout)
- [Validation và checkpoint](#validation-và-checkpoint)

## MDP và observation

Q-learning học giá trị reward tương lai của từng action tại từng state. Nó không dự báo trực tiếp giá AAPL hoặc fit một mô hình supervised return prediction.

| Thành phần | Trong dự án |
|---|---|
| Agent | QLearningAgent chọn target exposure |
| Environment | Lịch sử AAPL và tài khoản holdings/cash |
| Observation | Lagged market features, cash, holdings, equity, exposure, drawdown |
| State | Sáu features được chuyển thành một integer bằng bins cố định |
| Action | Một trong năm signed exposure targets |
| Transition | Simulator execute action và tiến sang open tiếp theo |
| Reward | Gross return − lambda × risk − cost fraction |
| Terminal | Hết segment hoặc insolvent, có liquidation |

TradingEnvironment là adapter theo episode trên [simulator](04-simulator.md). Nó tạo trajectory gồm SimulationResult và finalized transitions; không có accounting engine thứ hai.

Market features chỉ dùng lịch sử trước decision session. Account được mark ở current open; next open không nằm trong observation. Date/index không thuộc learned state.

## State bins và actions

| Feature | Bin edges |
|---|---|
| Lagged adjusted-close return 1 phiên | −0,02; 0; 0,02 |
| Return 5 phiên | −0,05; 0; 0,05 |
| Return 20 phiên | −0,1; 0; 0,1 |
| Causal open-return volatility | 0,01; 0,02; 0,04 |
| Current marked exposure | −0,75; −0,25; 0,25; 0,75 |
| Portfolio drawdown | 0,1; 0,25 |

Có bins ở hai đầu ngoài ngưỡng: 4 × 4 × 4 × 4 × 5 × 3 = **3.840 states**. Code dùng searchsorted(side="right") rồi ravel_multi_index. Giá trị đúng ngưỡng nằm ở bin bên phải.

Ví dụ return_1 = +0,01 thuộc khoảng [0;0,02); return_1 = 0,02 thuộc bin từ 0,02 trở lên. Exposure là tỷ trọng mark thực tế trước action, không phải target cuối cùng từng được đặt.

| Action ID | Target |
|---:|---:|
| 0 | −1 |
| 1 | −0,5 |
| 2 | 0 |
| 3 | +0,5 |
| 4 | +1 |

Features/bins cố định trong [state.py](../src/indexpilot_us100/agents/state.py). Không fit thresholds/scaler bằng validation/test. Cùng một state có thể gom nhiều market/account situations; cách biểu diễn này xấp xỉ, không chứng minh quá trình giá là Markov.

## Q table và chọn action

Q có shape (3840,5), float64; visits cùng shape, int64. Ban đầu Q bằng 0.

Epsilon-greedy:

- Với xác suất epsilon: chọn ngẫu nhiên một action ID.
- Phần còn lại: chọn action có Q lớn nhất.
- Khi tie: ưu tiên flat, small long, small short, full long, full short.

Unvisited states có Q bằng 0 nên greedy fallback là flat. Trong evaluation epsilon = 0, Q/visits chỉ đọc. RNG vẫn được reset nhưng không exploration.

Ví dụ một hàng Q theo action IDs:

```text
Q[state] = [-0,03; -0,01; 0; 0,02; 0,01]
greedy action = ID 3 → target +0,5
```

## Bellman update

```text
Nếu nonterminal:
    target = reward + gamma * max(Q[next_state])
Nếu terminal:
    target = reward

Q[state, action] += alpha * (target - Q[state, action])
visits[state, action] += 1
```

Gamma chiết khấu reward theo intervals, không chiết khấu cash/equity.

Ví dụ alpha = 0,5, gamma = 0,9, Q hiện tại = 0, reward = 1, max Q[next] = 2:

```text
target = 1 + 0,9*2 = 2,8
Q mới = 0 + 0,5*(2,8-0) = 1,4
```

Nếu update tiếp theo là terminal với reward = 1:

```text
target = 1
Q mới = 1,4 + 0,5*(1-1,4) = 1,2
```

Terminal không bootstrap từ một next state giả.

## Training sau rollout

Dự án dùng **off-policy Q-learning cập nhật sau mỗi rollout**:

1. Reset account flat; reset policy RNG bằng seed + episode index.
2. Đặt epsilon cho episode; giữ Q đã học ở các episode trước.
3. Rollout trọn training segment với Q không cập nhật trong rollout.
4. Simulator finalize terminal fees và accounting.
5. Duyệt transitions theo thứ tự thời gian để update Q.
6. Lặp lại cùng training segment cho episode tiếp theo.

Cách này bảo đảm reward cuối đã bao gồm liquidation; một quyết định không execute được trong closing-fee insolvency không tạo financial interval/transition giả.

Settings trong [stage-3.toml](../configs/stage-3.toml):

| Setting | Giá trị |
|---|---:|
| Episodes/model | 100 |
| Alpha | 0,1 |
| Gamma | 0,99 |
| Epsilon start | 1 |
| Epsilon decay | 0,97 |
| Epsilon floor | 0,05 |
| Seed chính | 42 |
| Phí training | 10 bps |
| Lambda validation grid | 0; 0,5; 1; 2 |

Epsilon của episode e, đếm từ 0, là max(0,05; 1 × 0,97^e). Các episode là nhiều lượt học trên **cùng lịch sử**, không phải 100 independent market samples.

Exploratory training reward, greedy train và greedy validation được lưu riêng. Performance tốt trên lịch sử được lặp lại không chứng minh generalization.

## Validation và checkpoint

Training dùng dữ liệu đến hết 2020. Validation 2021–2022 reset account và evaluate greedy; không update Q/visits. Chọn lambda có Sharpe validation hữu hạn cao nhất; bỏ insolvent. Ties giữ thứ tự grid. Nếu tất cả undefined, fallback lambda 0 và ghi status rõ ràng.

Lambda 2 được chọn trên snapshot đã khóa. Validation có một trade và 99,8% flat decisions, nên phải đọc Sharpe cùng mức hoạt động. Test từ 2023 đánh giá lựa chọn này; không dùng test đổi bins, lambda hoặc seed.

Checkpoint NPZ chứa Q, visits và versioned feature/bin/action metadata. Load không dùng pickle và kiểm tra shape/dtype/finite/state compatibility. Learning settings cần lấy từ manifest/protocol; NPZ không chứa đủ config để tự suy ra cách training.

Artifacts learning local:

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

Các thư mục lambda khác có cùng cấu trúc. selection.json của source vẫn ghi test_evaluated=false vì learning run chỉ train/validate; final evaluation có protocol/manifest riêng.

**Đọc tiếp:** [README dự án](../README.md) dẫn tới frozen evaluation và kết quả thực tế.
