# Tiến độ lab — 10/10/2026

Đã triển khai các TODO và sinh ba báo cáo bằng model lab20
`google_genai:gemini-3.5-flash-lite`. Đã kiểm tra lại lúc khoảng 00:11 ngày
10/10/2026 (Asia/Saigon): lượt thử ngắn thành công, nhưng lượt chạy agent thật
vẫn bị chặn bởi quota ngày. Repo public hiện giữ ba bộ báo cáo đã hoàn tất;
`.env` tiếp tục dùng Gemini lab20.

| Bước | Trạng thái | Bằng chứng |
|---|---|---|
| Môi trường | Đạt | Python 3.12.10, `.venv`, `pip check` thành công, Docker hoạt động. |
| Validator | Đạt kiểm tra offline | Schema, URL/nhãn, trích dẫn, References, nguồn trùng, cấu trúc và coverage. |
| Năm source tools | Đã thử mạng thật | arXiv, HF và Exa trả nguồn thật; retry có backoff, jitter và Retry-After. |
| Agents | Đã chạy thật | Lead giao việc, đọc ghi chú, gọi citation-checker; mọi agent có giới hạn gọi. |
| Sandbox | Đã thử thật | Upload → finalizer → validator → download → cleanup; khóa/network tools ở host. |
| Kiểm tra mã | Đạt | 66 tests offline thành công; các tệp CÓ SẴN được giữ nguyên. |
| Báo cáo | 3/5 hoàn tất | Bản nháp chưa đạt không được ghi vào `reports/`. |
| Kiểm chứng mẫu | 3/5 hoàn tất | Năm mẫu mỗi báo cáo đầu, ghi trong `VERIFICATION.md`. |
| Nộp link trước | Repo cá nhân public | Mã nguồn và ba bộ báo cáo đã đạt; hai chủ đề còn thiếu được ghi rõ. |

| Chủ đề | Nguồn cuối | Nhãn nguồn | Lượt `task` | Trạng thái |
|---|---:|---:|---:|---|
| World Model | 15 | 3 | 4 | Đạt validator, cấu trúc và coverage |
| RL for LLM reasoning | 11 | 3 | 4 | Đạt validator, cấu trúc và coverage |
| LLM agents/tool use | 10 | 3 | 8 | Đạt; metadata có 89 cặp URL/nhãn được tool khám phá |
| Video/multimodal | — | — | — | Giữ bản nháp agent gốc, chờ quota Gemini |
| Efficient inference/small models | — | — | — | Đã chuẩn bị nguồn thật, chưa có kết quả cuối |

## Cấu hình và trở ngại đã xác nhận

- Kiểm tra ngày 10/10: `run_all.py --resume` bỏ qua ba báo cáo đạt và thử tiếp
  video. Gemini trả `429 RESOURCE_EXHAUSTED`, quota
  `GenerateRequestsPerDayPerProjectPerModel-FreeTier`, hạn mức 500; API đề nghị
  chờ `24534s` (khoảng 6 giờ 49 phút). Không coi lượt thử text ngắn thành công
  là bằng chứng đủ để chạy được toàn bộ workflow.
- Lượt lỗi đã lưu lại bảy tệp nháp/ghi chú và dọn container. Không có báo cáo
  mới hoặc thay đổi nào trong ba bộ kết quả đã nộp. Docker đã khởi động thành công.

- Gemini chạm quota ngày 500 requests, thông báo phải chờ hơn 11 giờ. Khóa Gemini
  lab19 và lab20 giống nhau; đổi giữa hai khóa không tạo hạn mức mới.
- Hai tài khoản OpenRouter lab18/lab19 không còn số dư để dùng Qwen trả phí.
- LFM miễn phí đã gọi tool thành công. Lượt video đầu của LFM có nguồn sai schema,
  gán nhãn URL sai và khẳng định kiến trúc không được nguồn hỗ trợ. Đã dừng, lưu
  bản nháp lỗi riêng và dọn container; không đưa vào bài nộp.
- Lượt chạy lại LFM cũng chạm `free-models-per-day`: hạn mức 50, còn 0 request.
  Không tiếp tục gọi LLM hôm nay. Bản nháp Gemini gốc được khôi phục để tiếp tục.
- Chế độ tùy chọn `LAB_COMPACT_MODE=1` giới hạn 35 lượt model của lead, 10 của
  researcher, 8 của checker. Cấu hình hiện tại trở về `LAB_COMPACT_MODE=0` cho
  Gemini; pacing đầu vào dùng chung 180.000 token/phút.
- Lỗi quota ngày không được retry như quota phút. Model/key nằm trong `.env`
  được git bỏ qua; không ghi giá trị khóa vào tài liệu hoặc sandbox.

`prepare_sources.py` gọi tool nguồn thật ở host, lưu receipts và discovery ledger
trong `.runs/<slug>/`. Runner yêu cầu nguồn cuối khớp URL/nhãn đã quan sát thật.
Không sửa tay báo cáo; không cộng lượt `task`/token của run lỗi vào run mới.

## Lệnh tiếp tục

```powershell
cd E:\K4-Day23-AdvanceDeepAgents-Labs
.\.venv\Scripts\python.exe run_all.py --resume
.\.venv\Scripts\python.exe self_check.py
```

Chạy lại sau khi hết thời gian chờ do API trả về. Nếu Gemini vẫn báo quota ngày,
chờ đến khi provider cho phép thay vì retry liên tục. Lệnh này giữ ba báo cáo đã đạt và tiếp tục từ
ghi chú/bản nháp cục bộ trong `.runs/`; các checkpoint không được công khai.

[Tài liệu Gemini](https://ai.google.dev/gemini-api/docs/rate-limits) ghi quota
RPD theo project và reset lúc midnight Pacific; thời gian này khác thời gian chờ
của lỗi API vừa nhận. Vì vậy không cam kết giờ reset cụ thể: cần xác nhận bằng
workflow thật khi kiểm tra tiếp, không chỉ bằng một câu trả lời ngắn.

`--resume` chỉ bỏ qua báo cáo đã vượt kiểm tra. `self_check.py` chưa thể đạt đầy đủ
khi còn thiếu hai bộ kết quả. `model.py`, `sandbox.py`, `self_check.py` và
`finalize_citations.py` được giữ nguyên. Kho mẫu của lớp được giữ làm upstream;
bài nộp ở [repo cá nhân tungne1311](https://github.com/tungne1311/K4-Day23-AdvanceDeepAgents-DoThanhTung-2A202602845).

Kiểm tra trước khi công khai: ba báo cáo đạt citation/structure/coverage;
`self_check.py` chỉ báo thiếu hai chủ đề còn lại, kiểm tra git/secrets đạt.
Đã đối chiếu khóa hiện có của các lab với mọi file staged và blob trong lịch sử
Git, không có giá trị khóa bị đưa vào repo. `.env`, `.venv` và `.runs` được bỏ qua.
