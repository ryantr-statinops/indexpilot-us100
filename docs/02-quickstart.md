# 02 — Quickstart

## Mục lục

- [Cài môi trường](#cài-môi-trường)
- [Đọc kết quả đã có](#đọc-kết-quả-đã-có)
- [Xem và kiểm tra experiment đã khóa](#xem-và-kiểm-tra-experiment-đã-khóa)
- [Học với snapshot mới](#học-với-snapshot-mới)
- [Tra cứu lệnh](#tra-cứu-lệnh)

## Cài môi trường

Cần Git và uv. Mọi lệnh dưới đây chạy từ root repository:

```bash
git clone https://github.com/ryantr-statinops/indexpilot-us100.git
cd indexpilot-us100
uv sync --python 3.11.16 --frozen --extra dev
```

Để dùng FinPlot:

```bash
uv sync --python 3.11.16 --frozen --extra dev --extra charts
```

Python 3.11.16 là numerical runtime của experiment đã khóa. Code project khai báo Python ≥3.11; replay exact kiểm tra runtime chặt hơn.

Git clone không có data/checkpoints/results local. Nếu chỉ muốn hiểu dự án, đọc [kết quả](07-results.md) ngay; nếu muốn chạy, chọn workflow phù hợp bên dưới.

## Đọc kết quả đã có

Primary lambda 2/seed 42/10 bps trả −0,76%, chỉ active 2/940 intervals. Reference lambda 0 trả −17,42%; buy-and-hold +159,85% trên test 2023-01-03 → 2026-10-02. Năm 2026 chưa đủ.

[Kết quả và diễn giải](07-results.md) có metrics, seeds/costs và inactivity. Generated full report và accounting tables nằm local trong outputs/stage-4/aapl-frozen.

## Xem và kiểm tra experiment đã khóa

**Prerequisites:** restore archived snapshot, protocol/frozen_models/preparation, saved runs/summaries/manifest và ledger theo [hướng dẫn tái lập](08-reproduction.md#restore-archive-trong-checkout-sạch).

Sau khi restore:

```bash
uv run indexpilot-evaluate report --protocol-dir outputs/stage-4/aapl-frozen
uv run indexpilot-chart --run-dir outputs/stage-4/aapl-frozen
```

Report được ghi vào outputs/stage-4/aapl-frozen/report.md; chart mở equity/drawdown của tám policies chính. Hai lệnh này đọc kết quả đã lưu.

Kiểm tra cached run hoặc thực sự recompute:

```bash
uv run indexpilot-evaluate run \
  --protocol-dir outputs/stage-4/aapl-frozen \
  --data data/raw/aapl_daily_2015-01-01_to_2026-10-06_processed.parquet

uv run indexpilot-evaluate verify \
  --protocol-dir outputs/stage-4/aapl-frozen \
  --data data/raw/aapl_daily_2015-01-01_to_2026-10-06_processed.parquet
```

Với completed run, run kiểm tra hashes rồi reuse; verify tính lại riêng để so kết quả. Không chạy prepare vào directory đã restore. Thêm --data giúp máy mới dùng relocated snapshot có đúng hash.

Ví dụ đọc bảng chính:

```python
import polars as pl

summary = pl.read_csv("outputs/stage-4/aapl-frozen/primary_summary.csv")
print(summary.select("policy", "net_return", "sharpe", "trade_count", "active_intervals"))
```

Null metric phải đọc cùng metric_status; report hiển thị N/A hoặc ∞.

## Học với snapshot mới

Workflow này cần mạng ở bước fetch và tạo **experiment khác**; không thay input của protocol cũ:

```bash
uv run indexpilot-fetch --ticker AAPL --start 2015-01-01 --end 2026-10-06 --output-dir data/demo
uv run indexpilot-inspect data/demo/aapl_daily_2015-01-01_to_2026-10-06_processed.parquet

uv run indexpilot-simulate \
  --data data/demo/aapl_daily_2015-01-01_to_2026-10-06_processed.parquet \
  --config configs/stage-2.toml \
  --output-dir outputs/baseline-demo

uv run indexpilot-chart --run-dir outputs/baseline-demo
```

Simulator xuất summary và bảng equity/ledger/orders/trades/intervals cho sáu baselines. Output directory phải mới; dùng tên khác khi thử tiếp.

Muốn quan sát vòng học:

```bash
uv run indexpilot-train \
  --data data/demo/aapl_daily_2015-01-01_to_2026-10-06_processed.parquet \
  --config configs/stage-3.toml \
  --output-dir outputs/learning-demo

uv run indexpilot-chart --run-dir outputs/learning-demo
```

Training chạy 100 episodes cho mỗi lambda grid và selection bằng validation. Chart learning run mở validation của model được chọn; không phải final test.

Fresh download có thể đổi adjustments/hash, metrics và selected lambda. Prepare final evaluation hiện yêu cầu source selection khớp primary lambda trong config; mismatch sẽ dừng. Để tái lập kết quả đã công bố, dùng archive và exact hashes thay vì sửa config theo kết quả test mới.

Ví dụ một order có target +0,5 nhưng holdings không nhất thiết bằng 500 units: units phụ thuộc price, current account và phí. Xem [simulator](04-simulator.md) để truy kế toán.

## Tra cứu lệnh

```bash
uv run indexpilot-fetch --help
uv run indexpilot-process --help
uv run indexpilot-inspect --help
uv run indexpilot-simulate --help
uv run indexpilot-train --help
uv run indexpilot-evaluate --help
uv run indexpilot-evaluate prepare --help
uv run indexpilot-chart --help
```

Tham số simulation/learning/evaluation đặt trong các TOML version-controlled, không sửa outputs để thay cấu hình. Tests tổng hợp có thể chạy bằng uv run pytest -q mà không cần Yahoo hoặc market snapshot.

**Đọc tiếp:** [dữ liệu](03-data.md) để hiểu giá/timing; [tái lập](08-reproduction.md) để restore và xử lý lỗi.
