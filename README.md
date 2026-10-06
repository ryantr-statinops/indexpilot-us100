# IndexPilot US100

Dự án học reinforcement learning bằng một mô phỏng vị thế cổ phiếu có thể truy vết: **AAPL daily**, holdings/cash, chi phí giao dịch, baselines và NumPy tabular Q-learning.

Prototype đã hoàn thành, gồm pipeline dữ liệu, accounting engine, training/validation, frozen test, diagnostics và tái lập. Hướng US100 là universe 100 công ty niêm yết tại Mỹ lớn nhất theo market capitalization tại từng formation date; prototype chưa triển khai universe đó và không đồng nghĩa Nasdaq-100/S&P 100.

## Đọc tài liệu

Bắt đầu ở **[mục lục docs](docs/README.md)** với hai lộ trình: hiểu cơ chế hoặc chạy experiment.

| Bạn muốn | Đọc |
|---|---|
| Hiểu mục tiêu, stack và kiến trúc | [Tổng quan](docs/01-overview.md) |
| Cài đặt và chạy | [Quickstart](docs/02-quickstart.md) |
| Hiểu giá/returns/timing | [Dữ liệu](docs/03-data.md) |
| Hiểu tiền, vị thế, phí và metrics | [Simulator](docs/04-simulator.md) |
| Hiểu agent học thế nào | [Q-learning](docs/05-q-learning.md) |
| Hiểu protocol và diagnostics | [Evaluation](docs/06-evaluation.md) |
| Đọc kết quả và giới hạn | [Kết quả](docs/07-results.md) |
| Restore archive và verify | [Tái lập](docs/08-reproduction.md) |

## Setup

Từ repository root, với uv đã cài:

```bash
uv sync --python 3.11.16 --frozen --extra dev
```

Thêm optional chart dependencies:

```bash
uv sync --python 3.11.16 --frozen --extra dev --extra charts
```

Core dùng Python, NumPy, Polars và statsmodels; pandas phục vụ adapter yfinance/chart. Agent không cần PyTorch hoặc Gymnasium. Dependencies được khóa trong uv.lock.

## Kết quả đã kiểm chứng

Test thực tế **2023-01-03 → 2026-10-02**, 940 intervals; năm 2026 chưa đủ:

| Policy chính, seed 42 / 10 bps | Net return | Active intervals |
|---|---:|---:|
| RL lambda 2 | −0,76% | 2/940 |
| RL reference lambda 0 | −17,42% | 760/940 |
| Buy-and-hold | +159,85% | 940/940 |

Model chính gần như flat; đọc activity/trade counts cùng Sharpe/drawdown. Kết quả này chưa chứng minh RL vượt baseline hoặc có khả năng dự báo tốt.

Đã kiểm chứng **175 tests**, inventory 10 models, 60 scenarios, account/trade reconciliation, Q/visits immutable và independent replay trong fresh checkout/venv. [Các bảng và diễn giải](docs/07-results.md) trình bày validation, seeds/cost sensitivity và giới hạn.

## Xem experiment đã archive

**Prerequisites:** data/checkpoints/detailed outputs không có trong Git. Restore exact snapshot và saved artifacts theo [hướng dẫn tái lập](docs/08-reproduction.md) trước khi chạy:

```bash
uv run indexpilot-evaluate report --protocol-dir outputs/stage-4/aapl-frozen
uv run indexpilot-chart --run-dir outputs/stage-4/aapl-frozen
uv run indexpilot-evaluate verify --protocol-dir outputs/stage-4/aapl-frozen --data data/raw/aapl_daily_2015-01-01_to_2026-10-06_processed.parquet
```

Report/chart đọc saved artifacts; verify thực sự tính lại để đối chiếu. Archive local hiện có: outputs/stage-4/aapl-reproduction.tar.gz, với manifest SHA256 kèm theo.

Muốn học bằng một snapshot mới, xem [quickstart](docs/02-quickstart.md#học-với-snapshot-mới). Fresh Yahoo download có thể đổi historical adjustments/hash và không được coi là cùng frozen experiment.

## Kiểm chứng và mở rộng

```bash
uv run pytest -q
```

Tests tổng hợp không cần Yahoo/network. Baselines và RL dùng cùng execution/accounting engine. Default actions là −1/−0,5/0/+0,5/+1; reward = gross return − lambda × risk − cost fraction. Risk penalty ảnh hưởng reward, không trừ equity.

Các extensions gồm historical US100 membership, multi-asset allocation, walk-forward, richer costs và PPO. Phạm vi hiện tại vẫn là prototype AAPL; [tổng quan](docs/01-overview.md#phạm-vi-mô-phỏng) ghi rõ các giả định.
