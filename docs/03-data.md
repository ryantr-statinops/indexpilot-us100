# 03 — Dữ liệu và snapshot

## Mục lục

- [Nguồn và định dạng lưu](#nguồn-và-định-dạng-lưu)
- [Giá điều chỉnh và returns](#giá-điều-chỉnh-và-returns)
- [Snapshot của experiment](#snapshot-của-experiment)
- [Chất lượng và causal features](#chất-lượng-và-causal-features)
- [Splits và warm-up](#splits-và-warm-up)
- [Download và xử lý lại](#download-và-xử-lý-lại)

## Nguồn và định dạng lưu

Pipeline lấy AAPL daily qua yfinance với `auto_adjust=False` và corporate actions bật. pandas nhận kết quả từ provider; dữ liệu sau đó được chuẩn hóa sang Polars.

| Artifact local | Vai trò |
|---|---|
| Raw CSV | Snapshot bảng nguồn đã normalize: OHLC, adjusted close, volume và các corporate actions có sẵn |
| Processed Parquet | Bảng có kiểu dữ liệu rõ ràng, bổ sung adjusted open và returns |
| Data manifest JSON | Parameters, retrieval time, row/date coverage, quality checks, phiên bản và SHA256 |

Raw CSV là bảng normalize, không phải archive byte-for-byte của HTTP response. OHLC nguồn vẫn chưa điều chỉnh; simulator dùng các cột adjusted riêng.

yfinance là đường truy cập không chính thức. Archive của dự án được giữ local; tham khảo [ghi chú sử dụng yfinance](https://github.com/ranaroussi/yfinance#download-market-data-from-yahoo-finances-api) và [điều khoản dữ liệu Yahoo](https://uk.help.yahoo.com/kb/exchanges-data-providers-yahoo-finance-sln2310.html) trước khi chia sẻ dữ liệu.

## Giá điều chỉnh và returns

Với mỗi dòng:

```text
factor = adj_close / close
adj_open = open * factor
simple_return[i] = adj_close[i] / adj_close[i-1] - 1
log_return[i] = log(adj_close[i] / adj_close[i-1])
open_to_open_return[i] = adj_open[i] / adj_open[i-1] - 1
```

Synthetic adjusted open áp dụng hệ số adjusted-close lên open. Nó là giá của chuỗi kế toán điều chỉnh, không phải một historical fill thực tế. Holdings của simulator là **đơn vị tổng hợp** trên chuỗi đó; không cộng dividend hoặc split thêm lần nữa.

Ví dụ từ snapshot:

```text
adj_open ngày 2015-01-02 = 24,6271994096
adj_open ngày 2015-01-05 = 23,9418205485
return = 23,9418205485 / 24,6271994096 - 1
       ≈ −2,7830%
```

Return lưu tại dòng i mô tả **open i−1 → open i**. Outcome của action tại open i phải dùng **open i → open i+1**. Simulator tính P&L trực tiếp từ hai giá đã dùng; không tin cột return có sẵn để thực hiện kế toán.

## Snapshot của experiment

| Thuộc tính | Giá trị đã lưu |
|---|---|
| Ticker / interval | AAPL / 1d |
| Request | 2015-01-01 inclusive → 2026-10-06 exclusive |
| Coverage thực tế | 2015-01-02 → 2026-10-02 |
| Rows | 2.955 |
| Returns open-to-open | 2.954, dòng đầu null |
| Duplicate dates | 0 |
| Null hoặc non-positive price rows | 0 |
| Retrieval | 2026-10-05, khoảng 05:01 UTC |
| Provider adapter | yfinance 0.2.66 |

Processed file:

```text
data/raw/aapl_daily_2015-01-01_to_2026-10-06_processed.parquet
SHA256:
042605225d9f9dc91ac983ceb13079f09077a569bd485dd06774263f994db3cc
```

Tên file ghi request end, không phải ngày giao dịch cuối. Experiment kết thúc tại open 2026-10-02; không bao gồm return open-to-close của ngày đó. Năm 2026 chưa đủ.

Provider có thể sửa historical adjustments. Fresh download cùng ticker/date range vẫn có thể khác hash, nên không thay thế exact snapshot trong một protocol đã khóa.

## Chất lượng và causal features

Market loader yêu cầu `date`, `adj_open`, `adj_close`; dates phải là daily Date, duy nhất và tăng nghiêm ngặt. Giá phải finite, lớn hơn 0 và không null. Loader không tự sort, fill giá, tạo phiên hoặc fallback về raw open.

Weekend/holiday tự nhiên không phải lỗi. Gaps lớn hơn bốn ngày lịch được cảnh báo; dự án chưa dùng exchange calendar để chứng minh đủ mọi phiên.

Tại quyết định ở dòng i:

| Feature | Dữ liệu được dùng |
|---|---|
| Return 1/5/20 phiên | Adjusted closes kết thúc tại i−1 |
| Prior close / SMA20 | Close i−1 / mean của 20 closes trước i |
| Risk volatility | Sample std, ddof=1, của 20 open returns kết thúc trước open i |
| Account state | Cash, holdings, equity, exposure, drawdown mark bằng quote open i |

Open i được dùng định giá tài khoản; open i+1 không nằm trong observation. Các bins của agent được cố định, không fit scaler trên validation hoặc test.

Lệnh inspect dùng statsmodels ADF cho open returns. Trong snapshot, sample mean khoảng 0,00105685 và std khoảng 0,01868915; ADF statistic khoảng −33,822680. Diagnostic này không chứng minh returns dự báo được. P-value hiển thị 0 do underflow số thực không có nghĩa p-value toán học bằng 0.

## Splits và warm-up

| Segment | Boundary đã khai báo | Coverage được đánh giá |
|---|---|---|
| Training | Đến 2020-12-31 | 2015-02-03 → 2020-12-31; 1.489 intervals |
| Validation | 2021-01-01 → 2022-12-31 | 2021-01-04 → 2022-12-30; 502 intervals |
| Test | 2023-01-01 → 2026-10-02 | 2023-01-03 → 2026-10-02; 940 intervals |

Risk window mặc định 20. Cần `max(20, risk_window)+1` dòng trước quyết định đầu; với window 20, index đầu là 21 và cần ít nhất 23 rows để có một holding interval.

Validation/test dùng lịch sử trước boundary làm warm-up, nhưng các phiên đó không thuộc equity curve hoặc metrics. Tài khoản mỗi segment reset flat/$100.000; không mang holdings từ training hoặc validation sang test.

## Download và xử lý lại

Ví dụ lấy **snapshot mới**, lưu vào thư mục riêng để không thay archived input:

```bash
uv run indexpilot-fetch --ticker AAPL --start 2015-01-01 --end 2026-10-06 --output-dir data/new-snapshot
uv run indexpilot-inspect data/new-snapshot/aapl_daily_2015-01-01_to_2026-10-06_processed.parquet
```

Mặc định end của downloader là ngày UTC hiện tại, exclusive. Với raw CSV đã archive:

```bash
uv run indexpilot-process data/raw/aapl_daily_2015-01-01_to_2026-10-06_raw.csv --output data/reprocessed/aapl.parquet
```

Xử lý lại không cần Yahoo/network. File Parquet mới cần kiểm tra hash nếu định dùng cho exact reproduction; không mặc nhiên coi cùng nội dung bảng là cùng bytes.

Liên quan: [phạm vi và kiến trúc](01-overview.md).
**Đọc tiếp:** [README dự án](../README.md) dẫn tới các chương về simulator và tái lập.
