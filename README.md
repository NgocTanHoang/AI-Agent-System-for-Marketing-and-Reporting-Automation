# AI Marketing Agent System: Automated Research & Strategic Reporting

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/CrewAI-Agentic%20Orchestration-red)](https://www.crewai.com/)
[![LLM](https://img.shields.io/badge/NVIDIA%20NIM-Llama%203.3%2070B-green)]([https://www.nvidia.com/en-us/ai/nim/](https://build.nvidia.com/meta/llama-3_3-70b-instruct))

An advanced multi-agent system designed to automate the end-to-end workflow of market intelligence, content strategy, and business reporting for the technology sector. This project leverages **CrewAI** for agent orchestration and **NVIDIA NIM** for high-performance inference.

---

## 🚀 Overview

This system coordinates three specialized AI agents to transform raw market data and web search results into professional-grade strategic reports, automatically published to Google Docs.

### Key Capabilities:
- **Autonomous Market Intelligence**: Real-time web crawling (DuckDuckGo) for latest tech trends and competitor movements.
- **Enterprise Data Integration**: RAG-enabled agents querying an internal **SQLite** database containing marketing intelligence, sales performance, and consumer sentiment.
- **Strategic Synthesis**: Automatic generation of SWOT analyses and ROI-focused marketing recommendations.
- **Cloud Automation**: Unattended publishing of formatted reports to **Google Docs** via Google Drive API integration.

---

## 🛠 Tech Stack

- **Orchestration**: [CrewAI](https://github.com/joaomdmoura/crewAI)
- **Inference Engine**: [NVIDIA NIM](https://www.nvidia.com/en-us/ai/nim/) (Llama 3.3 70B via LiteLLM)
- **Search**: DuckDuckGo API
- **Database**: SQLite (Marketing Intelligence Schema)
- **Cloud Integration**: Google Drive & Google Docs API v1
- **Data Handling**: Pandas & Pydantic

---

## 🏗 System Architecture

The workflow follows a **Sequential Process**:

1.  **Search Analyst**: Scours the internet for the 5 most critical news items in the tech/smartphone industry and contrasts them with internal DB records.
2.  **Content Strategist**: Analyzes social sentiment scores from the database to draft 3 highly targeted social media campaigns and event ideas.
3.  **Business Reporter**: Aggregates all insights, queries sales performance data, builds a comprehensive Markdown report, and publishes it to the cloud.

---

## 📊 Database Schema

The system relies on a specialized `marketing_intelligence.db` containing:
- `competitor_products`: Technical specs, pricing, and competitive SWOT tags.
- `marketing_campaigns`: Historical performance, budgets, and ROI metrics.
- `social_sentiment`: Keyword-based sentiment scores and consumer complaints.
- `sales` & `sales_performance`: Granular sales data and monthly revenue summaries.

---

## ⚙️ Installation

### 1. Clone & Setup
```bash
git clone https://github.com/NgocTanHoang/AI-Agent-System-for-Marketing-and-Reporting-Automation.git
cd "AI Agent System for Marketing and Reporting Automation"
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment Variables (`.env`)
Create a `.env` file in the root directory:
```env
NVIDIA_NIM_API_KEY=your_nvidia_api_key_here
GOOGLE_DOCS_FOLDER_ID=your_drive_folder_id
```

### 3. Initialize Database
```bash
python src/init_db.py
```

---

## 🚀 Execution

Run the complete pipeline with a single command:

```bash
# Standard run
python main.py

# Windows PowerShell (Recommended for Unicode support)
$env:PYTHONUTF8=1; python main.py
```

---

## 📂 Project Structure

```
.
├── src/
│   ├── agents.py       # Agent definitions & LLM configuration
│   ├── tasks.py        # Detailed task prompts & requirements
│   ├── tools.py        # Search, SQLite, and Google API integrations
│   └── init_db.py      # Database schema & seed data creation
├── data/
│   ├── raw/            # marketing_intelligence.db location
│   └── processed/      # Locally saved Markdown reports
├── notebooks/          # Development & experimentation logs
├── main.py             # Main entry point & Crew orchestration
└── requirements.txt    # Project dependencies
```

---

## 🔒 Security Note
This project is configured to ignore `.env`, `credentials.json`, `token.json`, and `.db` files to prevent the leakage of sensitive credentials and internal data. Always use the provided `.gitignore`.

---

## 📄 License
This project is for educational and portfolio purposes.

---
**Author**: [Ngọc Tân Hoàng](https://github.com/NgocTanHoang)
