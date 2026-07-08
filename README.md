# Infosys Cobalt Powered AI Contract Lifecycle Management

AI-Powered Contract Lifecycle Management Tool built with Streamlit and OpenAI GPT-4o, running on the Infosys Cobalt cloud platform.

## Overview

Improve productivity of document reviews by identifying key elements, generating contract drafts, and managing risk in commercial contract management. Gen-AI integration enhances value, efficiency, and accuracy across the contract lifecycle.

## AI Agents

| Agent | Role |
|-------|------|
| **ClauseScout** | Scans contracts (including scanned PDFs via OCR) to extract parties, dates, obligations, penalties, and key terms |
| **DraftCraft** | Generates professionally structured contracts from templates with AI customization and clause library integration |
| **RiskRadar** | Evaluates contracts for risky clauses, compliance gaps, and missing protections with email alerts |
| **DiffLens** | Compares two contracts side-by-side with AI-powered difference analysis |
| **ContractCopilot** | Answers plain-English questions grounded in a specific contract, citing the exact clause it relied on |

## Features

### Core
- **Upload & Review** — Upload PDF/DOCX/TXT/scanned image contracts with AI key element extraction
- **Draft Generation** — Generate contracts from 6 templates (NDA, MSA, SOW, Employment, Vendor, Lease) with clause library
- **Risk Analysis** — Score contracts 0-100 with detailed risk breakdown and recommendations
- **Contract Comparison** — Side-by-side AI comparison of two contracts
- **Dashboard** — Portfolio overview with enterprise KPI cards, analytics charts, and expiration tracking
- **Contract Repository** — Search, filter, and manage all contracts with metadata

### Contract Intelligence (new)
- **Contract Copilot** — Conversational, grounded Q&A over any contract with clause-level citations and confidence — the "chat with your contract" experience expected of a modern CLM
- **Obligations & Renewals** — Obligation register with owner, due date, priority and status tracking; auto-import obligations extracted by ClauseScout; and a portfolio renewals calendar with overdue / due-soon signals

### Platform
- **Enterprise UI** — Cohesive design system (`utils/theme.py`): KPI stat cards, section headers, status/risk pills, consistent Plotly theming, active-state navigation, and an immersive animated login page
- **OCR Support** — Tesseract-based OCR for scanned/image-based PDFs and standalone images (PNG, JPG, TIFF)
- **Multi-User Authentication** — Role-based access (Admin, Analyst, Viewer) with streamlit-authenticator
- **Email Alerts** — SMTP-based notifications for expiring contracts and high-risk alerts
- **Clause Library** — Save, search, and reuse favorite contract clauses across drafts
- **Audit Trail** — Full activity tracking for compliance — who did what, when, on which contract
- **Bulk Upload** — Batch process multiple contracts with automatic extraction and risk scoring
- **Cloud Deployment** — Docker, docker-compose, and Streamlit Cloud ready

## Setup

### Local
```bash
pip install -r requirements.txt
streamlit run app.py
```

### Docker
```bash
docker-compose up --build
```

### Streamlit Cloud
1. Push to GitHub
2. Connect the repo in [share.streamlit.io](https://share.streamlit.io)
3. Set secrets (OPENAI_API_KEY, SMTP credentials) in the Streamlit Cloud dashboard
4. The `packages.txt` file installs Tesseract OCR automatically

### OCR Dependencies
For local OCR support, install:
- **Tesseract OCR**: https://github.com/tesseract-ocr/tesseract
- **Poppler** (for pdf2image): https://poppler.freedesktop.org/

## Default Login Credentials

| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | Admin |
| analyst | analyst123 | Analyst |
| viewer | viewer123 | Viewer |

## Tech Stack

- **Frontend**: Streamlit
- **AI**: OpenAI GPT-4o
- **Cloud**: Infosys Cobalt / Docker / Streamlit Cloud
- **Database**: SQLite (WAL mode)
- **OCR**: Tesseract + pdf2image
- **Auth**: streamlit-authenticator (bcrypt)
- **Charts**: Plotly
- **Export**: PDF (fpdf2), DOCX (python-docx), Excel (openpyxl)
- **Email**: smtplib (SMTP/TLS)
