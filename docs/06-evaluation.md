# 06 — Frozen evaluation

## Mục lục

- [Vì sao phải khóa protocol](#vì-sao-phải-khóa-protocol)
- [Các quyết định cố định](#các-quyết-định-cố-định)
- [Prepare, run, verify và report](#prepare-run-verify-và-report)
- [Resume và tính toàn vẹn](#resume-và-tính-toàn-vẹn)
- [Diagnostics và tổng hợp](#diagnostics-và-tổng-hợp)
- [Artifacts và biểu đồ](#artifacts-và-biểu-đồ)

## Vì sao phải khóa protocol

Validation đã dùng chọn lambda. Nếu xem test rồi chọn seed, lambda hoặc mức phí cho kết quả đẹp nhất, test cũng trở thành dữ liệu lựa chọn.

Protocol ghi lựa chọn và inventory **trước lần đánh giá test đầu**. Thành công của experiment là đánh giá đúng cấu hình đã chốt, kể cả RL thua baseline. Tất cả policies dùng [cùng simulator và metrics](04-simulator.md).

## Các quyết định cố định

| Nội dung | Quyết định |
|---|---|
| Primary | Checkpoint lambda 2, seed 42 từ learning run |
| Reference | Checkpoint lambda 0, seed 42 |
| Training / validation | Giữ nguyên đoạn đến hết 2020 / 2021–2022 |
| Test khai báo | 2023-01-01 → 2026-10-02 |
| Test thực tế | 2023-01-03 → 2026-10-02, 940 intervals |
| Snapshot | Đúng SHA256 đã dùng khi training |
| Seeds | 42, 7, 21, 84, 123 |
| Cost scenarios | 0/10/20 bps; chính luôn 10 bps |
| Mỗi run | Reset flat/$100.000; greedy epsilon 0 |
| Model updates | Q/visits chỉ đọc, không training trong evaluation |

Hai model seed 42 được copy byte-for-byte, không train lại trên validation. Tám model bổ sung là bốn seeds × hai lambda; mỗi model train 100 episodes trên training cũ, cùng bins/settings. Không validate để chọn lại lambda cho từng seed.

Matrix:

| Nhóm | Số run |
|---|---:|
| RL: 5 seeds × 2 lambdas × 3 costs | 30 |
| Baseline xác định: 5 policies × 3 costs | 15 |
| Random: 5 seeds × 3 costs | 15 |
| Tổng | 60 |

Baseline xác định chạy một lần mỗi cost; không nhân bản thành năm independent samples. Baseline reward dùng lambda 2; finances giữ nguyên engine. Không dùng reward để so P&L giữa hai lambda.

Primary table gồm tám dòng: hai RL và sáu baselines, seed 42/10 bps. Other seeds mô tả variability, không thay primary.

## Prepare, run, verify và report

Các lệnh dưới đây dùng archived snapshot và source learning run đã có. Output prepare phải là thư mục mới:

```bash
uv run indexpilot-evaluate prepare --data data/raw/aapl_daily_2015-01-01_to_2026-10-06_processed.parquet --source-run outputs/stage-3/aapl-default --config configs/stage-4.toml --output-dir outputs/stage-4/aapl-frozen
uv run indexpilot-evaluate run --protocol-dir outputs/stage-4/aapl-frozen
uv run indexpilot-evaluate verify --protocol-dir outputs/stage-4/aapl-frozen
uv run indexpilot-evaluate report --protocol-dir outputs/stage-4/aapl-frozen
```

| Command | Công việc |
|---|---|
| prepare | Validate source manifest/selection/state metadata/data hash; chuẩn bị 10 models; lưu protocol ID và hashes |
| run | Recheck frozen inputs/runtime, slice causal test, evaluate 60 scenarios và export |
| verify | Tính lại trong verification directory riêng; đối chiếu số liệu/decisions/artifacts |
| report | Đọc artifacts đã kiểm tra, sinh report.md; không evaluate hoặc train |

Prepare khóa expected data hash từ source đã validate, kiểm tra trước/sau load và trước publication. Source manifest, selection, primary checkpoints và training logs cũng được đối chiếu để phát hiện thay đổi giữa quá trình train/copy. Input đổi thì abort và cleanup temporary output, không publish protocol.

Prepare kiểm tra boundaries và warm-up để khóa intended coverage; chưa rollout trên test. Warm-up lấy thêm max(20,risk_window)+1 dòng trước phiên đầu đủ điều kiện. Không đưa warm-up vào equity curve, không mang vị thế từ validation sang test. Kết thúc tại open cuối; phí liquidation dùng cơ chế interval cuối của simulator.

Sensitivity **giữ nguyên Q table**, không bắt buộc cùng actions. Ví dụ phí cao hơn làm equity/drawdown đi sang một state bin khác; cùng Q có thể chọn action khác.

## Resume và tính toàn vẹn

Protocol khóa dataset/source/checkpoint/training-log hashes, cấu hình thực tế, bins/actions, Python/core package versions, uv.lock, Git revision và fingerprints các modules Python của package.

Thay docs không đổi calculation fingerprint. Hardening/refactor Python đã thay fingerprint: protocol AAPL cũ giữ nguyên, replay bằng revision b6c550d trong checkout riêng. Trên main, run/verify dùng protocol mới được chuẩn bị bằng code main; không sửa hashes cũ để bỏ qua kiểm tra. Thay logic Python hoặc lock sẽ bị phát hiện. Numerical runtime phải khớp Python/core packages; platform và optional GUI versions được ghi provenance.

Run bị gián đoạn: chạy lại cùng lệnh. Scenarios đã hoàn tất được kiểm tra hash trước khi tái dùng; chỉ scenarios thiếu mới được tính.

Completed manifest được ghi vào temporary file cùng directory, flush/fsync rồi replace atomic. Crash trước publication không để lại manifest JSON bị cắt; resume reuse scenarios đã hoàn tất và tạo lại summaries. Nếu manifest đã publish nhưng completed ledger event chưa ghi, lần chạy sau kiểm tra manifest và bổ sung event recovered.

Run hoàn tất: lệnh run kiểm tra summaries, scenario artifacts và protocol, rồi trả kết quả đã lưu. File bị sửa không bị âm thầm ghi đè. Không tự download snapshot hoặc thay checkpoint để vượt lỗi.

Experiment ledger tại outputs/stage-4/experiment-ledger.jsonl là append-only hash chain, có process locking. Events gồm prepared, started, scenario_completed, completed, failed và verified. Verify failures có record riêng.

Sau khi đã có test completed trong ledger, prepare protocol mới yêu cầu reason và thư mục mới, ví dụ:

```text
--output-dir outputs/stage-4/aapl-new-protocol
--reason "Tái dựng archive trong môi trường riêng"
```

Reason ghi lại mục đích experiment mới; không dùng vòng mới để chọn tham số theo test. Verify không tạo vòng lựa chọn mới và không sửa inventory đã khóa.

## Diagnostics và tổng hợp

| Diagnostic | Ý nghĩa |
|---|---|
| Action frequencies | Tỷ lệ target −1/−0,5/0/+0,5/+1; HoldPosition riêng |
| Flat decisions | Target 0, không phải exposure trước lệnh |
| Active intervals | Holdings sau quyết định khác 0 |
| Gross exposure | abs(units_after × execution_price / equity_before) |
| Long/short intervals | Dấu holdings sau quyết định |
| Unseen states | Không có visits nào trong state khi training |
| Trade duration | Calendar days từ mở đến đóng |
| Reward breakdown | Tổng gross-return fractions, cost fractions, lambda × risk và reward |
| Drawdown | Peak/trough/recovery của MDD và longest underwater calendar duration |

Nhãn cố định: no_trades; sparse_trades cho 1–4 closed trades; mostly_flat khi flat decisions ≥95%; unseen_states_present; insolvent. Nhãn giúp diễn giải, không thay policy hoặc selection.

Ví dụ target 0 có thể được đặt khi exposure trước quyết định là +0,5: đây là **một action flat để đóng vị thế**, không phải tài khoản đã flat trước đó.

Seed summaries báo mean/median/sample std/min/max của finite values, kèm số finite/undefined/infinite/not applicable/insolvent. Dưới hai finite values thì std là N/A. Không thay infinity bằng số lớn hoặc bỏ thất bại khỏi báo cáo.

Paired comparison lấy lambda 2 − lambda 0 **cùng seed và cost**. Không gộp equity năm seeds thành portfolio. Seed variability đo ngẫu nhiên của việc học trên cùng lịch sử, không phải confidence interval về tương lai thị trường.

Yearly summaries ghi expected_start_date/expected_end_date theo từng năm, lấy từ eligible intervals của test segment trước khi policy chạy. partial_year phản ánh horizon năm chưa đủ hoặc actual coverage không đạt các boundaries dự kiến; run insolvent trong tháng 12 vẫn được nhận diện. Đây không phải xác minh completeness của exchange calendar.

Yearly summaries giữ **một episode liên tục**. Returns compound theo end_date của interval; fees theo cùng intervals; trades đóng được đếm riêng. Không lấy trade P&L để tính calendar return vì trade có thể qua năm. Insolvent giữ actual coverage và debt, không thêm returns giả đến cuối horizon.

## Artifacts và biểu đồ

```text
protocol.json
frozen_models/
preparation/
run_manifest.json
primary_summary.csv/json
scenario_summary.csv/json
seed_summary.csv/json
paired_comparison.csv/json
yearly_summary.csv/json
diagnostics.json
runs/<scenario_id>/
    accounting/<policy>/
        equity.parquet
        ledger.parquet
        orders.parquet
        trades.parquet
        intervals.parquet
    decisions.parquet
    transitions.parquet       # RL only
    score.json
    diagnostics.json
    scenario.json
    completion.json
figures/
report.md
verification-*/
```

Score/manifest giữ intended và actual coverage/status; reward được ghi riêng với financial P&L. Completion hashes cho phép check/resume từng scenario.

FinPlot đọc artifacts với hai panel equity/drawdown:

```bash
uv run indexpilot-chart --run-dir outputs/stage-4/aapl-frozen
uv run indexpilot-chart --run-dir outputs/stage-4/aapl-frozen --cost-bps 20
uv run indexpilot-chart --run-dir outputs/stage-4/aapl-frozen --seeds --risk-lambda 2 --cost-bps 10
```

Report/chart không train hoặc đánh giá lại policies. Detailed outputs không nằm trong Git; kết quả cần đọc đi kèm archived inputs để replay.

**Đọc tiếp:** [README dự án](../README.md) dẫn tới kết quả và hướng dẫn tái lập.
