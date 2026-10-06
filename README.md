# IndexPilot US100

Prototype reinforcement learning mô phỏng vị thế **AAPL daily**, dùng NumPy tabular Q-learning và simulator theo dõi holdings/cash. Dự án tập trung vào hiểu quyết định của agent, kế toán giao dịch và đánh giá kết quả có thể tái lập.

**Trạng thái hiện tại: hoàn thành cả bốn stage của prototype AAPL**, gồm dữ liệu, simulator/baselines, Q-learning và frozen evaluation. US100 là hướng mở rộng, chưa phải universe đang được mô phỏng.

## Dự án làm được gì?

- Lấy và chuẩn hóa dữ liệu giá, lưu snapshot và hashes để kiểm tra nguồn đầu vào.
- Mô phỏng long/short/flat, đơn vị lẻ, tái cân bằng, phí giao dịch và liquidation.
- Chạy sáu baselines và agent Q-learning trên cùng accounting engine.
- Đánh giá Sharpe, maximum drawdown, CAGR, Profit Factor và Calmar.
- Truy vết bằng ledger, orders, trades, transitions và diagnostics về mức hoạt động.
- Chạy CLI, xem equity/drawdown bằng FinPlot và tái lập experiment đã khóa.

## Kết quả chính

Test **2023-01-03 → 2026-10-02**, 940 khoảng open-to-open; vốn đầu $100.000, seed 42, phí 10 bps. Năm 2026 chưa đủ.

| Policy | Net return | Khoảng giữ vị thế / 940 |
|---|---:|---:|
| RL chính — lambda 2 | −0,76% | 2 |
| RL reference — lambda 0 | −17,42% | 760 |
| Buy-and-hold | +159,85% | 940 |

Model chính gần như luôn flat; drawdown nhỏ đi cùng exposure rất thấp. Kết quả này chưa chứng minh RL vượt baseline hoặc có khả năng dự báo tốt. Xem [kết quả và diễn giải](docs/07-results.md) để đọc thêm validation, seeds và cost sensitivity.

Bộ kiểm chứng đã pass **191 tests**. Experiment gồm **10 models, 60 scenarios**, với đối soát tài khoản/trade P&L, Q/visits bất biến khi đánh giá và independent replay trong checkout/môi trường sạch.

## Quickstart

Cần Git và uv. Từ repository root, cài môi trường cùng các dependencies cho biểu đồ:

```bash
uv sync --python 3.11.16 --frozen --extra dev --extra charts
```

**Để xem experiment đã chạy:** restore saved artifacts theo [hướng dẫn tái lập](docs/08-reproduction.md), rồi chạy:

```bash
uv run indexpilot-evaluate report --protocol-dir outputs/stage-4/aapl-frozen
uv run indexpilot-chart --run-dir outputs/stage-4/aapl-frozen
```

Data, checkpoints và detailed outputs không có trong Git clone. Archive local của experiment là `outputs/stage-4/aapl-reproduction.tar.gz`; cần chuyển bản archive riêng để restore. Report/chart đọc kết quả đã lưu, không train hoặc đánh giá lại policies.

Để recompute experiment AAPL đã công bố, dùng **checkout riêng tại revision b6c550d**, restore exact snapshot/models theo hướng dẫn tái lập rồi chạy lệnh dưới đây trong checkout đó. Code main đã được harden và có fingerprint khác; report/chart vẫn đọc artifacts cũ.

```bash
uv run indexpilot-evaluate verify --protocol-dir outputs/stage-4/aapl-frozen --data data/raw/aapl_daily_2015-01-01_to_2026-10-06_processed.parquet
```

Muốn bắt đầu bằng snapshot mới, xem [quickstart đầy đủ](docs/02-quickstart.md). Fresh Yahoo download có thể khác historical adjustments/hash; nó không mặc nhiên tái tạo experiment cũ. Tests tổng hợp có thể chạy bằng `uv run pytest -q` mà không cần Yahoo/network.

## Tech stack

| Vai trò | Công cụ |
|---|---|
| Ngôn ngữ / numerical runtime đã khóa | Python 3.11.16 |
| Số học, state encoding và Q-learning | NumPy |
| Dataframes và CSV/Parquet | Polars |
| Diagnostic thống kê | statsmodels |
| Nguồn giá / adapter | yfinance / pandas |
| Biểu đồ | FinPlot và Qt, optional extra charts |
| Packaging / kiểm chứng | uv, uv.lock / pytest |

Agent hiện tại không cần PyTorch hoặc Gymnasium. pandas phục vụ adapter yfinance/chart; dữ liệu và exports ở core dùng Polars.

## Tài liệu

- [Tổng quan](docs/01-overview.md): mục tiêu, phạm vi, stack và kiến trúc.
- [Quickstart](docs/02-quickstart.md): cài đặt, chạy và xem kết quả.
- [Kết quả](docs/07-results.md): metrics, activity, độ ổn định và bài học.
- [Tái lập](docs/08-reproduction.md): restore archive, hashes, verify và xử lý lỗi.

[Mục lục docs](docs/README.md) có lộ trình đọc cùng các chương về dữ liệu, simulator, Q-learning và evaluation.

## Giới hạn và hướng mở rộng

Prototype dùng một tài sản, synthetic adjusted prices và chi phí tỷ lệ đơn giản. Short chưa có borrow fee, financing hoặc margin call; đây là mô phỏng học tập, chưa phải hệ thống live trading.

US100 dự kiến là 100 công ty niêm yết tại Mỹ lớn nhất theo market capitalization tại từng formation date, không đồng nghĩa Nasdaq-100 hoặc S&P 100. Point-in-time membership, multi-asset allocation, walk-forward, richer costs và PPO là các hướng mở rộng sau prototype hiện tại.
