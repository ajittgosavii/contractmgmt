# Demo Contract Pack

A curated set of **fictional** contracts for demonstrating the Infosys Cobalt AI Contract
Lifecycle Management app. All parties, names, figures, and terms are invented for demo
purposes only — they are not real agreements.

The set is designed to exercise **every feature**: extraction (ClauseScout), risk
scoring (RiskRadar), comparison (DiffLens), the grounded Q&A (Contract Copilot),
Obligations & Renewals, and the dashboard/email-alert flows. Dates are tuned so the
"Expiring Soon" and renewals views light up (reference date: mid-2026).

## How to use
1. Download the `.txt` files from this folder (GitHub → click a file → **Raw** → save;
   or **Code → Download ZIP** for the whole repo).
2. In the app, go to **🔍 Upload & Review** (one at a time) or **📦 Bulk Upload**
   (all at once), and upload the files.
3. When saving to the repository, set the **Contract Type** and **Status** as suggested
   below (Status drives the dashboard — mark the "expiring" ones **Active**).

## What each contract demonstrates

| # | File | Type | Suggested status | Highlights for the demo |
|---|------|------|------------------|--------------------------|
| 1 | `01_MSA_CloudScale_Acme_LowRisk.txt` | MSA | Active | Clean, well-balanced contract → **low risk score**. Great baseline to contrast against #2. Net-30, mutual indemnity, liability cap, GDPR/CCPA, 99.9% SLA. |
| 2 | `02_SaaS_Subscription_Nimbus_HighRisk.txt` | Vendor Agreement | Active | **High-risk showcase for RiskRadar.** Auto-renewal (90-day notice), **unlimited customer liability**, vendor cap of **$100**, perpetual data license, **no DPA/GDPR**, one-sided indemnification, unilateral price/term changes. Expires **2026-08-20** → also appears in renewals. |
| 3 | `03_Mutual_NDA_Infosys_Meridian.txt` | NDA | Active | Standard mutual NDA → low risk. Good for clean extraction of parties, confidentiality term, governing law. |
| 4 | `04_SOW_DataPlatform_Migration.txt` | SOW | Active | **5 milestones with owners, due dates, and payments** → perfect for the **Obligations & Renewals** import. Liquidated-damages/service-credit clause. |
| 5 | `05_Employment_SeniorEngineer_Sharma.txt` | Employment Agreement | Active | Non-compete (12 mo), IP assignment, severance, at-will → RiskRadar flags the **broad non-compete** and restrictive covenants. |
| 6 | `06_Vendor_Supply_Globex_ExpiringSoon.txt` | Vendor Agreement | Active | **Expires 2026-07-31** → triggers the **"Expiring Soon" KPI** and **Email Alerts**. Late-delivery penalties, warranty, INR pricing. |
| 7 | `07_Office_Lease_TechPark_Bangalore.txt` | Lease Agreement | Active | 5-year commercial lease, 5% annual escalation, lock-in, security deposit → shows lease-specific extraction. |

## Suggested 5-minute demo flow
1. **Bulk Upload** all 7 → watch batch extraction + auto risk scoring populate the **Dashboard** KPIs and charts.
2. **Dashboard** → point out **Total / Active / High Risk / Expiring ≤30d** cards and the "avg risk by type" chart. Contract #6 shows up under *Expiring Soon*.
3. **Risk Analysis** on **#2 (Nimbus SaaS)** → RiskRadar surfaces unlimited liability, the $100 cap, missing data protection, auto-renewal — then save a recommendation to the **Clause Library**.
4. **Contract Copilot** on **#2** → ask *"Can we get out of this contract, and what's the liability cap?"* → grounded answer with clause citations.
5. **Contract Comparison** → compare **#1 (clean MSA)** vs **#2 (risky SaaS)** → DiffLens shows which is more favorable.
6. **Obligations & Renewals** → import obligations from **#4 (SOW)**; show the renewals calendar with **#6** overdue/expiring.
7. **Email Alerts** → preview the expiry alert for **#6**.

> Tip: because RiskRadar and Copilot call OpenAI, make sure `OPENAI_API_KEY` is set in the app's Streamlit secrets before the demo.
