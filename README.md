# Smart Contracts Management

AI-Powered Contract Lifecycle Management Tool built with Streamlit and OpenAI GPT-4o.

## Overview

Improve productivity of document reviews by identifying key elements, generating contract drafts, and managing risk in commercial contract management. Gen-AI integration enhances value, efficiency, and accuracy across the contract lifecycle.

## AI Agents

| Agent | Role |
|-------|------|
| **ClauseScout** | Scans contracts to extract parties, dates, obligations, penalties, and key terms |
| **DraftCraft** | Generates professionally structured contracts from templates with AI customization |
| **RiskRadar** | Evaluates contracts for risky clauses, compliance gaps, and missing protections |
| **DiffLens** | Compares two contracts side-by-side with AI-powered difference analysis |

## Features

- **Upload & Review** — Upload PDF/DOCX/TXT contracts and extract key elements with AI
- **Draft Generation** — Generate contracts from 6 built-in templates (NDA, MSA, SOW, Employment, Vendor, Lease)
- **Risk Analysis** — Score contracts 0-100 with detailed risk breakdown and recommendations
- **Contract Comparison** — Side-by-side AI comparison of two contracts
- **Dashboard** — Portfolio overview with KPIs, charts, and expiration tracking
- **Contract Repository** — Search, filter, and manage all contracts with metadata

## Setup

```bash
pip install -r requirements.txt
streamlit run app.py
```

Enter your OpenAI API key in the sidebar to enable AI features.

## Tech Stack

- **Frontend**: Streamlit
- **AI**: OpenAI GPT-4o
- **Database**: SQLite (local)
- **Charts**: Plotly
- **Export**: PDF (fpdf2), DOCX (python-docx), Excel (openpyxl)
