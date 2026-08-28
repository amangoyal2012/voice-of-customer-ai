# voice-of-customer-ai

# 🚀 GenAI Customer Intelligence

An AI-powered customer insight platform that leverages Generative AI and Large Language Models (LLMs) to analyze customer feedback, reviews, surveys, and support interactions. The application transforms unstructured customer data into actionable business insights, helping organizations improve customer satisfaction and make data-driven decisions.

## ✨ Features

- 🔍 Customer Feedback Analysis
- 😊 Sentiment Analysis (Positive, Neutral, Negative)
- 📊 Automated Insight Generation
- 🏷️ Topic & Keyword Extraction
- 🤖 LLM-Based Summarization
- 💡 AI-Powered Recommendations
- 📈 Trend Analysis & Reporting


## 🏗️ Architecture

```text
Customer Data
     │
     ▼
 Data Processing Layer
     │
     ▼
 Sentiment Analysis Engine
     │
     ▼
 Generative AI / LLM
     │
     ▼
 Insights & Recommendations
     │
     ▼
 Dashboard & Reports
```

## 🛠️ Technology Stack

- Language: Python
- AI Framework: LangChain (`langchain_community`)
- LLM: Ollama (`llama3.2:1b`), runnable locally — can be swapped for OpenAI
- Sentiment Analysis: Hugging Face `transformers` (DistilBERT `sst-2-english`)
- Data Processing: pandas, openpyxl
- UI / Visualization: Streamlit, Matplotlib

## 📂 Project Structure

```text
voice-of-customer-ai/
│
├── data/                                  # Raw customer review data
│   └── raw_extracted_data.xlsx
├── notebook/                              # Notebook pipeline
│   └── genAI_Customer_Intelligence.ipynb  # raw data -> summary/sentiment/tag/recommendation pipeline
├── src/                                   # Streamlit apps
│   ├── Insight_Analyzer_App.py            # All-in-one Streamlit app (raw upload -> pipeline -> dashboard)
│   └── Dashboard.py                       # Visualization-only Streamlit dashboard (pre-processed data)
├── output/                                # Generated summaries produced by the pipeline
│   └── genAI_Customer_Reviews_Summaries.csv
├── README.md
└── requirements.txt
```

## 🚀 Use Cases

### Customer Review Analysis
Analyze product reviews and identify key customer sentiments and concerns.

### Voice of Customer (VoC)
Extract recurring themes from customer feedback channels.

### Support Ticket Intelligence
Automatically summarize support tickets and identify common issues.

### Brand Monitoring
Track customer perception and sentiment trends over time.

## 📊 Example Output

### Input

```text
"The product works well but customer support response time is very slow."
```

### AI Analysis

```json
{
  "sentiment": "Neutral",
  "positive_points": [
    "Product performance"
  ],
  "negative_points": [
    "Slow customer support"
  ],
  "recommendation": "Improve response time to enhance customer satisfaction."
}
```

## ⚙️ Installation

```bash
pip install -r requirements.txt
```

See **How to Use This Implementation** below for the full setup (including Ollama) and how to run each piece.

## 🧩 How to Use This Implementation

This repo contains a working implementation of the platform above, built with Python, [LangChain](https://python.langchain.com/)/[Ollama](https://ollama.com/) and [Streamlit](https://streamlit.io/).

### Folder reference

| Path | Purpose |
|---|---|
| `data/raw_extracted_data.xlsx` | Sample raw review export used as input. |
| `notebook/genAI_Customer_Intelligence.ipynb` | Notebook pipeline: reads the raw Excel sheet, generates a review summary, sentiment, one-word tag, and AI recommendation per row via Ollama + DistilBERT, and writes the summary CSV to `output/`. |
| `src/Insight_Analyzer_App.py` | All-in-one Streamlit app — upload raw Excel data, run the same AI pipeline live, and explore the results in an interactive dashboard. No notebook required. |
| `src/Dashboard.py` | Visualization-only Streamlit dashboard for data that has **already** been processed (e.g. the CSV produced by the notebook or `Insight_Analyzer_App.py`). |
| `output/genAI_Customer_Reviews_Summaries.csv` | Generated summary/sentiment/tag/recommendation output from the pipeline. |
| `requirements.txt` | Python dependencies for the notebook and both Streamlit apps. |

### 1. Set up the environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Also install and start [Ollama](https://ollama.com/) locally, then pull the model used by the pipeline:

```powershell
ollama pull llama3.2:1b
ollama serve
```

### 2. Option A — Run the notebook pipeline, then visualize

1. Open `notebook/genAI_Customer_Intelligence.ipynb` and run all cells against your raw Excel file in `data/` (default: `raw_extracted_data.xlsx`, feedback in the `Detailed Feedback` column). This produces a summary CSV in `output/` (e.g. `genAI_Customer_Reviews_Summaries.csv`).
2. Launch the visualization dashboard and upload that processed file:

   ```powershell
   streamlit run src/Dashboard.py
   ```

### 3. Option B — All-in-one app (no notebook needed)

```powershell
streamlit run src/Insight_Analyzer_App.py
```

- Upload your raw Excel file in the sidebar and pick the feedback column.
- Click **Run Analysis** to generate summaries, sentiment, tags, and AI recommendations.
- Explore Sentiment Distribution, Sentiment Over Time, Source Insights, Tag Insights, and Top Reviews tabs, plus an on-demand final comprehensive summary.
- Download the processed results as CSV.

## 📈 Future Enhancements

- Multi-language customer feedback analysis
- Real-time sentiment monitoring
- RAG-based knowledge retrieval
- Customer churn prediction
- Advanced analytics dashboard
- Agentic AI-powered recommendations

