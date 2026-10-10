# Đối chiếu mẫu trích dẫn — cập nhật 10/10/2026

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

## Video and multimodal generation

Báo cáo: `reports/survey-about-video-and-multimodal-generation.md`.
Metadata có 136 cặp URL/nhãn khám phá thực tế; chín nguồn cuối đều khớp sổ.
Ba nhãn: web, HF Search, HF Daily. Hai nhãn HF cùng một nhà cung cấp.

| Trích dẫn | Khẳng định được kiểm tra | Bằng chứng và kết quả |
|---|---|---|
| [1] Sora | Transformer hoạt động trên spacetime latent patches; dữ liệu có độ dài, độ phân giải, aspect ratio khác nhau | Đạt. [Báo cáo kỹ thuật OpenAI](https://openai.com/index/video-generation-models-as-world-simulators/) mô tả nén video theo không gian/thời gian, patchification và joint image/video training. |
| [4] NExT-GPT | Kết nối LLM với multimodal adaptors và diffusion decoders để nhận/sinh text, image, video, audio | Đạt. [Abstract bài gốc](https://arxiv.org/abs/2309.05519) hỗ trợ kiến trúc và các modality; không suy rộng thành một hệ thống sinh nội dung hoàn toàn autoregressive. |
| [6] CogVideoX | 3D VAE, expert transformer với expert adaptive LayerNorm; video 10 giây, 16 fps | Đạt trong mô hình được tác giả báo cáo. [Abstract](https://arxiv.org/abs/2408.06072) nêu trực tiếp các thành phần và thông số. |
| [7] Open-Sora 2.0 | Full attention; chi phí huấn luyện được tác giả báo cáo là $200k | Đạt. [Abstract](https://arxiv.org/abs/2503.09642) nêu chi phí, [mục 3.2](https://arxiv.org/html/2503.09642) nêu full attention. Không suy ra chi phí tương đối của hệ thống proprietary không công bố. |
| [8] WorldGuide | Closed-loop procedural execution: chọn hành động, sinh clip, dùng trạng thái sinh ra để chọn bước tiếp theo hoặc dừng | Đạt. [Abstract bài gốc](https://arxiv.org/abs/2610.12459) mô tả Planner/Executor và việc thích nghi với kết quả trung gian. |

Các lỗi phát hiện được đã sửa bằng agent trong sandbox: gán STDiT sai cho
Open-Sora, nhầm tham số của FLUX/Open-Sora, trích dẫn AnimateDiff trỏ vào
WorldGuide, nhầm mô hình hiểu video với mô hình sinh video, và câu xu hướng
vượt bằng chứng. Hai revision được ghi trong metadata; giữ tập URL/nhãn nguồn,
finalizer có thể đánh số lại theo thứ tự trích dẫn. Không sửa báo cáo ở host.

## Efficient inference and small language models

Báo cáo: `reports/survey-about-efficient-inference-and-small-language-models.md`.
21 nguồn cuối; bốn nhãn arXiv, HF Daily, HF Search, web đều có bằng chứng discovery.

| Trích dẫn | Khẳng định được kiểm tra | Bằng chứng và kết quả |
|---|---|---|
| [1] FlashAttention | Exact attention với IO-aware tiling, giảm HBM reads/writes; không loại bỏ quadratic arithmetic của dense attention | Đạt. [Abstract](https://arxiv.org/abs/2205.14135) phân biệt IO complexity và thuật toán exact. Các speedup trong abstract là kết quả training, không là bảo đảm inference chung. |
| [2] PagedAttention | Quản lý KV cache bằng nguyên lý paging, giảm fragmentation/waste và cho phép sharing | Đạt. [Bài gốc](https://arxiv.org/abs/2309.06180) nêu near-zero waste và flexible sharing; không khẳng định internal waste bằng không tuyệt đối. |
| [5] AWQ | Xác định các channel quan trọng theo activation distribution thay vì chỉ theo weight | Đạt. [Abstract](https://arxiv.org/abs/2306.00978) mô tả activation statistics và scaling salient channels. |
| [8] TinyLlama | Mô hình pretrained 1.1B, tận dụng FlashAttention và hệ sinh thái Llama | Đạt. [Abstract](https://arxiv.org/abs/2401.02385) nêu kích thước, pretraining và nền tảng Llama 2; không mô tả nó như distilled BERT. |
| [20] Speculative decoding | Draft sinh chuỗi autoregressively; target kiểm tra các vị trí song song, giữ target distribution bằng acceptance/rejection | Đạt. [Algorithm 1 và mục 2](https://arxiv.org/html/2211.17192) ghi rõ hai bước và quy tắc điều chỉnh phân phối. |

Các lỗi phát hiện được đã sửa bằng hai revision trong sandbox: độ phức tạp
FlashAttention, fragmentation PagedAttention, raw paper identifier trong câu,
phân biệt DistilBERT/TinyLlama và bước draft/verification của speculative decoding.
Đối chiếu tổng cộng 25 mẫu cho năm báo cáo; không khẳng định đã xác minh mọi câu.
