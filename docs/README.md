# Tài liệu IndexPilot US100

Bộ tài liệu mô tả **prototype AAPL đã hoàn thành**: từ snapshot giá đến simulator, Q-learning, frozen test và tái lập. Nội dung được tổ chức theo cách dùng/đọc dự án; không cần đi qua lịch sử triển khai để hiểu cơ chế.

## Mục lục

- [Bắt đầu ở đâu](#bắt-đầu-ở-đâu)
- [Các chương](#các-chương)
- [Hai lộ trình đọc](#hai-lộ-trình-đọc)
- [Phân biệt tài liệu và artifacts](#phân-biệt-tài-liệu-và-artifacts)

## Bắt đầu ở đâu

- Muốn hiểu dự án làm gì: [01 — Tổng quan](01-overview.md).
- Muốn chạy hoặc xem kết quả: [02 — Quickstart](02-quickstart.md).
- Muốn biết RL đã học được gì: [07 — Kết quả](07-results.md).
- Muốn replay đúng experiment: [08 — Tái lập](08-reproduction.md).

Ví dụ nếu chỉ muốn xem equity/drawdown, restore saved artifacts rồi dùng indexpilot-chart. Nếu muốn kiểm tra kết quả thật sự lặp lại được, restore thêm exact snapshot/models và dùng indexpilot-evaluate verify. Hai mục đích có prerequisites khác nhau.

## Các chương

| Chương | Nội dung chính |
|---|---|
| [01 — Tổng quan](01-overview.md) | Phạm vi AAPL/US100, stack và kiến trúc |
| [02 — Quickstart](02-quickstart.md) | Setup, commands, archived experiment và snapshot mới |
| [03 — Dữ liệu](03-data.md) | Giá điều chỉnh, quality checks, causal features, hash/splits |
| [04 — Simulator](04-simulator.md) | Account, target sau phí, reward, baselines, trades/metrics |
| [05 — Q-learning](05-q-learning.md) | State bins, actions, Bellman update, training/selection |
| [06 — Evaluation](06-evaluation.md) | Locked protocol, 60 scenarios, diagnostics/resume/verify |
| [07 — Kết quả](07-results.md) | Validation/test, activity, seeds/costs và giới hạn |
| [08 — Tái lập](08-reproduction.md) | Restore archive, runtime/hashes, report/chart và lỗi |

## Hai lộ trình đọc

### Hiểu dự án

[01](01-overview.md) → [03](03-data.md) → [04](04-simulator.md) → [05](05-q-learning.md) → [06](06-evaluation.md) → [07](07-results.md).

Đi theo luồng: dữ liệu có từ lúc nào → tiền và vị thế thay đổi thế nào → agent học bằng gì → test được giữ riêng thế nào → kết quả có ý nghĩa gì.

### Chạy dự án

[02](02-quickstart.md) → [08](08-reproduction.md), rồi [07](07-results.md) để đối chiếu và diễn giải.

Với fresh download, xem [03](03-data.md) và chỉ gọi đó là snapshot mới. Với exact reproduction, dùng archive có hash đã khóa. Git clone không chứa market data hoặc checkpoints.

## Phân biệt tài liệu và artifacts

- Docs giải thích cơ chế và chọn các bảng giúp hiểu kết quả.
- Configs là tham số thực tế version-controlled.
- Data/manifests/checkpoints/detailed outputs nằm local, ngoài Git.
- Generated report.md, CSV/JSON, Parquet và PNG được sinh từ artifacts; không thay thế input cần cho verify.

Vốn/fees/reward/metrics có định nghĩa trong [simulator](04-simulator.md); source of truth về protocol là frozen protocol.json đã lưu. Khi tiếp tục nghiên cứu, tạo experiment riêng có lý do rõ ràng thay vì đổi lựa chọn sau khi xem test đã công bố.

**Đọc tiếp:** [01 — Tổng quan](01-overview.md) hoặc [02 — Quickstart](02-quickstart.md). [README dự án](../README.md) là trang giới thiệu ở root.
