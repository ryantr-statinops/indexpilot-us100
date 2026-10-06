# 08 — Tái lập experiment

## Mục lục

- [Cần những gì](#cần-những-gì)
- [Restore archive trong checkout sạch](#restore-archive-trong-checkout-sạch)
- [Replay và verify](#replay-và-verify)
- [Sinh report và PNG từ artifacts](#sinh-report-và-png-từ-artifacts)
- [Chuẩn bị lại từ source](#chuẩn-bị-lại-từ-source)
- [Xử lý lỗi thường gặp](#xử-lý-lỗi-thường-gặp)

## Cần những gì

Exact reproduction dùng **cùng bytes của snapshot, models và config đã khóa**. Repository chỉ chứa code/config/tài liệu; data, checkpoints và detailed outputs bị Git ignore.

| Input | Cần cho |
|---|---|
| Repository và uv.lock tương thích protocol | Chạy evaluator/verify |
| Exact processed Parquet | Run hoặc recompute verify |
| protocol.json, frozen_models và preparation | Load/check frozen inventory và provenance |
| Saved runs/summaries/manifest | Reuse completed run, đối chiếu verify, report/chart |
| Source learning run | Prepare lại inventory từ source |
| Experiment ledger | Giữ lịch sử đã chuẩn bị/đánh giá |

Archive local hiện có là outputs/stage-4/aapl-reproduction.tar.gz, khoảng 16 MB. Manifest kèm theo là outputs/stage-4/reproduction_archive_manifest.json.

```text
Archive SHA256:
4a47e5d16e617a14328b37be2869cc2e7825b803f14bcfba4ff8c63e68789889

Dataset SHA256:
042605225d9f9dc91ac983ceb13079f09077a569bd485dd06774263f994db3cc

Protocol ID:
5fbce9eb3c97815487c57b7eaca4502390562e37ed062609d72c87ba189ec18b

Calculation revision:
b6c550da754fec519d14b7a0a9610a219b303904
```

Archive nằm trên máy đã chạy experiment, không được tải cùng Git clone. Cần chuyển bản archive riêng theo quyền sử dụng dữ liệu. Fresh Yahoo download không được coi là exact replacement nếu hash khác.

## Restore archive trong checkout sạch

Ví dụ với archive được đặt ở một đường dẫn riêng trên máy:

```bash
git clone https://github.com/ryantr-statinops/indexpilot-us100.git indexpilot-us100-frozen
cd indexpilot-us100-frozen
git checkout --detach b6c550d
uv sync --python 3.11.16 --frozen --extra dev --extra charts

sha256sum /absolute/path/aapl-reproduction.tar.gz
tar -xzf /absolute/path/aapl-reproduction.tar.gz \
  data/raw/aapl_daily_2015-01-01_to_2026-10-06_processed.parquet \
  outputs/stage-3/aapl-default \
  outputs/stage-4/aapl-frozen \
  outputs/stage-4/experiment-ledger.jsonl
```

Thay đường dẫn archive bằng file thực tế. Các members được trích là inputs/artifacts của experiment. Chạy trong checkout mới để không đè lên experiment local khác.

Code revision khi khóa là b6c550d. Main hiện đã có hardening và refactor Python, nên exact run/verify của archive cũ cần checkout này. Giữ protocol/model/data hashes nguyên trạng; không cập nhật fingerprint cũ để vượt lỗi. Đọc tài liệu hiện tại từ main, và chạy các lệnh replay trong checkout frozen riêng. Report/chart đọc artifacts cũ được cả trên main.

Revision chỉ đổi docs vẫn tương thích; thay code kể cả formatting/types/report helpers bị phát hiện vì fingerprint bao gồm toàn package Python.

## Replay và verify

Khi chuyển máy, đường dẫn input_file tuyệt đối trong protocol có thể trỏ về máy cũ. Dùng --data để cung cấp file đã restore; SHA256 vẫn phải khớp:

```bash
uv run indexpilot-evaluate run \
  --protocol-dir outputs/stage-4/aapl-frozen \
  --data data/raw/aapl_daily_2015-01-01_to_2026-10-06_processed.parquet

uv run indexpilot-evaluate verify \
  --protocol-dir outputs/stage-4/aapl-frozen \
  --data data/raw/aapl_daily_2015-01-01_to_2026-10-06_processed.parquet
```

Với completed archive, run kiểm tra integrity rồi trả artifacts; verify thực sự recompute 60 scenarios trong directory verification-* mới và so với bản đã lưu. Có thể chạy run để resume một experiment chưa hoàn tất; scenarios hoàn tất được hash-check trước khi reuse.

Verify đối chiếu decisions, RL transitions, accounting Parquet, metrics/diagnostics và summary files. Timestamp/Git fields của exporter không thuộc so sánh số liệu, nhưng provenance files vẫn nằm trong completion hashes. Verified event được append vào ledger.

Có thể chạy tests fixture độc lập với snapshot/Yahoo:

```bash
uv run pytest -q
```

Experiment AAPL tại revision đã khóa có 175 tests và independent 60-scenario replay trong clean venv. Suite main sau hardening có 191 tests; fixtures kiểm tra adjusted-close requirement, thay input giữa preparation, atomic manifest/recovery, December insolvency coverage và report composition. Matrix tổng hợp trước/sau refactor giữ nguyên summaries, accounting tables và Q/visits; generated report giữ output byte-identical. AAPL đã được verify lại 60/60 ở checkout b6c550d riêng sau hardening.

## Sinh report và PNG từ artifacts

Các lệnh này đọc saved results, không train hoặc evaluate lại:

```bash
uv run indexpilot-evaluate report --protocol-dir outputs/stage-4/aapl-frozen

uv run indexpilot-chart --run-dir outputs/stage-4/aapl-frozen \
  --save-png outputs/stage-4/aapl-frozen/figures/primary.png

QT_QPA_PLATFORM=offscreen uv run indexpilot-chart \
  --run-dir outputs/stage-4/aapl-frozen --seeds --risk-lambda 2 --cost-bps 10 \
  --save-png outputs/stage-4/aapl-frozen/figures/primary-seeds.png
```

Report mặc định là report.md trong run directory. Optional --output cho phép chọn nơi lưu bản xuất; tài liệu [kết quả](07-results.md) là phần giải thích biên tập riêng, còn generated report nằm local.

Chart có hai panel equity/drawdown; --cost-bps chọn cost đã khai báo, --seeds và --risk-lambda chọn tất cả RL seeds của một lambda. --save-png render bằng Qt rồi đóng cửa sổ. Offscreen dùng được khi máy không có desktop display; core evaluator không cần charts extra.

Có thể đọc bảng trực tiếp:

```python
import polars as pl

root = "outputs/stage-4/aapl-frozen"
print(pl.read_csv(f"{root}/primary_summary.csv"))
print(pl.read_csv(f"{root}/paired_comparison.csv"))
```

## Chuẩn bị lại từ source

Để tạo protocol mới bằng hardening, dùng **checkout main riêng**, restore exact snapshot/source learning run và ledger, chọn output directory khác và ghi reason sau một completed test. Các lệnh ở phần này chạy trên main:

```bash
uv run indexpilot-evaluate prepare \
  --data data/raw/aapl_daily_2015-01-01_to_2026-10-06_processed.parquet \
  --source-run outputs/stage-3/aapl-default \
  --config configs/stage-4.toml \
  --output-dir outputs/stage-4/aapl-reprepared \
  --reason "Tái dựng inventory từ archived training inputs"
```

Prepare copy hai seed-42 checkpoints và train tám model bổ sung trên training cũ; chưa evaluate test. Protocol ID mới vì preparation timestamp khác. Muốn replay **experiment cũ**, dùng archived inventory và protocol cũ thay vì prepare lại.

Raw CSV cũng có thể reprocess để học pipeline, nhưng exact reproduction cần hash đúng Parquet đã khóa. Không tự bỏ qua hash mismatch.

## Xử lý lỗi thường gặp

| Lỗi | Cách xử lý |
|---|---|
| Thiếu Parquet/models/artifacts sau clone | Restore đúng archived inputs; đọc prerequisites trước khi chạy |
| Data hash changed | Tìm đúng snapshot có hash đã ghi; đổi đường dẫn bằng --data nếu bytes đúng |
| Model/log/source hash changed | Restore bản archive nguyên vẹn, đối chiếu archive manifest |
| Code hoặc dependency lock changed | Archive AAPL cũ dùng b6c550d; main hardening cần protocol mới, không sửa fingerprint cũ |
| Numerical runtime differs | Tạo venv riêng bằng Python 3.11.16 và frozen lock |
| Output prepare đã tồn tại | Dùng thư mục mới; run/verify dùng protocol đã có |
| New protocol requires reason | Cung cấp lý do cụ thể, giữ lịch sử ledger; không chọn lại theo test |
| This protocol is already being evaluated | Kiểm tra process đang chạy và chờ nó kết thúc |
| Scenario/summary integrity failed | Giữ bản lỗi để audit, restore outputs đúng hash |
| Chart thiếu FinPlot/display | Cài extra charts; dùng desktop hoặc QT_QPA_PLATFORM=offscreen cho PNG |
| Insufficient warm-up/no interval | Kiểm tra boundary và số phiên lịch sử; không fill giá để vượt lỗi |

Evaluator dùng fcntl cho locking; runtime được kiểm chứng là Linux. Windows support chưa được triển khai.

Backups local nên giữ exact snapshot, source, frozen inventory, detailed results và ledger cùng nhau. Report/CSV giúp đọc kết quả; chúng không thay thế checkpoints và snapshot cho recomputation.

**Đọc tiếp:** [README dự án](../README.md) dẫn tới quickstart và mục lục các chương.
