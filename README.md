# 🤖 AI Marketing Agent System: Automated Research & Strategic Reporting

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/CrewAI-Agentic%20Orchestration-red)](https://www.crewai.com/)
[![LLM](https://img.shields.io/badge/NVIDIA%20NIM-Llama%203.3%2070B-green)](https://www.nvidia.com/en-us/ai/nim/)
[![Status](https://img.shields.io/badge/status-Demo%20%2F%20Portfolio-orange)]()

A multi-agent system that automates the end-to-end workflow of **market intelligence**, **content strategy**, and **business reporting** for a smartphone retail chain. Built with **CrewAI** for agent orchestration and **NVIDIA NIM** (Llama 3.3 70B) for high-performance LLM inference.

> [!NOTE]
> This project is designed for **local demo and portfolio purposes**. It uses SQLite as a lightweight data store — not intended for production-scale concurrent workloads.

---

## 🚀 Overview

The system coordinates **three specialized AI agents** running in a sequential pipeline. Each agent performs a distinct role — from web research to content planning to executive reporting — and the final output is displayed directly on a premium **FastAPI Dashboard**.

### Key Capabilities

| Capability                           | Description                                                                                             |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------- |
| 🔍 **Market Intelligence**      | Real-time web search (DuckDuckGo) for latest tech trends and competitor pricing                         |
| 📊 **SQL-Based Data Retrieval** | Agents query a local SQLite database containing marketing campaigns, sales data, and consumer sentiment |
| 📝 **Strategic Synthesis**      | Auto-generates SWOT analyses, ROI comparisons, and retail action plans                                  |
| 🌐 **Web Dashboard**           | Interactive UI built with FastAPI and Chart.js to visualize real-time retail intelligence               |
| 📈 **Data Visualization**       | Generates sales charts (matplotlib) embedded in the reports                                             |

---

## 🏗 System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CrewAI Sequential Pipeline                   │
│                                                                     │
│  ┌──────────────┐    ┌───────────────────┐    ┌──────────────────┐  │
│  │   Agent 1     │───▶│     Agent 2       │───▶│     Agent 3      │  │
│  │ Search Analyst│    │Content Strategist │    │Business Reporter │  │
│  └──────┬───────┘    └────────┬──────────┘    └────────┬─────────┘  │
│         │                     │                        │            │
│    DuckDuckGo +          SQLite Query            SQLite + Chart +   │
│    SQLite Query          (Sentiment)             Web UI (FastAPI)   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Agent Roles

1. **Search Analyst** — Scours the web for competitor pricing, promotions, and new product launches. Cross-references findings with internal sales and inventory data from the database.
2. **Content Strategist** — Analyzes social sentiment data (emotions, mentions, complaints) and raw marketing drafts to provide critical feedback and design targeted campaigns.
3. **Business Reporter** — Aggregates all insights, queries sales performance data, generates charts, and writes an Executive Retail Report in Markdown for the Web UI.

---

## 🛠 Tech Stack

| Category                    | Technology                                                                   |
| --------------------------- | ---------------------------------------------------------------------------- |
| **Orchestration**     | [CrewAI](https://github.com/crewAIInc/crewAI)                                   |
| **LLM Inference**     | [NVIDIA NIM](https://www.nvidia.com/en-us/ai/nim/) — Llama 3.3 70B via LiteLLM |
| **Web Search**        | DuckDuckGo (via `ddgs` library)                                            |
| **Database**          | SQLite (local demo store)                                                    |
| **Web Framework**     | [FastAPI](https://fastapi.tiangolo.com/)                                     |
| **Visualization**     | Chart.js (Dashboard) & Matplotlib (Generated reports)                        |

---

## 📊 Database Schema

The system uses a local `marketing_intelligence.db` with 5 tables of synthetic retail data:

| Table                   | Key Columns                                                         | Purpose                       |
| ----------------------- | ------------------------------------------------------------------- | ----------------------------- |
| `competitor_products` | brand, model, price, strengths, weaknesses                          | Competitive landscape & SWOT  |
| `marketing_campaigns` | channel, budget, reach, conversions, ROI, status                    | Campaign performance tracking |
| `social_sentiment`    | keyword, positive/negative score, top_emotion, mentions             | Consumer sentiment analysis   |
| `sales`               | brand, model, units_sold, price, customer_age_group, payment_method | Granular transaction data     |
| `sales_performance`   | product_name, units_sold, revenue, month_period                     | Monthly revenue summaries     |

---

## ⚙️ Installation

### 1. Clone & Setup

```bash
git clone https://github.com/NgocTanHoang/AI-Agent-System-for-Marketing-and-Reporting-Automation.git
cd AI-Agent-System-for-Marketing-and-Reporting-Automation
python -m venv venv

# Activate virtual environment
# Windows PowerShell:
.\venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

### 2. Environment Variables

Create a `.env` file in the project root:

```env
NVIDIA_NIM_API_KEY=your_nvidia_nim_api_key
```

### 3. Initialize Database

```bash
python src/init_db.py
```

---

## 🚀 Execution

### Run the Web UI (Recommended)
The Web UI provides a centralized place to trigger the pipeline and view results.

```bash
uvicorn app:app --reload
```
Visit: `http://localhost:8000`

### Run the Pipeline (CLI)
```bash
python main.py
```

---

## 📂 Project Structure

```apache
.
├── .env                      # API keys
├── README.md                 # Project documentation
├── app.py                    # Web UI (FastAPI)
├── main.py                   # Entry point for the AI pipeline
├── src/
│   ├── agents.py             # Agent definitions
│   ├── tasks.py              # Task prompts
│   ├── tools.py              # Custom tools (Search, SQL, Matplotlib)
│   └── init_db.py            # DB Initializer
├── data/
│   ├── raw/                  # DB and rough content
│   └── processed/            # Generated reports and charts
├── templates/                # HTML templates for Web UI
```

**Author**: [Ngọc Tân Hoàng](https://github.com/NgocTanHoang)
