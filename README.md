# thepoliticsofusaipolicy
This is the code I used to collect information for my senior thesis: The Politics of U.S. AI Regulation: An Exploratory Study of Industry Influence and Regulatory Capture in U.S. AI Policymaking

# U.S. AI Policy RFI Analysis – Detecting Industry Influence and Regulatory Capture

This repository contains the full codebase and methodology for the senior thesis project titled:

**_“The Politics of U.S. AI Regulation: An Exploratory Study of Industry Influence and Regulatory Capture in U.S. AI Policymaking”_**

By Barry Sabin  
University of Michigan - Ross School of Business  
April 2025

---

## 📘 Abstract

This study investigates whether the U.S. AI policymaking process—particularly in response to President Biden's Executive Order 14110—shows signs of **regulatory capture** by industry actors. Using **large language models (LLMs)** and a custom-built Python data pipeline, we analyze 547 public comments submitted to Requests for Information (RFIs) issued by NIST, NTIA, and OMB.

Our goal is to determine:
- Who is influencing AI policy?
- What are their policy objectives?
- How strongly do they advocate for these objectives?

---

## 🧪 Methodology Overview

### 1. **Data Collection**

- Scraped and downloaded **547 PDF comment documents** submitted to three government RFIs related to EO 14110:
  - [NIST](https://www.nist.gov/)
  - [NTIA](https://www.ntia.doc.gov/)
  - [OMB](https://www.whitehouse.gov/omb/)

- Downloaded using **Python + Selenium WebDriver**

### 2. **AI Models Used**

Two large language models were benchmarked:
- `OpenAI gpt-3.5-turbo (o3-mini)`
- `Google Gemini 2.0 Flash`

Each model was used for different tasks based on:
- Accuracy against human-validated benchmarks
- Cost
- Speed

### 3. **Metric Extraction**

For each comment, the following **metrics** were extracted using custom prompts and stored in a `.csv` file:

#### Meta Metrics
- Organization Name
- Type (Corporation, University, Research Lab, etc.)
- Industry
- Regulation Sentiment (Pro/Neutral/De-Regulation)

#### Policy Objective Metrics
- Content Percentage: % of text aligned to 8 defined policy objectives
- Advocacy Score: Strength of support (0–10) for each policy objective

Eight policy objectives:
1. Model Security and Vulnerability Testing  
2. Data Privacy and Protection  
3. AI Governance Frameworks  
4. Content Authenticity  
5. Global Standards and Cooperation  
6. Industry, Labor, and IP  
7. Ethical Development and Societal Impact  
8. Energy and Environmental Sustainability  

---

## 📈 Validation and Benchmarking

- **12 documents** were hand-analyzed to validate AI performance
- Both LLMs were benchmarked on accuracy (content extraction and advocacy scoring)
- OpenAI's `o3-mini` was chosen for content categorization
- Gemini 2.0 Flash was chosen for scoring advocacy strength

---

## 🧠 Theoretical Framework

We use the **Social Construction of Technology (SCOT)** framework to interpret our findings and understand how industry actors influence policymakers' perception of AI technologies.

---

## 📂 Project Structure

```bash
📁 /data
    └── Raw PDFs of RFI Comments
📁 /scripts
    ├── selenium_scraper.py
    ├── metric_extraction_gemini.py
    ├── metric_extraction_openai.py
    └── prompt_templates/
📁 /outputs
    ├── comments_metrics.csv
    └── benchmarking_results.csv
📄 README.md
📄 requirements.txt
