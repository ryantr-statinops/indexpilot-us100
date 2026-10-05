# Báo cáo hoàn thiện prototype AAPL

## 1. Câu hỏi nghiên cứu và phạm vi

Đánh giá Q-learning đã chọn bằng validation trên test dành riêng; mô tả độ ổn định theo seed và chi phí, cùng khả năng tái lập. Đây là prototype một tài sản AAPL; chưa phải kết luận cho US100.

## 2. Dữ liệu và splits

Training kết thúc 2020-12-31; validation 2021-01-01–2022-12-31. Test thực tế 2023-01-03–2026-10-02, 940 khoảng open-to-open. Năm cuối 2026 chưa đủ nếu snapshot kết thúc trước 31/12.

Synthetic adjusted open dùng hệ số adjusted close/raw close; holdings là đơn vị tổng hợp. Không cộng dividend/split lần nữa. Features trễ một phiên; warm-up chỉ cung cấp lịch sử, không thuộc metric coverage. Thiếu phiên không tự điền và chưa xác minh đủ lịch sàn.

Dataset SHA256: `042605225d9f9dc91ac983ceb13079f09077a569bd485dd06774263f994db3cc`.

## 3. Simulator và metrics

Equity = cash + holdings × price; reset flat $100.000 mỗi run. Target exposure được giải trên equity sau phí. Long/short, đơn vị lẻ, cash rate 0; chưa có borrow fee, margin call hay financing. Exposure chỉ giới hạn khi đặt target và có thể trôi. Đóng cuối có phí gộp vào interval cuối. Equity không bị chặn tại 0 khi insolvent.

Sharpe: net interval returns, ddof=1, annualization 252, risk-free 0. MDD: toàn bộ ledger kể cả sau phí. CAGR: số ngày lịch/365,25. PF: net P&L mỗi đợt vị thế, fees phân bổ reversal. Calmar = CAGR/MDD. N/A và ∞ được giữ rõ trạng thái. Reward được báo riêng, không dùng như P&L.

## 4. State, actions và Q-learning

State cố định gồm return/momentum, volatility, exposure và drawdown bins; 3.840 states × 5 actions {-1,-0,5,0,0,5,1}. Reward = gross portfolio return − λ × risk − cost fraction; risk không trừ equity. Mỗi episode tạo rollout rồi cập nhật Q theo thứ tự thời gian trên transitions đã finalize. Greedy evaluation ε=0 với Q/visits chỉ đọc; không bootstrap terminal.

## 5. Protocol đã khóa

Protocol ID: `5fbce9eb3c97815487c57b7eaca4502390562e37ed062609d72c87ba189ec18b`. Code revision khi chuẩn bị: `b6c550da754fec519d14b7a0a9610a219b303904`. Source manifest SHA256: `8f7b6151b7135669fec67e6ae5b892165c6b715396da9e8cd30d3a92c27e1ea2`. Primary λ=2, reference λ=0, seed 42; chính luôn 10 bps. Hai checkpoint seed 42 được sao chép nguyên trạng từ Stage 3. Seeds [42, 7, 21, 84, 123] dùng cùng bins/hyperparameters; seed bổ sung chỉ train trên training cũ. Không train lại primary hoặc chọn lambda/seed theo test.

Inventory 10 model, 60 scenarios. Protocol lưu hashes data/models/training logs/source/code/uv.lock và runtime. Ledger append-only ghi chuẩn bị, bắt đầu, hoàn tất, lỗi và verify.

## 6. Kết quả test chính

| Policy | λ | Net return | Sharpe | MDD | CAGR | PF | Calmar | Trades | Active | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| q_lambda_0 | 0.0000 | -17.42% | -0.1962 | 35.69% | -4.98% | 0.9078 | -0.1396 | 266 | 760 | completed |
| q_lambda_2 | 2.0000 | -0.76% | -0.4790 | 0.90% | -0.20% | 0.1110 | -0.2252 | 2 | 2 | completed |
| cash | 2.0000 | 0.00% | N/A | 0.00% | 0.00% | N/A | N/A | 0 | 0 | completed |
| buy_hold | 2.0000 | 159.85% | 1.0741 | 33.33% | 29.04% | ∞ | 0.8714 | 1 | 940 | completed |
| fixed_long_50 | 2.0000 | 66.44% | 1.0687 | 17.87% | 14.57% | ∞ | 0.8155 | 1 | 940 | completed |
| fixed_short_50 | 2.0000 | -44.69% | -1.0944 | 46.14% | -14.63% | 0.0000 | -0.3170 | 1 | 940 | completed |
| sma20_long_flat | 2.0000 | 80.61% | 0.9620 | 27.12% | 17.10% | 2.0797 | 0.6306 | 40 | 575 | completed |
| random_discrete | 2.0000 | 41.28% | 0.5497 | 29.09% | 9.66% | 1.1299 | 0.3323 | 450 | 740 | completed |

| Policy | Initial equity | Final equity | Fees | Traded notional | Turnover | Orders | Wins | Losses | Flat P&L | Actual start | Actual end | Intervals |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| q_lambda_0 | 100,000.0000 | 82,583.9620 | 45,755.4135 | 45,755,413.4823 | 458.4184 | 655 | 121 | 145 | 0 | 2023-01-03 | 2026-10-02 | 940 |
| q_lambda_2 | 100,000.0000 | 99,239.6149 | 199.4340 | 199,433.9933 | 1.9967 | 4 | 1 | 1 | 0 | 2023-01-03 | 2026-10-02 | 940 |
| cash | 100,000.0000 | 100,000.0000 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2023-01-03 | 2026-10-02 | 940 |
| buy_hold | 100,000.0000 | 259,848.5576 | 360.0088 | 360,008.7662 | 1.9990 | 2 | 1 | 0 | 0 | 2023-01-03 | 2026-10-02 | 940 |
| fixed_long_50 | 100,000.0000 | 166,436.5573 | 496.7281 | 496,728.0824 | 3.7441 | 941 | 1 | 0 | 0 | 2023-01-03 | 2026-10-02 | 940 |
| fixed_short_50 | 100,000.0000 | 55,309.0168 | 686.9657 | 686,965.7312 | 9.2546 | 941 | 0 | 1 | 0 | 2023-01-03 | 2026-10-02 | 940 |
| sma20_long_flat | 100,000.0000 | 180,613.4966 | 11,287.8515 | 11,287,851.5318 | 79.9600 | 80 | 21 | 19 | 0 | 2023-01-03 | 2026-10-02 | 940 |
| random_discrete | 100,000.0000 | 141,276.2265 | 96,136.8672 | 96,136,867.1953 | 763.2603 | 851 | 217 | 233 | 0 | 2023-01-03 | 2026-10-02 | 940 |

## 7. Seed/cost sensitivity và mức hoạt động

| Policy | Seed | bps | Return | Sharpe | MDD | Trades | Active | Flat actions | Unseen states | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| q_lambda_0 | 42 | 0.0000 | 72.43% | 0.8865 | 16.78% | 253 | 716 | 23.83% | 2.66% | completed |
| q_lambda_2 | 42 | 0.0000 | -0.56% | -0.3717 | 0.76% | 2 | 2 | 99.79% | 2.55% | completed |
| q_lambda_0 | 7 | 0.0000 | 22.81% | 0.3869 | 36.36% | 229 | 772 | 17.87% | 3.30% | completed |
| q_lambda_2 | 7 | 0.0000 | -1.67% | -0.5216 | 2.05% | 2 | 3 | 99.68% | 2.45% | completed |
| q_lambda_0 | 21 | 0.0000 | -11.42% | -0.0539 | 38.61% | 259 | 778 | 17.23% | 2.55% | completed |
| q_lambda_2 | 21 | 0.0000 | -0.83% | -0.5216 | 1.03% | 2 | 3 | 99.68% | 2.45% | completed |
| q_lambda_0 | 84 | 0.0000 | 41.36% | 0.6191 | 26.15% | 259 | 726 | 22.77% | 3.09% | completed |
| q_lambda_2 | 84 | 0.0000 | -1.13% | -0.3717 | 1.51% | 2 | 2 | 99.79% | 2.55% | completed |
| q_lambda_0 | 123 | 0.0000 | 9.25% | 0.2193 | 46.72% | 271 | 776 | 17.45% | 3.19% | completed |
| q_lambda_2 | 123 | 0.0000 | 1.38% | 0.2717 | 1.51% | 3 | 4 | 99.57% | 2.55% | completed |
| q_lambda_0 | 42 | 10.0000 | -17.42% | -0.1962 | 35.69% | 266 | 760 | 19.15% | 2.77% | completed |
| q_lambda_2 | 42 | 10.0000 | -0.76% | -0.4790 | 0.90% | 2 | 2 | 99.79% | 2.55% | completed |
| q_lambda_0 | 7 | 10.0000 | -13.24% | -0.0827 | 47.07% | 218 | 793 | 15.64% | 3.30% | completed |
| q_lambda_2 | 7 | 10.0000 | -2.06% | -0.6180 | 2.34% | 2 | 3 | 99.68% | 2.45% | completed |
| q_lambda_0 | 21 | 10.0000 | -29.65% | -0.3501 | 45.63% | 241 | 781 | 16.91% | 2.55% | completed |
| q_lambda_2 | 21 | 10.0000 | -1.03% | -0.6177 | 1.17% | 2 | 3 | 99.68% | 2.45% | completed |
| q_lambda_0 | 84 | 10.0000 | -27.97% | -0.3971 | 43.96% | 249 | 701 | 25.43% | 2.77% | completed |
| q_lambda_2 | 84 | 10.0000 | -1.52% | -0.4792 | 1.81% | 2 | 2 | 99.79% | 2.55% | completed |
| q_lambda_0 | 123 | 10.0000 | -29.94% | -0.3853 | 52.06% | 268 | 786 | 16.38% | 3.19% | completed |
| q_lambda_2 | 123 | 10.0000 | 0.78% | 0.1547 | 1.71% | 3 | 4 | 99.57% | 2.55% | completed |
| q_lambda_0 | 42 | 20.0000 | -34.52% | -0.5312 | 46.00% | 265 | 764 | 18.72% | 2.77% | completed |
| q_lambda_2 | 42 | 20.0000 | -0.96% | -0.5699 | 1.05% | 2 | 2 | 99.79% | 2.55% | completed |
| q_lambda_0 | 7 | 20.0000 | -37.43% | -0.5109 | 55.66% | 218 | 789 | 16.06% | 3.30% | completed |
| q_lambda_2 | 7 | 20.0000 | -2.45% | -0.6990 | 2.63% | 2 | 3 | 99.68% | 2.45% | completed |
| q_lambda_0 | 21 | 20.0000 | -50.23% | -0.7766 | 56.23% | 236 | 776 | 17.45% | 2.55% | completed |
| q_lambda_2 | 21 | 20.0000 | -1.23% | -0.6984 | 1.32% | 2 | 3 | 99.68% | 2.45% | completed |
| q_lambda_0 | 84 | 20.0000 | -57.72% | -1.1134 | 65.63% | 222 | 762 | 18.94% | 2.98% | completed |
| q_lambda_2 | 84 | 20.0000 | -1.91% | -0.5703 | 2.10% | 2 | 2 | 99.79% | 2.55% | completed |
| q_lambda_0 | 123 | 20.0000 | -53.69% | -0.9376 | 62.29% | 267 | 794 | 15.53% | 3.19% | completed |
| q_lambda_2 | 123 | 20.0000 | 0.17% | 0.0398 | 1.90% | 3 | 4 | 99.57% | 2.55% | completed |

### Thống kê qua seed

Mean/median/std chỉ dùng metric hữu hạn; sample std cần ít nhất hai giá trị. Số undefined/infinite/not applicable/insolvent vẫn được báo. Baseline xác định không được nhân bản thành năm mẫu. Random là sanity check. Đây là biến thiên quá trình học trên cùng lịch sử, không phải khoảng tin cậy cho lợi nhuận tương lai.

| Policy | bps | Metric | Mean | Median | Std | Min | Max | Finite | Undefined | ∞ | N/A | Insolvent |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| random_discrete | 0.0000 | net_return | 0.6493 | 0.6116 | 0.8390 | -0.0300 | 2.0322 | 5 | 0 | 0 | 0 | 0 |
| random_discrete | 0.0000 | sharpe | 0.6455 | 0.7622 | 0.6107 | 0.0583 | 1.5428 | 5 | 0 | 0 | 0 | 0 |
| random_discrete | 0.0000 | max_drawdown | 0.2621 | 0.2396 | 0.0899 | 0.1788 | 0.4152 | 5 | 0 | 0 | 0 | 0 |
| random_discrete | 0.0000 | cagr | 0.1222 | 0.1359 | 0.1440 | -0.0081 | 0.3447 | 5 | 0 | 0 | 0 | 0 |
| random_discrete | 0.0000 | profit_factor | 1.1693 | 1.1968 | 0.1951 | 0.9889 | 1.4649 | 5 | 0 | 0 | 0 | 0 |
| random_discrete | 0.0000 | calmar | 0.6107 | 0.5663 | 0.7962 | -0.0338 | 1.9277 | 5 | 0 | 0 | 0 | 0 |
| random_discrete | 0.0000 | total_fees | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 5 | 0 | 0 | 0 | 0 |
| random_discrete | 0.0000 | trade_count | 446.6000 | 450.0000 | 8.1731 | 438.0000 | 456.0000 | 5 | 0 | 0 | 0 | 0 |
| random_discrete | 0.0000 | active_intervals | 751.8000 | 746.0000 | 13.2363 | 740.0000 | 773.0000 | 5 | 0 | 0 | 0 | 0 |
| random_discrete | 10.0000 | net_return | -0.2246 | -0.2319 | 0.3892 | -0.5458 | 0.4128 | 5 | 0 | 0 | 0 | 0 |
| random_discrete | 10.0000 | sharpe | -0.3593 | -0.2833 | 0.6059 | -0.9721 | 0.5497 | 5 | 0 | 0 | 0 | 0 |
| random_discrete | 10.0000 | max_drawdown | 0.4323 | 0.3943 | 0.1425 | 0.2909 | 0.5954 | 5 | 0 | 0 | 0 | 0 |
| random_discrete | 10.0000 | cagr | -0.0823 | -0.0680 | 0.1169 | -0.1900 | 0.0966 | 5 | 0 | 0 | 0 | 0 |
| random_discrete | 10.0000 | profit_factor | 0.8847 | 0.9043 | 0.1605 | 0.7362 | 1.1299 | 5 | 0 | 0 | 0 | 0 |
| random_discrete | 10.0000 | calmar | -0.1387 | -0.2088 | 0.2718 | -0.3339 | 0.3323 | 5 | 0 | 0 | 0 | 0 |
| random_discrete | 10.0000 | total_fees | 66,999.1401 | 67,813.5098 | 18,774.3189 | 48,694.4913 | 96,136.8672 | 5 | 0 | 0 | 0 | 0 |
| random_discrete | 10.0000 | trade_count | 446.6000 | 450.0000 | 8.1731 | 438.0000 | 456.0000 | 5 | 0 | 0 | 0 | 0 |
| random_discrete | 10.0000 | active_intervals | 751.8000 | 746.0000 | 13.2363 | 740.0000 | 773.0000 | 5 | 0 | 0 | 0 | 0 |
| random_discrete | 20.0000 | net_return | -0.6354 | -0.6339 | 0.1806 | -0.7873 | -0.3418 | 5 | 0 | 0 | 0 | 0 |
| random_discrete | 20.0000 | sharpe | -1.3603 | -1.3364 | 0.6048 | -1.9996 | -0.4385 | 5 | 0 | 0 | 0 | 0 |
| random_discrete | 20.0000 | max_drawdown | 0.6624 | 0.6570 | 0.1552 | 0.4173 | 0.7989 | 5 | 0 | 0 | 0 | 0 |
| random_discrete | 20.0000 | cagr | -0.2496 | -0.2353 | 0.0949 | -0.3385 | -0.1057 | 5 | 0 | 0 | 0 | 0 |
| random_discrete | 20.0000 | profit_factor | 0.6608 | 0.6763 | 0.1296 | 0.5361 | 0.8596 | 5 | 0 | 0 | 0 | 0 |
| random_discrete | 20.0000 | calmar | -0.3639 | -0.3645 | 0.0690 | -0.4263 | -0.2531 | 5 | 0 | 0 | 0 | 0 |
| random_discrete | 20.0000 | total_fees | 94,404.4491 | 95,487.1993 | 22,753.5630 | 70,782.6511 | 128,687.0929 | 5 | 0 | 0 | 0 | 0 |
| random_discrete | 20.0000 | trade_count | 446.6000 | 450.0000 | 8.1731 | 438.0000 | 456.0000 | 5 | 0 | 0 | 0 | 0 |
| random_discrete | 20.0000 | active_intervals | 751.8000 | 746.0000 | 13.2363 | 740.0000 | 773.0000 | 5 | 0 | 0 | 0 | 0 |
| q_lambda_0 | 0.0000 | net_return | 0.2689 | 0.2281 | 0.3193 | -0.1142 | 0.7243 | 5 | 0 | 0 | 0 | 0 |
| q_lambda_0 | 0.0000 | sharpe | 0.4116 | 0.3869 | 0.3616 | -0.0539 | 0.8865 | 5 | 0 | 0 | 0 | 0 |
| q_lambda_0 | 0.0000 | max_drawdown | 0.3292 | 0.3636 | 0.1163 | 0.1678 | 0.4672 | 5 | 0 | 0 | 0 | 0 |
| q_lambda_0 | 0.0000 | cagr | 0.0604 | 0.0564 | 0.0715 | -0.0318 | 0.1566 | 5 | 0 | 0 | 0 | 0 |
| q_lambda_0 | 0.0000 | profit_factor | 1.1357 | 1.1264 | 0.1580 | 0.9416 | 1.3569 | 5 | 0 | 0 | 0 | 0 |
| q_lambda_0 | 0.0000 | calmar | 0.2854 | 0.1551 | 0.3980 | -0.0825 | 0.9329 | 5 | 0 | 0 | 0 | 0 |
| q_lambda_0 | 0.0000 | total_fees | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 5 | 0 | 0 | 0 | 0 |
| q_lambda_0 | 0.0000 | trade_count | 254.2000 | 259.0000 | 15.5306 | 229.0000 | 271.0000 | 5 | 0 | 0 | 0 | 0 |
| q_lambda_0 | 0.0000 | active_intervals | 753.6000 | 772.0000 | 30.0466 | 716.0000 | 778.0000 | 5 | 0 | 0 | 0 | 0 |
| q_lambda_0 | 10.0000 | net_return | -0.2364 | -0.2797 | 0.0777 | -0.2994 | -0.1324 | 5 | 0 | 0 | 0 | 0 |
| q_lambda_0 | 10.0000 | sharpe | -0.2823 | -0.3501 | 0.1375 | -0.3971 | -0.0827 | 5 | 0 | 0 | 0 | 0 |
| q_lambda_0 | 10.0000 | max_drawdown | 0.4488 | 0.4563 | 0.0596 | 0.3569 | 0.5206 | 5 | 0 | 0 | 0 | 0 |
| q_lambda_0 | 10.0000 | cagr | -0.0702 | -0.0839 | 0.0249 | -0.0906 | -0.0372 | 5 | 0 | 0 | 0 | 0 |
| q_lambda_0 | 10.0000 | profit_factor | 0.8710 | 0.8576 | 0.0455 | 0.8241 | 0.9290 | 5 | 0 | 0 | 0 | 0 |
| q_lambda_0 | 10.0000 | calmar | -0.1560 | -0.1741 | 0.0484 | -0.1965 | -0.0790 | 5 | 0 | 0 | 0 | 0 |
| q_lambda_0 | 10.0000 | total_fees | 43,150.6035 | 44,790.6997 | 2,772.2236 | 39,683.1815 | 45,755.4135 | 5 | 0 | 0 | 0 | 0 |
| q_lambda_0 | 10.0000 | trade_count | 248.4000 | 249.0000 | 20.4524 | 218.0000 | 268.0000 | 5 | 0 | 0 | 0 | 0 |
| q_lambda_0 | 10.0000 | active_intervals | 764.2000 | 781.0000 | 37.4126 | 701.0000 | 793.0000 | 5 | 0 | 0 | 0 | 0 |
| q_lambda_0 | 20.0000 | net_return | -0.4672 | -0.5023 | 0.1021 | -0.5772 | -0.3452 | 5 | 0 | 0 | 0 | 0 |
| q_lambda_0 | 20.0000 | sharpe | -0.7739 | -0.7766 | 0.2599 | -1.1134 | -0.5109 | 5 | 0 | 0 | 0 | 0 |
| q_lambda_0 | 20.0000 | max_drawdown | 0.5716 | 0.5623 | 0.0751 | 0.4600 | 0.6563 | 5 | 0 | 0 | 0 | 0 |
| q_lambda_0 | 20.0000 | cagr | -0.1571 | -0.1700 | 0.0430 | -0.2053 | -0.1069 | 5 | 0 | 0 | 0 | 0 |
| q_lambda_0 | 20.0000 | profit_factor | 0.7324 | 0.6941 | 0.0661 | 0.6724 | 0.8179 | 5 | 0 | 0 | 0 | 0 |
| q_lambda_0 | 20.0000 | calmar | -0.2714 | -0.2983 | 0.0462 | -0.3129 | -0.2114 | 5 | 0 | 0 | 0 | 0 |
| q_lambda_0 | 20.0000 | total_fees | 73,814.3199 | 71,284.6726 | 6,290.7217 | 68,552.1404 | 83,290.1095 | 5 | 0 | 0 | 0 | 0 |
| q_lambda_0 | 20.0000 | trade_count | 241.6000 | 236.0000 | 23.2659 | 218.0000 | 267.0000 | 5 | 0 | 0 | 0 | 0 |
| q_lambda_0 | 20.0000 | active_intervals | 777.0000 | 776.0000 | 14.3875 | 762.0000 | 794.0000 | 5 | 0 | 0 | 0 | 0 |
| q_lambda_2 | 0.0000 | net_return | -0.0056 | -0.0083 | 0.0116 | -0.0167 | 0.0138 | 5 | 0 | 0 | 0 | 0 |
| q_lambda_2 | 0.0000 | sharpe | -0.3030 | -0.3717 | 0.3299 | -0.5216 | 0.2717 | 5 | 0 | 0 | 0 | 0 |
| q_lambda_2 | 0.0000 | max_drawdown | 0.0137 | 0.0151 | 0.0050 | 0.0076 | 0.0205 | 5 | 0 | 0 | 0 | 0 |
| q_lambda_2 | 0.0000 | cagr | -0.0015 | -0.0022 | 0.0031 | -0.0045 | 0.0037 | 5 | 0 | 0 | 0 | 0 |
| q_lambda_2 | 0.0000 | profit_factor | 0.1288 | 0.1286 | 0.1487 | 0.0000 | 0.2578 | 4 | 0 | 1 | 0 | 0 |
| q_lambda_2 | 0.0000 | calmar | -0.1183 | -0.1999 | 0.2022 | -0.2185 | 0.2430 | 5 | 0 | 0 | 0 | 0 |
| q_lambda_2 | 0.0000 | total_fees | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 5 | 0 | 0 | 0 | 0 |
| q_lambda_2 | 0.0000 | trade_count | 2.2000 | 2.0000 | 0.4472 | 2.0000 | 3.0000 | 5 | 0 | 0 | 0 | 0 |
| q_lambda_2 | 0.0000 | active_intervals | 2.8000 | 3.0000 | 0.8367 | 2.0000 | 4.0000 | 5 | 0 | 0 | 0 | 0 |
| q_lambda_2 | 10.0000 | net_return | -0.0092 | -0.0103 | 0.0107 | -0.0206 | 0.0078 | 5 | 0 | 0 | 0 | 0 |
| q_lambda_2 | 10.0000 | sharpe | -0.4078 | -0.4792 | 0.3220 | -0.6180 | 0.1547 | 5 | 0 | 0 | 0 | 0 |
| q_lambda_2 | 10.0000 | max_drawdown | 0.0159 | 0.0171 | 0.0056 | 0.0090 | 0.0234 | 5 | 0 | 0 | 0 | 0 |
| q_lambda_2 | 10.0000 | cagr | -0.0025 | -0.0028 | 0.0029 | -0.0055 | 0.0021 | 5 | 0 | 0 | 0 | 0 |
| q_lambda_2 | 10.0000 | profit_factor | 0.0555 | 0.0554 | 0.0641 | 0.0000 | 0.1110 | 4 | 0 | 1 | 0 | 0 |
| q_lambda_2 | 10.0000 | calmar | -0.1604 | -0.2262 | 0.1574 | -0.2365 | 0.1211 | 5 | 0 | 0 | 0 | 0 |
| q_lambda_2 | 10.0000 | total_fees | 359.1998 | 397.2293 | 168.0734 | 198.8913 | 601.5875 | 5 | 0 | 0 | 0 | 0 |
| q_lambda_2 | 10.0000 | trade_count | 2.2000 | 2.0000 | 0.4472 | 2.0000 | 3.0000 | 5 | 0 | 0 | 0 | 0 |
| q_lambda_2 | 10.0000 | active_intervals | 2.8000 | 3.0000 | 0.8367 | 2.0000 | 4.0000 | 5 | 0 | 0 | 0 | 0 |
| q_lambda_2 | 20.0000 | net_return | -0.0127 | -0.0123 | 0.0100 | -0.0245 | 0.0017 | 5 | 0 | 0 | 0 | 0 |
| q_lambda_2 | 20.0000 | sharpe | -0.4995 | -0.5703 | 0.3083 | -0.6990 | 0.0398 | 5 | 0 | 0 | 0 | 0 |
| q_lambda_2 | 20.0000 | max_drawdown | 0.0180 | 0.0190 | 0.0063 | 0.0105 | 0.0263 | 5 | 0 | 0 | 0 | 0 |
| q_lambda_2 | 20.0000 | cagr | -0.0034 | -0.0033 | 0.0027 | -0.0066 | 0.0005 | 5 | 0 | 0 | 0 | 0 |
| q_lambda_2 | 20.0000 | profit_factor | 1.3565 | 0.0000 | 3.0332 | 0.0000 | 6.7824 | 5 | 0 | 0 | 0 | 0 |
| q_lambda_2 | 20.0000 | calmar | -0.1928 | -0.2451 | 0.1215 | -0.2505 | 0.0245 | 5 | 0 | 0 | 0 | 0 |
| q_lambda_2 | 20.0000 | total_fees | 716.8861 | 792.8770 | 334.8539 | 397.3861 | 1,199.5727 | 5 | 0 | 0 | 0 | 0 |
| q_lambda_2 | 20.0000 | trade_count | 2.2000 | 2.0000 | 0.4472 | 2.0000 | 3.0000 | 5 | 0 | 0 | 0 | 0 |
| q_lambda_2 | 20.0000 | active_intervals | 2.8000 | 3.0000 | 0.8367 | 2.0000 | 4.0000 | 5 | 0 | 0 | 0 | 0 |

### Chênh lệch primary − reference cùng seed/cost

| seed | cost_bps | net_return_delta | sharpe_delta | max_drawdown_delta | total_fees_delta | trade_count_delta | active_intervals_delta |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 7 | 0.0000 | -0.2447 | -0.9085 | -0.3431 | 0.0000 | -227 | -769 |
| 7 | 10.0000 | 0.1118 | -0.5353 | -0.4473 | -40,250.3133 | -216 | -790 |
| 7 | 20.0000 | 0.3498 | -0.1881 | -0.5303 | -70,491.7956 | -216 | -786 |
| 21 | 0.0000 | 0.1058 | -0.4677 | -0.3759 | 0.0000 | -257 | -775 |
| 21 | 10.0000 | 0.2862 | -0.2676 | -0.4445 | -39,484.2902 | -239 | -778 |
| 21 | 20.0000 | 0.4900 | 0.0782 | -0.5491 | -68,154.7543 | -234 | -773 |
| 42 | 0.0000 | -0.7299 | -1.2583 | -0.1603 | 0.0000 | -251 | -714 |
| 42 | 10.0000 | 0.1666 | -0.2829 | -0.3478 | -45,555.9795 | -264 | -758 |
| 42 | 20.0000 | 0.3356 | -0.0386 | -0.4495 | -82,891.6393 | -263 | -762 |
| 84 | 0.0000 | -0.4249 | -0.9908 | -0.2463 | 0.0000 | -257 | -724 |
| 84 | 10.0000 | 0.2645 | -0.0822 | -0.4215 | -44,391.8429 | -247 | -699 |
| 84 | 20.0000 | 0.5581 | 0.5431 | -0.6353 | -68,114.5263 | -220 | -760 |
| 123 | 0.0000 | -0.0787 | 0.0524 | -0.4521 | 0.0000 | -268 | -772 |
| 123 | 10.0000 | 0.3071 | 0.5400 | -0.5035 | -44,274.5929 | -265 | -782 |
| 123 | 20.0000 | 0.5387 | 0.9774 | -0.6038 | -75,834.4535 | -264 | -790 |

Sensitivity giữ nguyên Q, nhưng actions có thể đổi vì phí làm equity/exposure/drawdown đi vào state khác. Flat target và exposure trước lệnh là hai đại lượng khác nhau. Nhãn no_trades/sparse_trades/mostly_flat/unseen_states_present/insolvent chỉ giúp diễn giải.

## 8. Theo năm và run kết thúc sớm

Một episode liên tục; returns compound theo năm của end_date, fees theo cùng intervals. Trades đóng trong năm không được dùng để tính calendar return. Coverage phản ánh ngày thực tế; không thêm returns giả cho run insolvent.

| Scenario | Year | Return | Fees | Active | Trades closed | Start | End | Partial |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| rl_q_lambda_0_seed_42_cost_10 | 2023 | 15.65% | 11,976.3496 | 185 | 55 | 2023-01-03 | 2023-12-29 | False |
| rl_q_lambda_0_seed_42_cost_10 | 2024 | -7.48% | 15,084.5405 | 205 | 89 | 2023-12-29 | 2024-12-31 | False |
| rl_q_lambda_0_seed_42_cost_10 | 2025 | -17.47% | 11,547.2276 | 208 | 78 | 2024-12-31 | 2025-12-31 | False |
| rl_q_lambda_0_seed_42_cost_10 | 2026 | -6.49% | 7,147.2957 | 162 | 44 | 2025-12-31 | 2026-10-02 | True |
| rl_q_lambda_2_seed_42_cost_10 | 2023 | 0.00% | 0.0000 | 0 | 0 | 2023-01-03 | 2023-12-29 | False |
| rl_q_lambda_2_seed_42_cost_10 | 2024 | 0.00% | 0.0000 | 0 | 0 | 2023-12-29 | 2024-12-31 | False |
| rl_q_lambda_2_seed_42_cost_10 | 2025 | 0.09% | 100.1451 | 1 | 1 | 2024-12-31 | 2025-12-31 | False |
| rl_q_lambda_2_seed_42_cost_10 | 2026 | -0.85% | 99.2889 | 1 | 1 | 2025-12-31 | 2026-10-02 | True |
| deterministic_cash_seed_42_cost_10 | 2023 | 0.00% | 0.0000 | 0 | 0 | 2023-01-03 | 2023-12-29 | False |
| deterministic_cash_seed_42_cost_10 | 2024 | 0.00% | 0.0000 | 0 | 0 | 2023-12-29 | 2024-12-31 | False |
| deterministic_cash_seed_42_cost_10 | 2025 | 0.00% | 0.0000 | 0 | 0 | 2024-12-31 | 2025-12-31 | False |
| deterministic_cash_seed_42_cost_10 | 2026 | 0.00% | 0.0000 | 0 | 0 | 2025-12-31 | 2026-10-02 | True |
| deterministic_buy_hold_seed_42_cost_10 | 2023 | 49.52% | 99.9001 | 249 | 0 | 2023-01-03 | 2023-12-29 | False |
| deterministic_buy_hold_seed_42_cost_10 | 2024 | 30.83% | 0.0000 | 252 | 0 | 2023-12-29 | 2024-12-31 | False |
| deterministic_buy_hold_seed_42_cost_10 | 2025 | 8.66% | 0.0000 | 250 | 0 | 2024-12-31 | 2025-12-31 | False |
| deterministic_buy_hold_seed_42_cost_10 | 2026 | 22.26% | 260.1087 | 189 | 1 | 2025-12-31 | 2026-10-02 | True |
| deterministic_fixed_long_50_seed_42_cost_10 | 2023 | 22.87% | 119.9948 | 249 | 0 | 2023-01-03 | 2023-12-29 | False |
| deterministic_fixed_long_50_seed_42_cost_10 | 2024 | 15.21% | 87.0886 | 252 | 0 | 2023-12-29 | 2024-12-31 | False |
| deterministic_fixed_long_50_seed_42_cost_10 | 2025 | 5.65% | 112.3270 | 250 | 0 | 2024-12-31 | 2025-12-31 | False |
| deterministic_fixed_long_50_seed_42_cost_10 | 2026 | 11.29% | 177.3177 | 189 | 1 | 2025-12-31 | 2026-10-02 | True |
| deterministic_fixed_short_50_seed_42_cost_10 | 2023 | -19.77% | 211.1306 | 249 | 0 | 2023-01-03 | 2023-12-29 | False |
| deterministic_fixed_short_50_seed_42_cost_10 | 2024 | -14.80% | 159.1742 | 252 | 0 | 2023-12-29 | 2024-12-31 | False |
| deterministic_fixed_short_50_seed_42_cost_10 | 2025 | -8.35% | 179.1152 | 250 | 0 | 2024-12-31 | 2025-12-31 | False |
| deterministic_fixed_short_50_seed_42_cost_10 | 2026 | -11.71% | 137.5457 | 189 | 1 | 2025-12-31 | 2026-10-02 | True |
| deterministic_sma20_long_flat_seed_42_cost_10 | 2023 | 41.40% | 1,892.1838 | 179 | 8 | 2023-01-03 | 2023-12-29 | False |
| deterministic_sma20_long_flat_seed_42_cost_10 | 2024 | 18.15% | 3,193.0122 | 147 | 11 | 2023-12-29 | 2024-12-31 | False |
| deterministic_sma20_long_flat_seed_42_cost_10 | 2025 | -11.81% | 3,605.2067 | 142 | 13 | 2024-12-31 | 2025-12-31 | False |
| deterministic_sma20_long_flat_seed_42_cost_10 | 2026 | 22.58% | 2,597.4489 | 107 | 8 | 2025-12-31 | 2026-10-02 | True |
| random_random_discrete_seed_42_cost_10 | 2023 | -10.10% | 19,426.3927 | 190 | 126 | 2023-01-03 | 2023-12-29 | False |
| random_random_discrete_seed_42_cost_10 | 2024 | 34.00% | 23,749.7620 | 201 | 123 | 2023-12-29 | 2024-12-31 | False |
| random_random_discrete_seed_42_cost_10 | 2025 | 37.80% | 30,127.2361 | 197 | 115 | 2024-12-31 | 2025-12-31 | False |
| random_random_discrete_seed_42_cost_10 | 2026 | -14.90% | 22,833.4764 | 152 | 86 | 2025-12-31 | 2026-10-02 | True |

Run insolvent: 0/60.

## 9. Kết luận, hạn chế và bài học

Primary λ=2, seed 42, 10 bps: return -0.76%, Sharpe -0.4790, MDD 0.90%, 2 trades, active 0.21% intervals. Reference return -17.42%. Flags primary: sparse_trades, mostly_flat, unseen_states_present. Kết quả này phải được đọc cùng mức hoạt động; ít giao dịch chưa đủ bằng chứng về chất lượng dự báo. Không yêu cầu RL thắng baseline để hoàn thành prototype.

Một tài sản, một chuỗi lịch sử, state discretization thô, chế độ thị trường thay đổi và thiếu financing/slippage thực tế giới hạn khả năng suy luận. Chọn λ bằng validation vẫn tạo selection bias; test chỉ được dùng đánh giá protocol đã chốt. Fresh Yahoo download có thể đổi adjustments, nên không thay thế snapshot đã khóa.

## 10. Tái tạo, artifacts và backlog

```bash
uv sync --python 3.11.16 --frozen --extra dev --extra charts
uv run pytest -q
uv run indexpilot-evaluate prepare --data data/raw/aapl_daily_2015-01-01_to_2026-10-06_processed.parquet --source-run outputs/stage-3/aapl-default --config configs/stage-4.toml --output-dir outputs/stage-4/aapl-frozen
uv run indexpilot-evaluate run --protocol-dir outputs/stage-4/aapl-frozen
uv run indexpilot-evaluate verify --protocol-dir outputs/stage-4/aapl-frozen
uv run indexpilot-evaluate report --protocol-dir outputs/stage-4/aapl-frozen
uv run indexpilot-chart --run-dir outputs/stage-4/aapl-frozen --save-png outputs/stage-4/aapl-frozen/figures/primary.png
uv run indexpilot-chart --run-dir outputs/stage-4/aapl-frozen --seeds --risk-lambda 2 --cost-bps 10
```

Chuẩn bị mới cần source Stage 3 và exact snapshot; thư mục output phải mới. Sau một test hoàn tất, chuẩn bị protocol mới cần --reason; không coi đây là quyền chọn lại theo test. Để tái lập experiment đã khóa, restore protocol/frozen_models/preparation/runs và dùng verify; --data cho phép đổi đường dẫn snapshot nhưng phải khớp SHA256. Thiếu snapshot thì báo thiếu input.

Artifacts gồm primary/scenario/seed/paired/yearly tables, diagnostics, protocol, ledger và từng run với equity/ledger/orders/trades/intervals/decisions/transitions. Report/chart chỉ đọc artifacts. GUI tùy chọn; PNG hỗ trợ QT_QPA_PLATFORM=offscreen. Data/models/detailed outputs nằm ngoài Git, cần lưu trữ riêng. Backlog: historical US100 universe tránh survivorship bias, multi-asset allocation, walk-forward, PPO, borrow/margin/slippage, state representation và data-provider archival.
