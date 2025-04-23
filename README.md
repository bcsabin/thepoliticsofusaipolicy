# The Politics of U.S. AI Policy — Data Pipeline

This repository contains the codebase behind my senior thesis, “The Politics of U.S. AI Regulation: An Exploratory Study of Industry Influence and Regulatory Capture in U.S. AI Policymaking.”  
It automates the end-to-end process of:

1. Scraping all public comments (PDFs *and* on-page text) from Regulations.gov RFIs related to Executive Order 14110.  
2. Extracting structured insights with LLMs (OpenAI GPT o3-mini or Google Gemini 2.0 Flash).  
3. Exporting clean CSV / Excel tables used for every quantitative result in the thesis.

---

## Repository Layout

| `Scraper.py` | Headless Selenium crawler to download PDFs (or print on-page comments to PDF). | – |
| `MainArgumentsv2_GPTo3.py` / `MainArgumentsv2_Gem2.py` | Extracts each commenter’s main policy arguments. | GPT o3-mini / Gemini |
| `Organization_GPTo3.py` | Classifies **organization name, type, industry, and function**. | GPT o3-mini / Gemini |
| `SentimentScore_*` | Scores **sentiment** toward regulation (Pro, Neutral, De-Reg). | GPT o3-mini / Gemini |
| `Advocacy_GPT.py` / `advocacy_Gem.py` | Scores **advocacy strength** (0–10) across 8 policy topics. | GPT o3-mini / Gemini |
| `percentoutputGPT.py` / `percentoutputGEm.py` | Calculates **% content** about each policy topic. | GPT o3-mini / Gemini |

> Use either GPT or Gemini versions consistently throughout.

---

## Quick Start

### 1 · Clone and Create Virtual Environment

```bash
git clone https://github.com/bcsabin/thepoliticsofusaipolicy.git
cd thepoliticsofusaipolicy
python -m venv .venv
source .venv/bin/activate
```

### 2 · Install Requirements

```bash
pip install -r requirements.txt
```

### 3 · Add API Keys

```bash
export OPENAI_API_KEY="sk-..."
export GOOGLE_API_KEY="your-gemini-key"
```

Or, place them in a `.env` file and use `python-dotenv` to load them.

---

### 4 · Edit File Paths

Each script contains placeholders like:

```python
pdf_directory = "your file location"   # input PDFs
desktop_path  = "your file location"   # output CSV/XLSX
```

Update *all* such file paths to match your local environment.

---

### 5 · Run the Full Pipeline

```bash
# A. Scrape PDFs
python Scraper.py

# B. Extract main arguments
python MainArgumentsv2_GPTo3.py       # or MainArgumentsv2_Gem2.py

# C. Classify organizations
python Organization_GPTo3.py          # or Organization_Gem2.py

# D. Score sentiment
python SentimentScore_GPTo3.py        # or SentimentScore_Gem2.py

# E. Score advocacy strength
python Advocacy_GPT.py                # or advocacy_Gem.py

# F. Calculate % content per topic
python percentoutputGPT.py            # or percentoutputGEm.py
```

All output files are saved as CSV or Excel in your specified output directory.

---

## Dependencies

| Package | Purpose |
|--------|---------|
| `selenium` + `chromedriver` | Scraping PDFs from Regulations.gov |
| `reportlab` | Saving web-only comments as PDFs |
| `PyPDF2`, `PyMuPDF (fitz)` | Text extraction from PDFs |
| `openai` | GPT o3-mini API calls |
| `google-generativeai` | Gemini 2.0 Flash API calls |
| `pandas`, `openpyxl`, `tqdm`, `concurrent.futures` | Data handling, file writing, and performance |

You can manage these with `pip` and store them in `requirements.txt`.

---

## How Everything Fits

```text
Regulations.gov  ──▶  Scraper.py  ──▶  PDFs
PDFs ──▶ MainArguments  ▹ arguments.csv
     └─▶ Organization   ▹ org_meta.csv
     └─▶ SentimentScore ▹ sentiment.csv
     └─▶ Advocacy       ▹ advocacy.csv
     └─▶ PercentOutput  ▹ percent.csv
```

Merge those five tables to reproduce every figure in Sections 6–7 of the thesis.

---

## Reproducing Thesis Figures

1. Run the full pipeline above.  
2. Import the CSVs into your analysis notebook or stats tool.  
3. Recreate visuals using the column names documented in the **Methodology** appendix.

---

## Citation

If you use this code or methodology, please cite:

Sabin, B. (2025). The Politics of U.S. AI Regulation: An Exploratory Study of Industry Influence and Regulatory Capture in U.S. AI Policymaking. University of Michigan, Ross School of Business.**
