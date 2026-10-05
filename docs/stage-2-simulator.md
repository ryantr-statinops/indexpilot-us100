# Stage 2 — Simulator và baseline walkthrough

## Chạy dự án

Từ thư mục repository:

```bash
uv sync --extra dev
uv run pytest -q
uv run indexpilot-simulate \
  --data data/raw/aapl_daily_2015-01-01_to_2026-10-06_processed.parquet \
  --config configs/stage-2.toml \
  --output-dir outputs/stage-2/aapl-default
```

Nếu output đã tồn tại, chọn thư mục mới hoặc thêm `--overwrite`. Chỉ thư mục có manifest Stage 2 được ghi đè. Dữ liệu và outputs nằm ngoài Git; máy khác cần chạy workflow Stage 1 trước. Không cần mạng để mô phỏng một snapshot đã có.

Mở biểu đồ desktop:

```bash
uv sync --extra dev --extra charts
uv run indexpilot-chart --run-dir outputs/stage-2/aapl-default
```

Hai panel hiển thị equity USD và drawdown %. Đường random nét đứt. Chart đọc kết quả đã lưu, không chạy lại chiến lược. Khi không có display/extra charts, dùng summary và Parquet; core không import FinPlot.

## Simulator đang mô phỏng gì?

Một tài sản, đơn vị lẻ tổng hợp, giá `adj_open = open * adj_close / close`. Đây là chuỗi kế toán total return điều chỉnh; đơn vị không tương ứng cổ phiếu broker thực. Không cộng dividend/split thêm lần nữa.

- Equity: `cash + holdings * price`.
- Long có holdings dương, short có holdings âm.
- Cash mặc định không có lãi. Short chưa có phí vay, margin call hay financing.
- `TargetExposure(a)` đưa notional về tỷ trọng `a` trên equity **sau phí**.
- `HoldPosition()` giữ nguyên units. Exposure có thể trôi theo giá.
- Target hợp lệ nằm trong `[-1, 1]`; không tự clip. Giới hạn áp dụng lúc giao dịch, không tự ép giảm short giữa các phiên.
- Chi phí 10 bps mặc định là giả định all-in đơn giản trên actual traded notional; chưa tách spread/slippage.

Với equity trước lệnh `E`, notional hiện tại `v`, phí tỷ lệ `k`, target `a`, giải:

```text
x = a * (E - k * abs(x - v))
s = +1 nếu a*E >= v, ngược lại -1
x = a * (E + k*s*v) / (1 + a*k*s)
fee = k * abs(x-v)
delta_units = (x-v) / price
cash_after = cash_before - delta_units*price - fee
```

Nếu không đủ equity cho target sau phí do short drift lớn, đóng toàn bộ và kết thúc mất khả năng thanh toán. Vốn âm được giữ lại để thấy khoản nợ, không sửa thành 0.

### Ví dụ tính tay

Từ $100.000 cash, giá $100, target +1, phí 10 bps:

| Đại lượng | Giá trị |
|---|---:|
| Notional mua | $99.900,099900 |
| Phí mở | $99,900100 |
| Holdings | 999,000999 units |
| Cash sau mở | xấp xỉ $0 |
| Exposure sau phí | 100% |
| Equity ở giá $110, trước đóng | $109.890,109890 |
| Phí đóng | $109,890110 |
| Equity cuối | $109.780,219780 |
| Trade P&L ròng | $9.780,219780 |

Ledger ghi từng mốc này; phí và risk penalty không bị trừ lẫn nhau.

## Thời gian, observation và reward

Bước đi từ open hiện tại sang open tiếp theo:

1. Mark tài khoản tại open hiện tại.
2. Tạo features từ lịch sử trước phiên quyết định.
3. Policy chọn target/hold.
4. Giao dịch và trả phí.
5. Giữ units sang open tiếp theo, ghi P&L.
6. Nếu là open cuối hoặc equity không dương, liquidation và trả phí đóng.

Market features: adjusted-close returns 1/5/20 phiên, prior close, SMA20 và độ lệch chuẩn open-to-open theo risk window. Portfolio observation: cash, units, equity, exposure và drawdown tại quote hiện tại. Quote này được dùng để định giá tài khoản; next quote không nằm trong observation.

Open return của dòng `i` là `open[i]/open[i-1]-1`. P&L cho action ở dòng `i` phải dùng `open[i+1]-open[i]`. Volatility ở dòng `i` loại return kết thúc tại open `i`, chỉ dùng các returns kết thúc đến open `i-1`.

Warm-up yêu cầu `max(20, risk_window)+1` dòng trước index quyết định đầu. Với window20, index đầu là21 và cần ít nhất23 rows để có một interval. Các phiên warm-up không tính vào thời gian đánh giá.

```text
gross_return = units_after * (next_price-price) / equity_before
cost_fraction = (execution_fee + terminal_fee_if_any) / equity_before
risk = abs(units_after*price/equity_before) * historical_sample_volatility
reward = gross_return - risk_lambda*risk - cost_fraction
net_return = equity_end/equity_before - 1
```

Lambda0 cho `reward = net_return` trong sai số số học. Lambda chỉ thay đổi reward đối với cùng actions, không thay đổi equity. Phí đóng cuối nằm trong interval cuối; không thêm ngày giả. Vốn không dương kết thúc ngay sau liquidation; không đặt target tiếp.

## Baselines

| Policy | Quy tắc |
|---|---|
| cash | Luôn target0 |
| buy_hold | Target+1 lần đầu, sau đó hold units |
| fixed_long_50 | Target+0,5 mỗi phiên |
| fixed_short_50 | Target−0,5 mỗi phiên |
| sma20_long_flat | Prior adjusted close > prior SMA20 thì target+1, ngược lại0 |
| random_discrete | NumPy RNG, seed42, actions −1/−0,5/0/0,5/1 |

SMA20 đã được chọn trước; không tối ưu theo kết quả. Random phục vụ sanity check. Policy reset trước mỗi episode để tránh mang trạng thái run trước sang run sau.

## Năm metrics

| Metric | Định nghĩa |
|---|---|
| Sharpe | Mean excess net interval return / sample std, nhân sqrt252; annual risk-free đổi sang per-session qua compounding |
| Maximum drawdown | Max của `1-equity/running_peak`, độ lớn dương; dùng **toàn bộ ledger**, kể cả mốc ngay sau phí |
| CAGR | `(final/initial) ** (365.25/calendar_days) - 1` |
| Profit Factor | Tổng net P&L trade thắng / abs tổng net P&L trade thua |
| Calmar | CAGR / maximum drawdown |

Equity Parquet là snapshot mỗi open sau interval; drawdown tại snapshot dùng peak của event ledger. Chart lấy các snapshot này. MDD summary dùng cả các mốc trong ledger, nên một đáy sau phí trước một phiên tăng có thể không hiện thành điểm riêng trên đường chart. Kiểm tra ledger để truy đúng event của MDD.

Một trade là một đợt cùng chiều từ mở đến flat/đảo chiều. Scale-in/out không tạo trade mới. Reversal chia phí theo notional đóng/mở. Tất cả phí cùng chiều thuộc trade đang mở. Trade hòa vốn có tolerance $1e-8 để bỏ nhiễu số thực; không sửa P&L tài khoản.

- Sharpe: thiếu2 returns hoặc std <=1e-14 → undefined.
- CAGR: vốn cuối không dương hoặc thời gian không dương → undefined.
- Profit Factor: không trade/toàn hòa → undefined; chỉ thắng → positive infinity; chỉ thua →0.
- Calmar: DD0 với CAGR dương → positive infinity; CAGR0/DD0 → undefined.
- Run insolvent: Sharpe/CAGR/Calmar → not applicable. MDD có thể lớn hơn100%.
- JSON dùng `null` và cột `<metric>_status`, không chứa NaN/Infinity. Terminal hiển thị N/A/∞.
- Normalized turnover cộng `traded_notional/equity_before` ở các lệnh có equity_before dương; lệnh đóng khi đã insolvent không có mẫu số dương nên không đưa vào tổng này. Tổng notional và tổng fees vẫn bao gồm mọi lệnh.

## Đọc outputs

```text
summary.csv / summary.json     # metrics, phí, số trades, seed, status
run_manifest.json             # hash input, config thực tế, version, Git revision
<baseline>/
  equity.parquet              # snapshots theo phiên, reward và drawdown
  ledger.parquet              # initial / execution / hold / mark / liquidation
  orders.parquet              # chỉ lệnh có actual traded notional
  trades.parquet              # các đợt vị thế đã đóng, P&L sau phí
  intervals.parquet           # gross return, risk, costs, reward, net return
```

Ví dụ đọc vài lệnh:

```python
import polars as pl
orders = pl.read_parquet('outputs/stage-2/aapl-default/buy_hold/orders.parquet')
print(orders)
```

Cash có bảng orders/trades rỗng nhưng giữ schema. Manifest ghi coverage/gap diagnostics; chưa dùng exchange calendar để xác nhận đủ mọi phiên sàn. Run có insolvency kết thúc sớm nên end date và interval count sẽ khác các baseline còn sống.

## Kiểm chứng

`uv run pytest -q` hiện có103 test độc lập Yahoo/network, bao gồm:

- Bài toán giá/fees tính tay, long/short/flat, reversal, hold và drift.
- Equity=cash+holdings×price ở mọi event; tổng trade P&L khớp tài khoản sau đóng.
- Warm-up, no look-ahead, đổi tương lai giữ nguyên prefix.
- Reward không trừ phí hai lần; lambda không đổi kế toán.
- Insolvency do biến động giá hoặc không đủ trả closing fee.
- Metrics finite/undefined/infinite; schema rỗng; export/import; CLI lỗi rõ ràng.
- Cùng seed/config có artifact số liệu giống byte-for-byte; chart optional.

Desktop FinPlot đã mở và render thành công hai panel, sáu baseline. Snapshot preview nằm local trong run directory.

## Kết quả AAPL đã kiểm tra

Snapshot hash: `042605225d9f9dc91ac983ceb13079f09077a569bd485dd06774263f994db3cc`. Run dùng code commit `951d706`, phí10bps, seed42, lambda0.

Đánh giá từ **2015-02-03 đến 2026-10-02**, sau warm-up. Vốn ban đầu $100.000. Đây là mô phỏng toàn mẫu để học và kiểm tra kế toán, chưa phải kết quả RL ngoài mẫu.

| Baseline | Equity cuối USD | Sharpe | MDD | CAGR | PF | Calmar | Phí USD | Trades |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| cash | 100,000.00 | N/A | 0.00% | 0.00% | N/A | N/A | 0.00 | 0 |
| buy_hold | 1,269,484.47 | 0.885 | 37.39% | 24.35% | ∞ | 0.651 | 1,370.66 | 1 |
| fixed_long_50 | 401,271.80 | 0.879 | 20.45% | 12.66% | ∞ | 0.619 | 2,271.84 | 1 |
| fixed_short_50 | 18,522.01 | -0.902 | 83.12% | -13.46% | 0.000 | -0.162 | 1,496.32 | 1 |
| sma20_long_flat | 1,083,047.77 | 1.144 | 27.12% | 22.67% | 2.160 | 0.836 | 118,739.60 | 124 |
| random_discrete | 7,171.94 | -0.979 | 94.36% | -20.23% | 0.786 | -0.214 | 108,656.77 | 1383 |

### Độ nhạy với phí

| Baseline | Equity phí0bps | Equity phí10bps | Equity phí20bps |
|---|---:|---:|---:|
| cash | 100,000.00 | 100,000.00 | 100,000.00 |
| buy_hold | 1,272,025.98 | 1,269,484.47 | 1,266,948.03 |
| fixed_long_50 | 405,480.68 | 401,271.80 | 397,106.31 |
| fixed_short_50 | 19,073.62 | 18,522.01 | 17,986.30 |
| sma20_long_flat | 1,387,882.44 | 1,083,047.77 | 845,166.61 |
| random_discrete | 74,774.88 | 7,171.94 | 687.88 |

- Buy-and-hold chỉ có hai lệnh, nên tổng phí nhỏ hơn các baseline giao dịch nhiều.
- Fixed long50 giữ ít exposure hơn và tái cân bằng mỗi phiên; equity và drawdown khác buy-and-hold.
- Short mất vốn trên mẫu này, phù hợp với hướng tăng dài hạn của AAPL trong snapshot.
- Random giao dịch nhiều; tác động của phí và compounding rất lớn. Không nên chỉ nhìn tổng phí USD mà bỏ qua phần vốn bị mất và lợi nhuận lẽ ra có thể tái đầu tư.
- PF vô hạn của long liên tục đến cuối chỉ có nghĩa một trade đóng có lời, không chứng minh chiến lược ít rủi ro.

Đã audit cả ba cấu hình: fees và trade P&L đối soát; cash không có lệnh; buy-and-hold có đúng hai lệnh; terminal fee nằm trong interval cuối. Run10bps lặp lại có summary và các bảng đã so sánh giống nhau. Timestamp manifest khác là metadata của mỗi lần chạy.

Để tái tạo sensitivity: copy TOML, đổi `cost_bps` thành0/20, chạy CLI với output directory riêng. Không chọn policy hoặc tham số bằng kết quả toàn mẫu này; protocol ngoài mẫu thuộc Stage4.
