# Stage 4 — frozen test và tái lập

## Quy trình cố định

Đọc [protocol](stage-4-protocol.md) trước khi chạy. Model chính vẫn là checkpoint Stage 3 lambda 2/seed 42; reference lambda 0/seed 42. Bốn seed mới chỉ train trên dữ liệu đến hết 2020. Validation 2021–2022 đã dùng chọn lambda; test từ 2023 không chọn lại model.

```bash
uv sync --python 3.11.16 --frozen --extra dev --extra charts
uv run pytest -q
uv run indexpilot-evaluate prepare --data data/raw/aapl_daily_2015-01-01_to_2026-10-06_processed.parquet --source-run outputs/stage-3/aapl-default --config configs/stage-4.toml --output-dir outputs/stage-4/aapl-frozen
uv run indexpilot-evaluate run --protocol-dir outputs/stage-4/aapl-frozen
uv run indexpilot-evaluate verify --protocol-dir outputs/stage-4/aapl-frozen
uv run indexpilot-evaluate report --protocol-dir outputs/stage-4/aapl-frozen
```

`prepare` chưa đánh giá test; nó xác minh source selection, data SHA256, metadata state/actions rồi copy hai model seed 42, train tám model bổ sung và khóa protocol. Hash config là cấu hình thực tế trong protocol, không phụ thuộc thay đổi file TOML sau đó. End date phải nằm trong snapshot; ngày bắt đầu được chuyển sang phiên đầu có date ≥ boundary. Warm-up có `max(20, risk_window)+1` phiên trước, không tính vào equity/metrics.

`run` xác minh protocol/data/model/log/code/uv.lock/runtime rồi mới tạo outcomes test. Q/visits chỉ đọc và epsilon 0. Mỗi scenario reset flat; engine accounting, terminal fee, insolvency và metrics giữ nguyên Stage 2. 60 scenarios gồm 30 RL, 15 baseline xác định và 15 random. Kết quả chính luôn seed 42/10 bps, tám dòng; random chỉ là sanity check.

Nếu run bị gián đoạn, chạy lại cùng lệnh: scenario hoàn tất được kiểm tra hash trước khi tái dùng. Nếu run đã hoàn tất, lệnh chỉ trả artifacts đã kiểm tra. File bị sửa hoặc input/code không khớp sẽ báo lỗi, không tự xóa hay đánh giá lại.

`verify` thực sự tính lại 60 scenarios trong thư mục `verification-*` riêng. Nó so sánh decisions, transitions, tables Parquet, metrics và diagnostics. Timestamp/Git provenance của exporter không thuộc so sánh số liệu; các file provenance vẫn có hash trong từng completion marker. Không dùng verify để chọn tham số.

Protocol mới sau một run hoàn tất cần `prepare --reason "lý do cụ thể"` và output directory mới. Lịch sử tại `outputs/stage-4/experiment-ledger.jsonl` append-only, có hash chain và process lock. Lý do phải giải thích việc tạo experiment mới, không biến test thành validation.

## Artifacts và cách đọc

| File | Nội dung |
|---|---|
| protocol.json | Config, boundaries, 10 model hashes, data/source hashes, state/action definitions, code fingerprints, lock/runtime, protocol ID |
| frozen_models/ | Checkpoints cố định; không train trong run/verify |
| preparation/ | Training CSV theo seed/lambda, source manifest và selection |
| primary_summary.csv/json | Hai RL + sáu baselines seed 42/10 bps |
| scenario_summary.csv/json | Đầy đủ 60 scenarios và intended/actual coverage/status |
| seed_summary.csv/json | Mean/median/sample std/min/max của finite values, số undefined/infinite/N/A/insolvent |
| paired_comparison.csv/json | Lambda 2 − lambda 0 cùng seed và mức phí |
| yearly_summary.csv/json | Returns compound, fees, actions, active intervals, trades đóng theo năm |
| diagnostics.json | Activity/exposure, unseen states, reward breakdown, trade duration, drawdown events và nhãn |
| runs/scenario/ | Accounting exports, decisions, RL transitions nếu có, score/diagnostics và completion hashes |
| run_manifest.json | Intended coverage, mọi actual status/coverage và hashes bảng tổng hợp |
| report.md | Báo cáo sinh từ artifacts đã kiểm tra |

Metric null phải đọc cùng metric_status: undefined, positive_infinity, not_applicable. CLI dùng bảng Polars nên null có thể hiển thị null; report hiển thị N/A/∞. Không thay infinite bằng số lớn trong aggregate. Seed variability chỉ đo sự khác biệt học trên cùng lịch sử.

Flat decisions là target 0, còn active interval là holdings **sau** quyết định khác 0. Exposure trước lệnh khác hai đại lượng này. Gross exposure dùng abs(units_after × execution_price / equity_before). HoldPosition được thống kê riêng, không bị coi là target 0.

mostly_flat dùng ngưỡng 95%; sparse_trades là 1–4 closed trades; no_trades, unseen_states_present và insolvent được giữ bên cạnh metric. Reward breakdown gồm tổng gross-return fractions, cost fractions và lambda × risk; đó là tổng theo interval, không phải cumulative compounded P&L.

Một episode test liên tục đi qua năm mới. Return/fee theo năm dùng end_date của interval, kể cả phí liquidation cuối; không lấy P&L trade đóng thay calendar return. Năm 2026 kết thúc 02/10 nên là năm chưa đủ. Insolvent giữ debt/equity âm và coverage kết thúc sớm, không thêm returns giả.

## Biểu đồ

```bash
uv run indexpilot-chart --run-dir outputs/stage-4/aapl-frozen
uv run indexpilot-chart --run-dir outputs/stage-4/aapl-frozen --cost-bps 20
uv run indexpilot-chart --run-dir outputs/stage-4/aapl-frozen --seeds --risk-lambda 2 --cost-bps 10
uv run indexpilot-chart --run-dir outputs/stage-4/aapl-frozen --save-png outputs/stage-4/aapl-frozen/figures/primary.png
QT_QPA_PLATFORM=offscreen uv run indexpilot-chart --run-dir outputs/stage-4/aapl-frozen --seeds --risk-lambda 0 --save-png outputs/stage-4/aapl-frozen/figures/reference-seeds.png
```

Hai panel equity và drawdown. Chart dùng mốc daily equity lưu sẵn; MDD trong bảng dùng toàn bộ accounting events, nên trough ngay sau phí có thể không hiện thành mốc riêng trên chart. Diagnostics giữ peak/trough/recovery theo event và maximum underwater calendar days. Drawdown diagnostics mô tả sự kiện MDD sâu nhất và thời gian underwater dài nhất, không liệt kê mọi đợt drawdown.

Report/core evaluator chạy không cần desktop/FinPlot. GUI và PNG cần extra charts. PNG render bằng Qt, có offscreen smoke test. Xem riêng các seed giúp phát hiện policy gần như flat; không gộp equity các seed thành portfolio mới.

## Tái lập từ checkout sạch

Git không chứa snapshot/checkpoints/detailed outputs. Cần archive riêng:

- Exact Parquet có SHA256 đã khóa.
- outputs/stage-3/aapl-default/ nếu cần chuẩn bị lại từ source.
- outputs/stage-4/aapl-frozen/ và experiment ledger để replay experiment đã khóa.
- Commit code và uv.lock ghi trong protocol.

```bash
git clone https://github.com/ryantr-statinops/indexpilot-us100.git
cd indexpilot-us100
# Checkout code revision trong protocol hoặc revision sau đó chỉ thay tài liệu.
uv sync --python 3.11.16 --frozen --extra dev --extra charts
# Restore archived protocol/models/preparation/results vào outputs/stage-4/aapl-frozen.
uv run indexpilot-evaluate verify --protocol-dir outputs/stage-4/aapl-frozen --data /absolute/path/to/archived_snapshot.parquet
uv run indexpilot-evaluate report --protocol-dir outputs/stage-4/aapl-frozen
```

Fresh download Yahoo có thể khác historical adjustment; thiếu snapshot thì không thay bằng download mới và gọi là cùng experiment. Chuẩn bị lại từ training có thể tái tạo arrays/model nhưng tạo protocol ID mới vì thời gian chuẩn bị khác; replay experiment cũ dùng inventory đã archive.

Code fingerprint bao gồm modules Python của package; thay logic hoặc lock bị phát hiện. Thay tài liệu không đổi fingerprint. Runtime core kiểm tra Python version và package versions; GUI/platform được lưu provenance nhưng không bắt buộc giống để core replay. Hoàn thành dự án xác nhận protocol/kế toán/tái lập, không khẳng định lợi nhuận live hay RL vượt baseline.

## Kết quả AAPL đã kiểm chứng

Protocol đã khóa trước khi mở test:

- ID: `5fbce9eb3c97815487c57b7eaca4502390562e37ed062609d72c87ba189ec18b`.
- Code: `b6c550d`; dataset SHA256: `042605225d9f9dc91ac983ceb13079f09077a569bd485dd06774263f994db3cc`.
- Test thực tế: **2023-01-03 → 2026-10-02**, 940 intervals; 2026 chưa đủ năm.
- 10 models, 60/60 scenarios completed; không có run insolvent trên snapshot này.
- Hyperparameters: 100 episodes/model, alpha 0,1, gamma 0,99, epsilon max(0,05; 1 × 0,97^episode_index). Learning config gốc vẫn ghi grid Stage 3 [0;0,5;1;2], nhưng Stage 4 chỉ chuẩn bị các lambda cố định 0 và 2.

[Báo cáo đầy đủ](REPORT.md) chứa năm metrics, phí/turnover/orders/trades, coverage, toàn bộ RL seeds/costs, seed statistics và calendar returns.

### Diễn giải kết quả chính

| Policy | Equity cuối | Net return | Sharpe | MDD | Trades | Active intervals |
|---|---:|---:|---:|---:|---:|---:|
| RL lambda 2 | $99.239,61 | −0,76% | −0,479 | 0,90% | 2 | 2/940 |
| RL lambda 0 | $82.583,96 | −17,42% | −0,196 | 35,69% | 266 | 760/940 |
| Cash | $100.000,00 | 0,00% | N/A | 0,00% | 0 | 0/940 |
| Buy-and-hold | $259.848,56 | +159,85% | 1,074 | 33,33% | 1 | 940/940 |

Lambda 2 gần như không giao dịch: 938/940 target flat, tương đương 99,79%. Hai trade đều target long 50% và chỉ giữ một interval:

| Mở → đóng | Net P&L |
|---|---:|
| 2025-01-03 → 2025-01-06 | +$94,94 |
| 2026-02-13 → 2026-02-17 | −$855,33 |

Tổng phí $199,43; equity cuối thấp hơn cash. MDD nhỏ đi kèm exposure rất thấp nên không chứng minh khả năng dự báo tốt. 2,55% states chưa được gặp khi training; phần lớn quyết định flat vẫn ở states đã gặp. Volatility penalty mạnh đã khuyến khích tránh giữ vị thế.

Lambda 0 hoạt động nhiều hơn và trả $45.755,41 phí. Cả năm seed lambda 0 đều lỗ ở 10 bps: mean return −23,64%, sample std 7,77 điểm phần trăm, range −29,94% đến −13,24%. Lambda 2 mean −0,92%, std 1,07 điểm phần trăm, range −2,06% đến +0,78%. Không đổi primary sang seed có kết quả dương.

Random seed 42 đạt +41,28%, nhưng mean năm seed là −22,46%, std 38,92 điểm phần trăm. Đây là ví dụ vì sao một seed thuận lợi không đủ kết luận chất lượng policy. Random vẫn là sanity check, không phải benchmark chất lượng đầu tư.

### Audit và tái lập đã thực hiện

- 175 tests pass ở repo chính và checkout mới, gồm 129 tests Stage 1–3.
- Fixture chạy đủ matrix 60 scenarios; resume sau lỗi chỉ tính scenarios chưa xong.
- AAPL audit 60 terminal events: equity = cash + holdings × price; sum trade P&L khớp account P&L, sai số lớn nhất khoảng 6,26 × 10^-10 USD.
- Cash đúng tuyệt đối ở cả ba mức phí; buy-and-hold chỉ có hai orders.
- Yearly returns compound về total net return; yearly fees cộng về tổng phí.
- Hai model seed 42 byte-identical với checkpoints Stage 3.
- Audit đủ 30 RL scenarios: Q/visits sau rollout bằng arrays load trước, và arrays chỉ đọc.
- Verify tính lại 60 scenarios trong thư mục riêng; decisions, transitions, accounting, metrics, diagnostics và summary files khớp.
- Checkout mới có venv riêng, Python 3.11.16 và frozen lock; restore artifacts và đổi đường dẫn snapshot vẫn verify 60/60.
- Report sinh trong checkout mới giống byte-for-byte với report được commit.
- FinPlot đã mở trên desktop và xuất primary PNG; seed views và chart trong checkout mới render offscreen. Đã đối chiếu axes/legend với tables.

Các bằng chứng local nằm trong `audit.json`, `verification-*/verification.json`, experiment ledger và `figures/`. File detailed và checkpoints vẫn ngoài Git.

Archive phục vụ tái lập: `outputs/stage-4/aapl-reproduction.tar.gz`, kèm `reproduction_archive_manifest.json` chứa hash archive. Archive gồm exact snapshot, source Stage 3, frozen protocol/models/results, ledger, config và lock. Chỉ dùng bản local phù hợp quyền sử dụng dữ liệu; repo không chứa market data.
