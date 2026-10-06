# 07 — Kết quả và cách diễn giải

## Mục lục

- [Experiment nào được báo cáo](#experiment-nào-được-báo-cáo)
- [Validation và model được chọn](#validation-và-model-được-chọn)
- [Kết quả test chính](#kết-quả-test-chính)
- [Mức hoạt động của primary](#mức-hoạt-động-của-primary)
- [Seeds và cost sensitivity](#seeds-và-cost-sensitivity)
- [Primary theo năm](#primary-theo-năm)
- [Giới hạn và bài học](#giới-hạn-và-bài-học)
- [Bằng chứng kiểm chứng](#bằng-chứng-kiểm-chứng)

## Experiment nào được báo cáo

Kết quả dưới đây đọc từ artifacts đã lưu, không chạy lại policy. [Frozen protocol](06-evaluation.md) định nghĩa primary lambda 2/seed 42/10 bps và reference lambda 0; không chọn lại sau khi thấy test.

- Training: đến hết 2020; validation thực tế 2021-01-04 → 2022-12-30.
- Test: **2023-01-03 → 2026-10-02**, 940 open-to-open intervals; 2026 chưa đủ.
- Mỗi run reset $100.000, all policies dùng cùng engine.
- 10 models và 60 scenarios; tất cả completed, không insolvent trên snapshot này.
- Protocol ID: `5fbce9eb3c97815487c57b7eaca4502390562e37ed062609d72c87ba189ec18b`.
- Calculation revision: `b6c550d`; [snapshot SHA256 và convention](03-data.md#snapshot-của-experiment).

Các bảng ở đây chọn thông tin cần để đọc kết quả. Full scenario/seed/paired/yearly tables và generated report nằm trong outputs/stage-4/aapl-frozen local, không được commit vào docs.

## Validation và model được chọn

100 episodes mỗi lambda, seed 42, phí 10 bps:

| Lambda | Equity USD | Sharpe | MDD | CAGR | Trades |
| --- | --- | --- | --- | --- | --- |
| 0.0 | 88,470.96 | -0.162 | 32.56% | -5.98% | 174 |
| 0.5 | 103,386.52 | 0.297 | 8.23% | 1.69% | 34 |
| 1.0 | 103,687.96 | 0.595 | 2.05% | 1.84% | 4 |
| 2.0 | 103,584.38 | 0.698 | 0.05% | 1.79% | 1 |

Lambda 2 có Sharpe validation cao nhất, nhưng chỉ **một trade** và 99,80% flat decisions. Đó là trade 2022-02-24 → 2022-02-25, net P&L khoảng $3.584,38. PF vô hạn hoặc Calmar cao đi kèm một trade không chứng minh chất lượng dự báo.

Selection được giữ nguyên khi đánh giá test. Validation kết quả đẹp không bảo đảm test tiếp tục đẹp.

## Kết quả test chính

Seed 42, phí 10 bps, cùng intended/actual coverage:

| Policy | Equity USD | Return | Sharpe | MDD | CAGR | PF | Calmar |
| --- | --- | --- | --- | --- | --- | --- | --- |
| q_lambda_0 | 82,583.96 | -17.42% | -0.196 | 35.69% | -4.98% | 0.908 | -0.140 |
| q_lambda_2 | 99,239.61 | -0.76% | -0.479 | 0.90% | -0.20% | 0.111 | -0.225 |
| cash | 100,000.00 | 0.00% | N/A | 0.00% | 0.00% | N/A | N/A |
| buy_hold | 259,848.56 | 159.85% | 1.074 | 33.33% | 29.04% | ∞ | 0.871 |
| fixed_long_50 | 166,436.56 | 66.44% | 1.069 | 17.87% | 14.57% | ∞ | 0.816 |
| fixed_short_50 | 55,309.02 | -44.69% | -1.094 | 46.14% | -14.63% | 0.000 | -0.317 |
| sma20_long_flat | 180,613.50 | 80.61% | 0.962 | 27.12% | 17.10% | 2.080 | 0.631 |
| random_discrete | 141,276.23 | 41.28% | 0.550 | 29.09% | 9.66% | 1.130 | 0.332 |

Return/MDD/CAGR là tỷ lệ; Sharpe/PF/Calmar là ratios. PF ∞ của buy-and-hold và fixed long 50 có nghĩa một closed position episode có lời, không có nghĩa không có drawdown. Cash có Sharpe/PF/Calmar N/A vì không có variation/trades và CAGR/MDD đều 0.

| Policy | Fees USD | Orders | Trades | Active/940 | Flat actions |
| --- | --- | --- | --- | --- | --- |
| q_lambda_0 | 45,755.41 | 655 | 266 | 760 | 19.15% |
| q_lambda_2 | 199.43 | 4 | 2 | 2 | 99.79% |
| cash | 0.00 | 0 | 0 | 0 | 100.00% |
| buy_hold | 360.01 | 2 | 1 | 940 | 0.00% |
| fixed_long_50 | 496.73 | 941 | 1 | 940 | 0.00% |
| fixed_short_50 | 686.97 | 941 | 1 | 940 | 0.00% |
| sma20_long_flat | 11,287.85 | 80 | 40 | 575 | 38.83% |
| random_discrete | 96,136.87 | 851 | 450 | 740 | 21.28% |

Buy-and-hold mua đầu, giữ units, bán cuối; fixed exposure tái cân bằng mỗi phiên. Order count và trade count vì thế khác nhau rất lớn dù cùng một đợt vị thế long. Full-sample baseline từ 2015 đã được dùng kiểm tra simulator; các bảng trên chỉ là đoạn test của experiment đã chốt.

## Mức hoạt động của primary

Lambda 2 lỗ **0,76%**, equity cuối $99.239,61; thấp hơn cash và buy-and-hold. MDD chỉ 0,90% đi cùng **2/940 active intervals** và **938/940 flat actions**.

Hai trades đều target long 50%, mỗi trade giữ một interval:

| Mở → đóng | Gross P&L USD | Fees USD | Net P&L USD |
|---|---:|---:|---:|
| 2025-01-03 → 2025-01-06 | +195,09 | 100,15 | +94,94 |
| 2026-02-13 → 2026-02-17 | −756,04 | 99,29 | −855,33 |

Ví dụ đọc dòng thứ hai: gross loss và cả phí mở/đóng tạo net loss $855,33. Cộng hai net P&L cho khoảng −$760,39, khớp final equity trừ vốn đầu.

Unseen-state fraction primary là 2,55%; phần lớn flat decisions vẫn nằm trong states đã gặp. Volatility penalty mạnh khuyến khích tránh exposure. Với rất ít giao dịch, metrics không đủ bằng chứng về predictive skill; không diễn giải low drawdown thành chiến lược tốt hơn cash.

Lambda 0 hoạt động 760 intervals, đóng 266 trades, trả khoảng $45.755,41 phí và lỗ 17,42%. Khoảng cách với performance training cho thấy rủi ro fit nhiều lần trên một lịch sử và generalization kém.

## Seeds và cost sensitivity

### Tất cả RL seeds ở 10 bps

| Lambda | Seed | Return | Sharpe | MDD | Trades | Active | Flat actions |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0.0 | 42 | -17.42% | -0.196 | 35.69% | 266 | 760 | 19.15% |
| 2.0 | 42 | -0.76% | -0.479 | 0.90% | 2 | 2 | 99.79% |
| 0.0 | 7 | -13.24% | -0.083 | 47.07% | 218 | 793 | 15.64% |
| 2.0 | 7 | -2.06% | -0.618 | 2.34% | 2 | 3 | 99.68% |
| 0.0 | 21 | -29.65% | -0.350 | 45.63% | 241 | 781 | 16.91% |
| 2.0 | 21 | -1.03% | -0.618 | 1.17% | 2 | 3 | 99.68% |
| 0.0 | 84 | -27.97% | -0.397 | 43.96% | 249 | 701 | 25.43% |
| 2.0 | 84 | -1.52% | -0.479 | 1.81% | 2 | 2 | 99.79% |
| 0.0 | 123 | -29.94% | -0.385 | 52.06% | 268 | 786 | 16.38% |
| 2.0 | 123 | 0.78% | 0.155 | 1.71% | 3 | 4 | 99.57% |

Primary vẫn là seed 42; không thay bằng seed 123 vì thấy return dương. Các run lambda 2 đều sparse/mostly flat. Random seed 42 có lời trên test cũng không đủ để đánh giá chất lượng: mean năm random seeds ở 10 bps là −22,46%, sample std 38,92 điểm phần trăm.

### Tổng hợp net returns

| Policy | bps | Mean return | Median | Std (điểm %) | Min | Max |
| --- | --- | --- | --- | --- | --- | --- |
| random_discrete | 0 | 64.93% | 61.16% | 83.90 | -3.00% | 203.22% |
| random_discrete | 10 | -22.46% | -23.19% | 38.92 | -54.58% | 41.28% |
| random_discrete | 20 | -63.54% | -63.39% | 18.06 | -78.73% | -34.18% |
| q_lambda_0 | 0 | 26.89% | 22.81% | 31.93 | -11.42% | 72.43% |
| q_lambda_0 | 10 | -23.64% | -27.97% | 7.77 | -29.94% | -13.24% |
| q_lambda_0 | 20 | -46.72% | -50.23% | 10.21 | -57.72% | -34.52% |
| q_lambda_2 | 0 | -0.56% | -0.83% | 1.16 | -1.67% | 1.38% |
| q_lambda_2 | 10 | -0.92% | -1.03% | 1.07 | -2.06% | 0.78% |
| q_lambda_2 | 20 | -1.27% | -1.23% | 1.00 | -2.45% | 0.17% |

Mỗi dòng dùng đủ năm seeds và năm finite net returns; không có insolvent. Đây là sample std của kết quả training ngẫu nhiên trên **cùng lịch sử**, không phải confidence interval lợi nhuận tương lai. Các metric khác có thể undefined hoặc infinite; full seed_summary giữ status counts và chỉ aggregate finite values.

### Seed 42 ở ba mức phí

| Policy, seed 42 | 0 bps | 10 bps | 20 bps |
| --- | --- | --- | --- |
| q_lambda_0 | 72.43% | -17.42% | -34.52% |
| q_lambda_2 | -0.56% | -0.76% | -0.96% |
| cash | 0.00% | 0.00% | 0.00% |
| buy_hold | 160.37% | 159.85% | 159.33% |
| fixed_long_50 | 67.06% | 66.44% | 65.81% |
| fixed_short_50 | -44.18% | -44.69% | -45.20% |
| sma20_long_flat | 95.66% | 80.61% | 66.73% |
| random_discrete | 203.22% | 41.28% | -34.18% |

Phí làm equity/account state đổi; frozen Q không bảo đảm identical actions ở các cost scenarios. Vì vậy sensitivity là đánh giá cùng policy đã học dưới các execution assumptions, không chỉ lấy một equity curve rồi trừ thêm fees. Cost 0/20 không được dùng chọn mức phí thuận lợi; kết quả chính vẫn 10 bps.

## Primary theo năm

| Năm | Intervals | Net return | Fees USD | Active | Trades đóng | Coverage |
| --- | --- | --- | --- | --- | --- | --- |
| 2023 | 249 | 0.00% | 0.00 | 0 | 0 | Theo horizon đã khai báo |
| 2024 | 252 | 0.00% | 0.00 | 0 | 0 | Theo horizon đã khai báo |
| 2025 | 250 | 0.09% | 100.15 | 1 | 1 | Theo horizon đã khai báo |
| 2026 | 189 | -0.85% | 99.29 | 1 | 1 | Chưa đủ năm |

Một account liên tục, không reset vào 01/01. Intervals được gán theo **end_date**, nên interval từ open cuối tháng 12 đến open đầu tháng 1 thuộc năm mới. Returns năm compound về total return; trade P&L không được dùng thay calendar return.

Không có giao dịch trong 2023–2024 là một kết quả cần báo cáo. Return năm 2026 chỉ đến open 02/10, không so như một full calendar year.

## Giới hạn và bài học

- Một mã AAPL và một lịch sử không đại diện US100 hoặc mọi chế độ thị trường.
- Validation selection có bias lựa chọn; test chỉ kiểm tra protocol cố định này.
- 3.840 bins gom nhiều situations khác nhau; Q table không chứng minh giá có tính Markov.
- Risk proxy theo interval và lambda lớn có thể làm agent gần như luôn flat.
- Synthetic prices, phí tỷ lệ và short thiếu financing/borrow/margin khác brokerage thực tế.
- Seed variability không thay thế thêm independent market histories hoặc walk-forward.
- Historical adjustments có thể sửa; fresh Yahoo download không phải exact reproduction.

Bài học chính là phải đọc return/Sharpe cùng exposure, trade counts, fees và coverage. Prototype đã kiểm chứng accounting và evaluation; kết quả này chưa hỗ trợ kết luận RL vượt baselines hoặc có lợi nhuận live.

Hướng mở rộng gồm point-in-time US100 membership, multi-asset actions, walk-forward, richer costs và PPO. Đây là extensions, không phải phần đang được chạy trong experiment này.

## Bằng chứng kiểm chứng

- 175 tests đã pass ở repo chính và fresh checkout/venv; tests tổng hợp không cần Yahoo.
- Audit 60 terminal events: equity/cash/holdings reconciliation, terminal fee và coverage khớp.
- Sum net trade P&L khớp account P&L; sai số lớn nhất khoảng 6,26 × 10^-10 USD.
- Cash exact ở cả ba costs; buy-and-hold có đúng hai orders.
- Hai checkpoints seed 42 byte-identical với source; audit 30 RL scenarios giữ Q/visits nguyên và read-only.
- Independent verify 60 scenarios khớp decisions, transitions, Parquet tables, metrics và diagnostics.
- Clean environment với relocated exact snapshot cũng replay 60/60; generated report khớp byte-for-byte.
- Desktop FinPlot, offscreen seed views và PNG trong clean checkout đã render thành công.

Local evidence gồm audit.json, clean_environment_verification.json, verification directories và experiment ledger. Không cần chạy lại test để đọc hoặc vẽ các kết quả đã lưu.

**Đọc tiếp:** [README dự án](../README.md) dẫn tới hướng dẫn restore archive và tái lập.
