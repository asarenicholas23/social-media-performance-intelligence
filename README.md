# Social Media Performance Intelligence System

A Python-based data pipeline that transforms raw, multi-platform social media data into clean, structured datasets and meaningful performance metrics — delivered through an interactive analytics dashboard.

Built using real data from **TNYOU Fitness** across Instagram, TikTok, Facebook, and LinkedIn.

**🔗 [Live Dashboard →](https://smpi2026.streamlit.app)**

---

## What It Does

Most social media reporting stops at vanity metrics. This system goes further — it answers real business questions:

- Which platform gives us the most **awareness**, **engagement**, and **conversions**?
- Which **post type** works best on each platform?
- Which **day of the week** drives the highest engagement?
- What do **save rate**, **profile visits**, and **posting consistency** tell us?

---

## System Architecture

```
Raw CSV Data
     │
     ▼
┌─────────────────┐
│  clean_data.py  │  ← Standardise, parse dates, enforce types
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   metrics.py    │  ← Compute engagement rate, save rate, follow conversion
└────────┬────────┘
         │
         ▼
┌──────────────────────┐
│  exploration.ipynb   │  ← EDA: validate, analyse, extract insights
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│  dashboard/          │  ← Interactive Streamlit dashboard
│  dashboard.py        │
└──────────────────────┘
```

---

## Project Structure

```
social-media-performance-intelligence/
├── data/
│   ├── raw/
│   │   └── SM_Pred_Training_Data.csv       # Original raw data (frozen)
│   └── processed/
│       ├── cleaned_SM_data.csv             # Output of clean_data.py
│       └── metrics_SM_data.csv             # Output of metrics.py
├── scripts/
│   ├── clean_data.py                       # Layer 1 — Data cleaning pipeline
│   └── metrics.py                          # Layer 2 — Metrics computation
├── notebooks/
│   └── exploration.ipynb                   # Layer 3 — Exploratory data analysis
├── dashboard/
│   └── dashboard.py                        # Layer 4 — Streamlit dashboard
├── docs/
│   └── project_overview.md
├── requirements.txt
└── README.md
```

---

## Pipeline Layers

### Layer 1 — Data Foundation (`scripts/clean_data.py`)
- Handles encoding issues (`latin1`)
- Standardises column names to `snake_case`
- Parses mixed date formats safely
- Enforces platform-specific data types
- Preserves `NaN` where metrics are structurally absent (not data quality issues)
- Cleans text fields: caption, hashtags, post description

### Layer 2 — Metrics Engine (`scripts/metrics.py`)
- Computes `total_engagement` = likes + comments + shares + saves
- Computes `engagement_rate` = total_engagement / impressions
- Computes `save_rate` = saves / impressions (Instagram & TikTok only)
- Computes `follow_conversion_rate` = follows / impressions (Instagram only)
- Uses safe division — no divide-by-zero errors
- Preserves `NaN` where metrics don't apply per platform

### Layer 3 — Exploratory Data Analysis (`notebooks/exploration.ipynb`)
10-section notebook covering:
- Pipeline validation
- Data overview and null audit
- Post type normalisation (12 raw variants → 5 canonical labels)
- Metric distributions
- Platform comparison
- Content type analysis
- Temporal patterns (day of week, monthly trends)
- Correlation analysis
- Top and bottom performers
- EDA summary and insights

### Layer 4 — Dashboard (`dashboard/dashboard.py`)
Interactive Streamlit dashboard with 5 tabs:

| Tab | Question Answered |
|-----|------------------|
| Q1 · Platform Performance | Awareness (impressions/reach), Engagement (rate + components), Conversion (follows) |
| Q2 · Content by Platform | Best post type per platform for awareness and engagement |
| Q3 · Best Days to Post | Day-of-week analysis overall and per platform |
| Q4 · Additional Metrics | Save rate, profile visits, impressions spread, posting frequency |
| Top Posts | Rank any metric, filter by platform, identify posts by caption |

**Sidebar filters:** Platform, Post Type, Date Range
**Export:** Filtered data CSV, per-tab summary CSVs, full interactive HTML report

---

## Data

| Field | Detail |
|-------|--------|
| Source | TNYOU Fitness (used with consent) |
| Platforms | Instagram, TikTok, Facebook, LinkedIn |
| Posts | 337 |
| Date range | January 2024 – December 2025 |
| Post types | Reel, Video, Photo, Carousel, Text |

**Key design decision:** No blanket `.fillna(0)` — metrics are only computed where they are meaningful per platform. Facebook and LinkedIn do not track saves; TikTok does not report reach separately. These are treated as structurally absent, not missing data.

---

## Running Locally

**1. Clone the repo**
```bash
git clone https://github.com/asarenicholas23/social-media-performance-intelligence.git
cd social-media-performance-intelligence
```

**2. Create and activate a virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Run the pipeline**
```bash
python scripts/clean_data.py
python scripts/metrics.py
```

**5. Launch the dashboard**
```bash
streamlit run dashboard/dashboard.py
```

**6. (Optional) Run the EDA notebook**
```bash
jupyter notebook notebooks/exploration.ipynb
```

---

## Tech Stack

| Layer | Tools |
|-------|-------|
| Data processing | Python, pandas, NumPy |
| Analysis | Jupyter, Matplotlib, Seaborn, SciPy |
| Dashboard | Streamlit, Plotly |
| Version control | Git, GitHub |

---

## Key Findings

- **LinkedIn** leads on median engagement rate despite the smallest post volume
- **TikTok** drives the highest median impressions — best platform for awareness
- **Reels outperform Photos** on Instagram for reach; Photos outperform Reels for engagement rate
- **Videos** are the strongest format on Facebook and LinkedIn for engagement
- Higher impressions weakly negatively correlates with engagement rate (r = -0.16) — reach and resonance are not the same thing
- **Time of day** is not captured in the current dataset — a data gap to address going forward

---

## Status

| Layer | Status |
|-------|--------|
| Data cleaning | ✅ Complete |
| Metrics engine | ✅ Complete |
| Exploratory analysis | ✅ Complete |
| Dashboard | ✅ Complete — [Live](https://smpi2026.streamlit.app) |
| CSV upload packaging | 🔄 In progress |

---

## About

Built by [Nicholas Asare](https://www.linkedin.com/in/nicholas-asare-718175169/) as a portfolio project in social media analytics and data pipeline engineering.

Data provided by TNYOU Fitness with consent.