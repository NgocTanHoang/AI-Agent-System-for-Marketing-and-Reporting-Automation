# AI Agent System — Marketing & Reporting (Smartphone)

Hệ thống đa tác nhân (CrewAI) tự động: nghiên cứu xu hướng, sinh nội dung marketing và báo cáo có số liệu từ SQLite; tùy chọn xuất bản lên Google Docs.

## Yêu cầu

- Python 3.10+ (khuyến nghị; 3.8+ có thể chạy nếu dependency tương thích)
- Kết nối Internet (tìm kiếm DuckDuckGo)
- **NVIDIA NIM**: biến `NVIDIA_NIM_API_KEY` (hoặc `NVIDIA_API_KEY`) trong `.env` — nếu thiếu, code dùng `NoOpLLM` và pipeline vẫn *khởi động* nhưng không có suy luận LLM thực sự
- **Google Docs** (để đẩy báo cáo cuối): `credentials.json`, OAuth lần đầu tạo `token.json`, và `GOOGLE_DOCS_FOLDER_ID` trong `.env` (trùng với thư mục Drive đích bên dưới)

### Đích Google Drive cho báo cáo cuối

Agent **Business Reporter** gọi tool `publish_to_google_docs`; file Google Doc được tạo **trong thư mục Drive** có ID đặt trong `GOOGLE_DOCS_FOLDER_ID`.

- Thư mục dự án (mở bằng trình duyệt khi đã đăng nhập Google): [01_AI Agent System for Marketing and Reporting Automation trên Drive](https://drive.google.com/drive/folders/1MEBHa1MdluQ9b9ng4pa-cXr6gC3C5dD-?usp=drive_link)
- **Folder ID** (đã ghi trong `.env.example`): `1MEBHa1MdluQ9b9ng4pa-cXr6gC3C5dD-`

**Lưu ý quyền:** Tài khoản Google dùng khi chạy OAuth (`credentials.json` / `token.json`) phải có quyền **Chỉnh sửa** (Editor) đối với thư mục đó. Nếu thư mục thuộc tài khoản khác, hãy **chia sẻ thư mục** cho đúng email đó.

**Mình không thể “vào Drive” kiểm tra giúp bạn** (không có đăng nhập Google của bạn). Cách xác nhận sau khi chạy `main.py`:

1. Xem log: tool trả về dòng có `https://docs.google.com/document/d/...` nếu tạo Doc thành công.
2. Mở link thư mục Drive ở trên — file mới tên kiểu *Smartphone Market Strategic Report 2026* (hoặc theo `title` agent truyền vào).

Có thể copy `.env.example` thành `.env` rồi điền `NVIDIA_NIM_API_KEY` (và chỉnh `GOOGLE_DOCS_FOLDER_ID` nếu đổi thư mục).

## Cấu trúc thư mục

```
.
├── main.py
├── requirements.txt
├── .env                    # tạo tay, không commit
├── credentials.json        # OAuth Google — không commit
├── token.json              # sinh sau OAuth — không commit
├── data/
│   ├── raw/
│   │   ├── marketing_intelligence.db   # tạo bằng init_db (hoặc đã có sẵn)
│   │   └── sales_data.csv
│   └── processed/          # báo cáo .md (save_report)
├── notebooks/
└── src/
    ├── agents.py           # agent + LLM + đăng ký tools
    ├── tasks.py
    ├── tools.py            # search, DB, lưu file, Google Docs
    └── init_db.py          # tạo/làm mới DB mẫu
```

## Cài đặt

```bash
cd "01_AI Agent System for Marketing and Reporting Automation"
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Biến môi trường (`.env`)

Sao chép `.env.example` → `.env`, rồi điền API key. Thư mục Drive mặc định cho báo cáo:

```env
NVIDIA_NIM_API_KEY=your_nvidia_nim_key
GOOGLE_DOCS_FOLDER_ID=1MEBHa1MdluQ9b9ng4pa-cXr6gC3C5dD-
```

### Cơ sở dữ liệu

Tạo hoặc làm mới SQLite mẫu (chạy từ thư mục gốc project):

```bash
python src/init_db.py
```

File database: `data/raw/marketing_intelligence.db` (bảng: `sales`, `sales_performance`, `competitor_products`, `social_sentiment`, `marketing_campaigns`).

## Chạy

```bash
python main.py
```

**Windows (PowerShell):** Nếu console dùng CP1252 và CrewAI in nhiều ký tự Unicode, có thể gặp lỗi mã hóa. Cách ổn định:

```powershell
$env:PYTHONUTF8=1; python main.py
```

Luồng tuần tự: **Search Analyst** → **Content Strategist** → **Business Reporter** (`Process.sequential`, `memory=False` trong `main.py`).

## Cấu hình trong code

| File | Nội dung |
|------|----------|
| `src/agents.py` | Vai trò agent, LLM (NVIDIA / NoOp), tools |
| `src/tasks.py` | Mô tả từng Task |
| `src/tools.py` | DuckDuckGo, `query_marketing_db`, `save_report`, `publish_to_google_docs` |
| `src/init_db.py` | Schema + dữ liệu mẫu |

## Đầu ra

- Tóm tắt nghiên cứu, bản thảo nội dung, báo cáo markdown (có thể lưu dưới `data/processed/` qua tool `save_report`)
- Nếu cấu hình Google đủ: tài liệu mới trên Drive trong thư mục `GOOGLE_DOCS_FOLDER_ID`

## Phụ thuộc chính

- `crewai[tools]`, `litellm` (bắt buộc để CrewAI gọi NVIDIA NIM qua model `nvidia_nim/...`), `pydantic`, `python-dotenv`, `pandas`
- `ddgs` (tìm kiếm)
- `langchain-nvidia-ai-endpoints` (tuỳ chọn; LLM trong `agents.py` dùng `crewai.LLM` + LiteLLM, không còn `ChatNVIDIA` trực tiếp)
- `google-api-python-client`, `google-auth-oauthlib`, `google-auth-httplib2` (Google)

## Bảo mật

Không commit `.env`, `credentials.json`, `token.json`. Nên dùng `.gitignore` cho các file trên.

## License

Thêm thông tin license nếu cần.
