# Tiến độ lab — hoàn tất ngày 10/10/2026

Đã hoàn tất mã nguồn và năm bộ báo cáo. `self_check.py` của lớp báo
**READY to submit**. Cả năm báo cáo đạt kiểm tra citation, cấu trúc, coverage;
các lượt có discovery ledger cũng khớp toàn bộ URL/nhãn nguồn đã khám phá thật.
Đã đối chiếu năm mẫu trích dẫn mỗi báo cáo với nguồn gốc; xem `VERIFICATION.md`.

Repo nộp bài: [K4-Day23-AdvanceDeepAgents-DoThanhTung-2A202602845](https://github.com/tungne1311/K4-Day23-AdvanceDeepAgents-DoThanhTung-2A202602845).

| Chủ đề | Nguồn cuối | Nhãn nguồn | Lượt `task` thật | Trạng thái |
|---|---:|---:|---:|---|
| World Model | 15 | 3 | 4 | Đạt |
| RL for LLM reasoning | 11 | 3 | 4 | Đạt |
| LLM agents/tool use | 10 | 3 | 8 | Đạt; discovery ledger trong metadata |
| Video/multimodal | 9 | 3 | 5 | Đạt; hai revision kiểm chứng nội dung trong sandbox |
| Efficient inference/small models | 21 | 4 | 5 | Đạt; hai revision kiểm chứng nội dung trong sandbox |

## Kiểm tra đã hoàn tất

- Python 3.12.10, `.venv`, dependencies và `pip check` đã kiểm tra.
- Năm source tools đã chạy với mạng thật; retry/backoff/jitter/Retry-After và
  khoảng cách arXiv được triển khai.
- Docker sandbox đã chạy thật, upload/check/download/cleanup. Mọi sửa báo cáo,
  finalizer và validator chạy trong sandbox; file tải về giữ nguyên bytes.
- 68 tests offline đạt, gồm kiểm tra không chấp nhận bản sửa bị validator từ chối.
- `self_check.py`: năm chủ đề OK, git/secrets OK, READY to submit.
- `model.py`, `sandbox.py`, `self_check.py`, `finalize_citations.py` được giữ nguyên.
- `.env`, `.venv`, `.runs` được git bỏ qua. Khóa ở host, không tải vào sandbox.

Ba báo cáo đầu dùng model lab20 `google_genai:gemini-3.5-flash-lite`. Ngày 09/10
và đầu ngày 10/10 Gemini báo hết quota ngày; lượt thử text nhỏ thành công không
đủ để xác nhận chạy được workflow. Sau khi gọi agent thật thành công tối 10/10,
đã tiếp tục từ checkpoint và hoàn tất hai chủ đề còn lại bằng cùng model lab20.

Model miễn phí lab19 đã thử khi Gemini hết quota, nhưng lượt lỗi không được
đưa vào bài nộp hoặc cộng vào metadata. Token trong metadata chỉ đếm lead;
chi phí/tokens thực tế còn bao gồm researcher/checker. Revision giữ các lượt
giao việc thật của generation, cộng đúng lượt model/tool của revision thành công
và lưu lịch sử `revisions`. Các lượt đã dừng không được coi là revision thành công.

## Chạy lại

```powershell
cd E:\K4-Day23-AdvanceDeepAgents-Labs
.\.venv\Scripts\python.exe -m unittest discover -s tests
.\.venv\Scripts\python.exe self_check.py
# Chỉ sinh lại chủ đề chưa đạt; lượt chạy đủ năm hiện sẽ bỏ qua cả năm:
.\.venv\Scripts\python.exe run_all.py --resume
```

`prepare_sources.py` lưu kết quả tool thật/receipts ở `.runs/` để tránh tìm lại
nguồn đã có; checkpoint không phải bài nộp và không công khai. Nếu kiểm chứng
phát hiện lỗi mới, dùng `revise_report.py <topic> <review.md> --focused` để agent
fetch nguồn và gửi bản sửa vào sandbox, không sửa tay báo cáo ở host.

Kiểm tra tự động và 25 mẫu đối chiếu không bảo đảm mọi câu đều đúng hoặc quyết
định điểm số. Các mục chất lượng nội dung trong RUBRIC vẫn do giảng viên chấm.
