# 04 — Simulator, baselines và metrics

## Mục lục

- [Tài khoản và vị thế](#tài-khoản-và-vị-thế)
- [Giao dịch và phí](#giao-dịch-và-phí)
- [Một interval diễn ra thế nào](#một-interval-diễn-ra-thế-nào)
- [Reward và risk](#reward-và-risk)
- [Sáu baselines](#sáu-baselines)
- [Trade và năm metrics](#trade-và-năm-metrics)
- [Đọc ledger và outputs](#đọc-ledger-và-outputs)

## Tài khoản và vị thế

Simulator dùng [synthetic adjusted open](03-data.md#giá-điều-chỉnh-và-returns). Với q là holdings, C là cash và P là giá:

```text
position_value = q * P
equity = C + q * P
exposure = q * P / equity         # chỉ khi equity > 0
```

q dương là long, q âm là short. Float64 và đơn vị lẻ được dùng; chưa có lot rounding, cash interest, financing, borrow fee hoặc margin call.

Short sale làm cash tăng nhưng không tự sinh lợi nhuận. Ví dụ không phí: vốn $10.000, short 100 units tại $100 tạo cash $20.000 và vị thế −$10.000; equity vẫn $10.000. Giá lên $110 làm equity $9.000, exposure khoảng −122,22%.

Hai chỉ thị có ý nghĩa khác nhau:

| Chỉ thị | Hành vi |
|---|---|
| TargetExposure(+0.5) | Đưa signed position value về 50% equity sau phí |
| TargetExposure(0) | Đóng vị thế |
| HoldPosition() | Giữ nguyên số units, không tái cân bằng |

Target phải finite và nằm trong [−1,1]; giá trị sai bị từ chối, không tự clip. Exposure có thể trôi ngoài khoảng này khi giữ vị thế; không có margin intervention khi equity còn dương.

Ví dụ long 50% không phí: ban đầu cash $50.000 và 500 units ở $100. Giá lên $110 thì equity $105.000, exposure = $55.000/$105.000 ≈ 52,38%. Hold giữ 500 units; fixed exposure sẽ bán bớt để trở về 50%.

## Giao dịch và phí

Default config trong [stage-2.toml](../configs/stage-2.toml): vốn $100.000, phí 10 bps, lambda 0, risk window 20, annualization 252, risk-free 0, seed 42.

10 bps = 0,001 = 0,1% **notional thực sự giao dịch**. Không tính phí trên toàn vốn mỗi phiên; chưa tách spread/slippage.

Với E là equity trước lệnh, v = qP là position value hiện tại, a là target và k là cost rate:

```text
x = a * (E - k * abs(x-v))
s = +1 nếu a*E >= v, ngược lại -1
x = a * (E + k*s*v) / (1 + a*k*s)
delta_units = (x-v) / P
fee = k * abs(x-v)
q_after = x / P
cash_after = cash_before - delta_units*P - fee
equity_after = equity_before - fee
```

Như vậy target áp dụng trên equity **sau trả phí**, không phải mua a × vốn trước phí rồi chấp nhận sai tỷ trọng.

### Ví dụ tính tay

Từ $100.000 cash, P = $100, target +1, phí 10 bps; sau đó giá lên $110 và đóng:

| Đại lượng | Giá trị gần đúng |
|---|---:|
| Notional mua | $99.900,099900 |
| Phí mở | $99,900100 |
| Holdings | 999,000999 units |
| Cash sau mở | $0 |
| Exposure sau phí | 100% |
| Equity ở $110 trước đóng | $109.890,109890 |
| Phí đóng | $109,890110 |
| Equity cuối | $109.780,219780 |
| Net trade P&L | $9.780,219780 |

Nếu giá đứng yên, gross P&L bằng 0 nhưng equity vẫn giảm bởi phí mở và đóng.

## Một interval diễn ra thế nào

1. Mark cash/holdings tại open i.
2. Tạo observation: market features từ lịch sử trước i, account state tại current quote.
3. Policy chọn target hoặc hold.
4. Execute tại open i, trả phí, cập nhật cash và holdings.
5. Giữ holdings đến open i+1; ghi gross P&L.
6. Tính net return/reward, ghi events và interval.

Có đủ warm-up mới bắt đầu; mọi policy dùng cùng eligible interval schedule. Không đặt quyết định mới ở open cuối.

Kết thúc bình thường: liquidate ở open cuối, phí đóng được gộp vào interval cuối. Không thêm một ngày giả để ghi phí.

Nếu equity không dương, liquidate tại quote đã quan sát và terminate với status insolvent. Equity âm được giữ nguyên để thấy debt; không tiếp tục chia exposure cho vốn không dương. Trường hợp short drift khiến equity dương nhưng không đủ trả closing fee cũng được đóng và kết thúc; engine điều chỉnh interval trước đã đến quote đó thay vì thêm interval giả.

## Reward và risk

```text
gross_return = q_after * (next_price-price) / equity_before
cost_fraction = total_interval_fees / equity_before
risk = abs(q_after*price/equity_before) * historical_sample_volatility
reward = gross_return - lambda*risk - cost_fraction
net_return = equity_end/equity_before - 1
```

Risk dùng sample volatility của 20 open returns **đã có trước quyết định**. Nó là proxy theo interval, không phải volatility annualized của cả portfolio.

Equity thay đổi bởi gross P&L và phí; risk penalty chỉ ảnh hưởng reward. Không lấy net return rồi trừ phí lần nữa. Với lambda 0, reward bằng net interval return trong sai số số học; tổng reward vẫn không phải compounded return.

Ví dụ gross return 0,005; cost fraction 0,001; risk 0,01; lambda 2:

```text
net return = 0,005 - 0,001 = 0,004 = +0,4%
reward = 0,005 - 2*0,01 - 0,001 = -0,016
```

Account có lời trong interval nhưng reward âm. Mức penalty này có thể khiến agent ưu tiên flat.

## Sáu baselines

| Policy | Quy tắc |
|---|---|
| cash | Luôn target 0 |
| buy_hold | Target +1 đầu episode, sau đó HoldPosition |
| fixed_long_50 | Target +0,5 mỗi phiên |
| fixed_short_50 | Target −0,5 mỗi phiên |
| sma20_long_flat | Prior adjusted close > SMA20 trước quyết định thì +1; ngược lại 0 |
| random_discrete | RNG NumPy chọn −1/−0,5/0/+0,5/+1 |

SMA20 là quy tắc đã chọn trước, không tối ưu bằng test. Random là sanity check; reset RNG theo seed mỗi episode. Các policies dùng cùng execution engine và liquidation.

## Trade và năm metrics

Một **order** là một lệnh thực sự có traded notional. Một **trade** là một đợt vị thế cùng chiều, từ mở đến flat hoặc reversal. Scale-in/out cùng chiều vẫn thuộc trade đó; reversal đóng trade cũ và mở trade mới, phân bổ fees theo notional đóng/mở.

| Metric | Định nghĩa |
|---|---|
| Sharpe | Mean excess net interval return / sample std, ddof=1, nhân sqrt(252); annual risk-free chuyển sang per-session bằng compounding |
| Maximum drawdown | Max(1 − equity/running peak), báo độ lớn dương trên toàn event ledger |
| CAGR | (final equity / initial equity)^(365,25 / calendar days) − 1 |
| Profit Factor | Tổng net P&L trades thắng / abs tổng net P&L trades thua |
| Calmar | CAGR / maximum drawdown |

Phí mở, rebalance và đóng đều thuộc net trade P&L. Sau liquidation, tổng net trade P&L phải khớp equity cuối trừ vốn đầu. Wins/losses/breakeven dùng tolerance $10^-8 để bỏ nhiễu số thực; không sửa account P&L.

Các trường hợp đặc biệt:

- Sharpe thiếu hai returns hoặc std ≤ 10^-14: undefined.
- PF không trade hoặc toàn hòa vốn: undefined; chỉ thắng: +∞; chỉ thua: 0.
- Calmar có DD 0 và CAGR dương: +∞; CAGR 0/DD 0: undefined.
- Insolvent: Sharpe/CAGR/Calmar not applicable; MDD có thể vượt 100%.
- JSON lưu null và metric_status; không xuất NaN/Infinity số học không hợp lệ.

Normalized turnover cộng notional/equity_before cho các orders có equity_before dương. Lệnh closing khi vốn đã không dương vẫn nằm trong total notional/fees nhưng không có mẫu số hợp lệ cho normalized turnover.

## Đọc ledger và outputs

```text
summary.csv/json
run_manifest.json
<policy>/
    equity.parquet
    ledger.parquet
    orders.parquet
    trades.parquet
    intervals.parquet
```

Ledger có initial, execution/hold, mark và liquidation. Mỗi event thỏa equity = cash + holdings × price. Cash có orders/trades rỗng với schema vẫn đầy đủ.

Ví dụ đọc kết quả đã có, không chạy lại policy:

```python
import polars as pl

root = "outputs/stage-2/aapl-default/buy_hold"
print(pl.read_parquet(f"{root}/orders.parquet"))
print(pl.read_parquet(f"{root}/trades.parquet"))
```

MDD trong summary dùng toàn ledger, kể cả đáy ngay sau phí. FinPlot vẽ daily equity snapshots; một đáy sau execution trước khi giá hồi có thể không hiện thành điểm riêng trên chart.

**Đọc tiếp:** [README dự án](../README.md) dẫn tới chương Q-learning và evaluation.
