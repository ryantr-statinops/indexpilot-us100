# 01 — Tổng quan dự án

## Mục lục

- [Bài toán và kết quả](#bài-toán-và-kết-quả)
- [Phạm vi mô phỏng](#phạm-vi-mô-phỏng)
- [Stack thực tế](#stack-thực-tế)
- [Kiến trúc và luồng dữ liệu](#kiến-trúc-và-luồng-dữ-liệu)
- [Cách đọc dự án](#cách-đọc-dự-án)

## Bài toán và kết quả

IndexPilot US100 là dự án học reinforcement learning thông qua mô phỏng quyết định vị thế cổ phiếu. Prototype đã hoàn thành dùng **AAPL, dữ liệu daily**: mỗi phiên policy chọn tỷ trọng short, flat hoặc long; simulator tính cash, holdings, phí và equity.

Câu hỏi nghiên cứu là: một policy Q-learning học trên lịch sử cũ có giữ được hiệu quả trên dữ liệu về sau, so với các baseline đơn giản không?

Kết quả đã lưu cho thấy model chính gần như luôn flat và không vượt cash hay buy-and-hold trong test. Giá trị của prototype là có thể giải thích từng quyết định, đối soát kế toán và tái lập experiment; hoàn thành dự án không yêu cầu RL có lợi nhuận.

Ví dụ, action +0,5 nghĩa là đưa giá trị vị thế long về 50% equity **sau phí**. Nó không có nghĩa mua thêm 50% vốn mỗi phiên. Action 0 đóng vị thế; −0,5 tạo vị thế short tương đương 50% equity sau phí.

## Phạm vi mô phỏng

| Nội dung | Quy ước |
|---|---|
| Tài sản đã triển khai | Một mã AAPL |
| Tần suất | Daily, giữ từ open hiện tại đến open tiếp theo |
| Giá giao dịch mô phỏng | Synthetic adjusted open |
| Tài khoản | Cash và đơn vị tổng hợp, cho phép đơn vị lẻ |
| Vốn ban đầu | $100.000, flat mỗi episode |
| Agent | NumPy tabular Q-learning, năm actions |
| Đánh giá | Training đến hết 2020, validation 2021–2022, test từ 2023 |
| Prototype hoàn chỉnh | Pipeline, simulator, baselines, agent, frozen evaluation, report/chart |

**US100** trong tên dự án là hướng mở rộng: 100 công ty niêm yết tại Mỹ lớn nhất theo market capitalization tại từng ngày hình thành universe. Đây không phải Nasdaq-100 hoặc S&P 100. Prototype chưa có dữ liệu membership lịch sử, multi-asset allocation hay agent cho 100 mã.

Mô hình short chưa có borrow fee, financing, margin call; phí giao dịch là tỷ lệ đơn giản trên traded notional. Chưa có live execution, PPO hoặc walk-forward.

## Stack thực tế

| Vai trò | Công cụ và cách dùng |
|---|---|
| Ngôn ngữ | Python; experiment đã khóa dùng 3.11.16 |
| Số học và agent | NumPy: arrays float64, RNG, Q table và state encoding |
| Dữ liệu và exports | Polars: CSV, typed Parquet, bảng kết quả |
| Diagnostic thống kê | statsmodels: Augmented Dickey-Fuller trong lệnh inspect |
| Nguồn giá | yfinance truy cập Yahoo Finance |
| Adapter dữ liệu | pandas tại biên yfinance và chart; không thay Polars ở core |
| Biểu đồ | FinPlot, Qt/PyQt6; optional extra charts |
| Đóng gói | uv, pyproject.toml và uv.lock |
| Kiểm chứng | pytest; suite đã kiểm chứng có 175 tests |

Agent hiện tại không cần PyTorch hoặc Gymnasium. Environment dùng episode API riêng; statsmodels không được dùng để chọn actions hoặc train Q.

Cấu hình thực tế nằm ở [configs](../configs/); dependencies và entry points nằm trong [pyproject.toml](../pyproject.toml). Dùng lockfile để tái tạo numerical environment thay vì tự chọn phiên bản thư viện mới.

## Kiến trúc và luồng dữ liệu

```text
Yahoo/yfinance
    ↓ normalize pandas → Polars
raw CSV + processed Parquet + data manifest
    ↓ validate dates/prices, causal features
MarketData + portfolio simulator
    ├── six baseline policies → accounting artifacts + metrics
    └── TradingEnvironment → finalized transitions
             ↓ Q-learning updates after rollout
        checkpoints + training logs + validation selection
             ↓ freeze inventory/config/data/code hashes
        60 test scenarios → summaries + diagnostics
             ↓ read persisted artifacts
        report + equity/drawdown charts
```

Trong [src/indexpilot_us100](../src/indexpilot_us100/):

| Module | Trách nhiệm |
|---|---|
| data | Download, processing và inspect snapshot |
| portfolio | Account, execution, interval transition, trades và simulator |
| environment | Adapter tạo RL transitions từ simulator |
| agents | Bins/actions, Q-learning và training |
| metrics | Sharpe, MDD, CAGR, Profit Factor, Calmar |
| evaluation | CLI, exports, chart và frozen final evaluation |

RL và baselines dùng **cùng accounting engine**. Risk penalty chỉ thay reward; financial metrics được tính từ tài khoản sau phí.

Data, checkpoints và outputs được lưu local trong các thư mục bị Git ignore. Clone repository chỉ đem về code/config/tài liệu; không tự có experiment inputs.

## Cách đọc dự án

Nếu học từ đầu, đi qua dữ liệu → simulator → Q-learning → evaluation → kết quả. Nếu muốn chạy lại experiment, bắt đầu với prerequisites và archive đã khóa; fresh download không bảo đảm cùng bytes hoặc historical adjustments.

**Đọc tiếp:** [README dự án](../README.md) dẫn tới mục lục tài liệu và hướng dẫn chạy.
