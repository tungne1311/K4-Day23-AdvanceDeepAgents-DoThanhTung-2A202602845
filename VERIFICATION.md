# Đối chiếu mẫu trích dẫn — 09/10/2026

Đây là ghi chú kiểm chứng, không sửa nội dung báo cáo đã tải từ sandbox.
Kiểm tra tự động xác nhận cấu trúc và liên kết số trích dẫn; đối chiếu mẫu dưới
đây kiểm tra nội dung bằng nguồn gốc. Việc kiểm tra mẫu không đảm bảo mọi câu
trong báo cáo đều đúng. Các số liệu chỉ áp dụng trong thiết lập của từng bài.

## World Model

Báo cáo: `reports/survey-about-world-model.md`.

| Trích dẫn | Khẳng định được kiểm tra | Bằng chứng và kết quả |
|---|---|---|
| [4] PlaNet | Khoảng 200 lần ít tương tác môi trường hơn các baseline model-free | Đạt trong thiết lập thí nghiệm của bài; phần Introduction, mục đóng góp, nêu mức trung bình 200×. [Bài đầy đủ](https://arxiv.org/html/1811.04551v5). |
| [2] DreamerV3 | Hơn 150 nhiệm vụ, một cấu hình hyperparameter; lấy kim cương Minecraft không dùng dữ liệu người | Đạt. Abstract và Introduction của [bài Nature](https://www.nature.com/articles/s41586-025-08744-2) nêu các kết quả này. |
| [10] DayDreamer | Bốn robot thật; quadruped học trong một giờ, thích nghi với đẩy trong mười phút | Đạt. Abstract của [bài PMLR](https://proceedings.mlr.press/v205/wu23c.html) hỗ trợ số robot và các thời gian này. |
| [7] IRASim | Push-T IoU tăng từ 0.637 lên 0.961 nhờ model-based planning tại thời điểm kiểm thử | Đạt cho thí nghiệm được tác giả báo cáo. [Abstract arXiv](https://arxiv.org/abs/2406.14540) nêu hai giá trị và cơ chế test-time scaling. |
| [11] WorldArena | 16 chỉ số cảm nhận; chất lượng hình ảnh cao không đảm bảo khả năng làm nhiệm vụ tốt | Đạt. [Trang HF](https://huggingface.co/papers/2602.08971) và [bài gốc, Abstract và kết quả](https://arxiv.org/html/2602.08971) mô tả 16 chỉ số và perception–functionality gap. |

## Reinforcement learning for LLM reasoning

Báo cáo: `reports/survey-about-reinforcement-learning-for-llm-reasoning.md`.

| Trích dẫn | Khẳng định được kiểm tra | Bằng chứng và kết quả |
|---|---|---|
| [3] DPO | Tối ưu preference bằng classification loss, tránh vòng RL và reward model riêng | Đạt. [Abstract bài gốc](https://arxiv.org/abs/2305.18290) mô tả policy đóng và classification loss; không suy rộng kết quả sang mọi bài reasoning. |
| [4] PPO | Cho phép nhiều epoch cập nhật minibatch qua surrogate objective | Đạt. [Bài PPO](https://arxiv.org/abs/1707.06347) nêu cải tiến so với một cập nhật mỗi mẫu của policy gradient truyền thống. |
| [6] Process/outcome feedback | Trên GSM8K, outcome supervision có thể đạt độ đúng đáp án tương tự với ít nhãn; reasoning-step correctness cần process feedback | Đạt trong thiết lập của [bài gốc](https://arxiv.org/abs/2211.14275). Không coi đây là kết luận chung cho mọi mô hình/nhiệm vụ. |
| [11] OmegaPRM | Divide-and-conquer MCTS tự động thu thập nhãn process supervision | Đạt. [Abstract bài gốc](https://arxiv.org/abs/2406.06592) mô tả MCTS, binary search lỗi đầu tiên và thu thập tự động không có can thiệp người. |
| [5] TIPS | Huấn luyện generative PRM bằng outcome-only RL | Đạt. [Abstract bài gốc](https://arxiv.org/abs/2609.36641) nêu reward chỉ phụ thuộc outcome và tối ưu toàn bộ response bằng group-relative advantage. |

## LLM agents and tool use

Báo cáo: `reports/survey-about-llm-agents-and-tool-use.md`.
Metadata có 89 bản ghi URL/nhãn từ tool ở host; cả 10 nguồn cuối đều khớp sổ.
Ba nhãn là arXiv, HF Daily, HF Search: hai nhãn HF cùng một nhà cung cấp.

| Trích dẫn | Khẳng định được kiểm tra | Bằng chứng và kết quả |
|---|---|---|
| [1] MRKL | Kiến trúc neuro-symbolic kết hợp mô hình ngôn ngữ với module tri thức/suy luận rời rạc | Đạt. [Abstract bài gốc](https://arxiv.org/abs/2205.00445) định nghĩa kiến trúc nhiều neural model cùng module discrete knowledge/reasoning. |
| [2] Toolformer | Học khi nào gọi API, tham số và sử dụng kết quả bằng self-supervised learning | Đạt. [Abstract bài gốc](https://arxiv.org/abs/2302.04761) hỗ trợ các thành phần này. |
| [5] Agentic BBO | Kết hợp ngữ nghĩa nhiệm vụ, tool tối ưu và quyết định dựa trên phản hồi | Đạt. [Abstract bài gốc](https://arxiv.org/abs/2610.12183) mô tả cách agent giải BBO với ngân sách hữu hạn. |
| [6] Intent-Eval | Đề xuất bị người dùng từ chối vẫn có thể làm lệch nhiệm vụ; benchmark gồm tool actions, code, databases, mathematics | Đạt. [Abstract bài gốc](https://arxiv.org/abs/2610.06496) mô tả thất bại mentioned-as-in-effect và các miền đánh giá. |
| [7] SoK Agentic Skills | Skill đóng gói tri thức thủ tục, điều kiện áp dụng và execution policies | Đạt. [Abstract bài gốc](https://arxiv.org/abs/2602.20867) định nghĩa skill theo các thành phần này, phân biệt với một tool call đơn lẻ. |

## Video/multimodal và efficient inference

Đang sinh báo cáo; sẽ đối chiếu mẫu sau khi có kết quả cuối.
