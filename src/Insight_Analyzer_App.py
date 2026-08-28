"""Streamlit app: upload a raw review Excel sheet, run the GenAI summarization,
sentiment analysis, tagging and recommendation pipeline (same logic as
FinalSummarization.ipynb), then explore the results in an interactive
dashboard (based on UI/Dashboard.py).

Run with:
    streamlit run "Insight_Analyzer_App.py"
"""
import csv

import pandas as pd
import matplotlib.pyplot as plt
import requests
import streamlit as st

st.set_page_config(page_title="voice-of-customer-ai", layout="wide")

# Import heavy/optional dependencies defensively so a broken env shows a clean
# message in the UI instead of a raw traceback.
try:
    import nltk
    from langchain_community.llms import Ollama
    from transformers import pipeline
except ImportError as e:
    st.error(
        f"Missing or broken dependency: **{e}**\n\n"
        "Fix by reinstalling the pinned requirements in this project's virtual environment:\n"
        "```powershell\n"
        "pip install -r requirements.txt --force-reinstall\n"
        "```\n"
        "Then restart the Streamlit app."
    )
    st.stop()

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.2:1b"
SENTIMENT_MODEL = "distilbert/distilbert-base-uncased-finetuned-sst-2-english"

SUMMARY_PROMPT_TEMPLATE = """
Carefully read the following content and please summarize the review like a short summary that captures important insights, features, observations.
Go beyond high-level abstraction — include specific details, examples, comparision with other maket tools or nuanced feedback if present. Highlight what stands out, whether it's strong opinions, repeated concerns, uncommon suggestions. Maintain a professional and coherent tone. Avoid sentiments, don't provide ratings, headings, bullet points, or lists. Avoid using word - praise, instead use highlight.

Do not include any extra title or header while returning the short summary.

Content:
{reviews}
"""

FINAL_SUMMARY_PROMPT = """Here are summaries of individual customer reviews:
{all_summaries}

Based on this information, write a comprehensive final summary in paragraph form.
Identify key patterns, trends, and insights shared across reviews.
Also highlight any comparisons or feedback where customers referenced or compared this product/tool with other similar tools or competitors.
Avoid using bullet points or section headers; keep the summary in a well-structured paragraph."""

COLOR_MAP = {"POSITIVE": "#4CAF50", "NEUTRAL": "#FFC107", "NEGATIVE": "#F44336", "N/A": "#CCCCCC"}


# ---------------------------------------------------------------------------
# Cached model loaders (loaded once per Streamlit server session)
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner="Loading local LLM (Ollama)...")
def get_llm():
    return Ollama(model=OLLAMA_MODEL, temperature=0)


@st.cache_resource(show_spinner="Loading sentiment analysis model...")
def get_sentiment_pipeline():
    nltk.download("wordnet", quiet=True)
    nltk.download("omw-1.4", quiet=True)
    return pipeline("sentiment-analysis", model=SENTIMENT_MODEL, truncation=True)


def is_ollama_running():
    try:
        requests.get(OLLAMA_BASE_URL, timeout=2)
        return True
    except requests.exceptions.RequestException:
        return False


# ---------------------------------------------------------------------------
# Pipeline logic (mirrors FinalSummarization_28072025.ipynb)
# ---------------------------------------------------------------------------
def safe_sentiment(sentiment_pipeline, text):
    if not isinstance(text, str) or text.strip() == "":
        return {"label": "N/A", "score": 0.0}
    try:
        return sentiment_pipeline(text, truncation=True)[0]
    except Exception as e:
        st.warning(f"Sentiment analysis error: {e}")
        return {"label": "N/A", "score": 0.0}


def generate_tag(llm, summary):
    if not isinstance(summary, str) or summary.strip() == "":
        return "N/A"
    tag_prompt = f"""Read the following review summary and respond with exactly one single word that best tags its main theme (for example: Performance, Usability, Pricing, Support, Reliability, Integration, Security, FeatureRequest, Bug, Positive, Negative). Respond with only the single word, no punctuation, no explanation.

Summary:
{summary}"""
    try:
        words = llm.invoke(tag_prompt).strip().split()
        return words[0].strip(".,!?") if words else "N/A"
    except Exception as e:
        st.warning(f"Tagging error: {e}")
        return "N/A"


def generate_recommendation(llm, summary):
    if not isinstance(summary, str) or summary.strip() == "":
        return "N/A"
    recommendation_prompt = f"""Read the following review summary and provide one concise, actionable AI recommendation for the product team based on it. Respond in a single sentence, no headers or bullet points.

Summary:
{summary}"""
    try:
        return llm.invoke(recommendation_prompt).strip()
    except Exception as e:
        st.warning(f"Recommendation error: {e}")
        return "N/A"


def process_reviews(raw_df, feedback_col, row_limit, include_tag, include_recommendation, progress_callback=None):
    llm = get_llm()
    sentiment_pipeline = get_sentiment_pipeline()

    rows = raw_df if not row_limit else raw_df.head(row_limit)
    total = len(rows)
    results = []

    for position, (_, row) in enumerate(rows.iterrows(), start=1):
        feedback = row.get(feedback_col, "")
        summary = llm.invoke(SUMMARY_PROMPT_TEMPLATE.format(reviews=feedback))
        sentiment_result = safe_sentiment(sentiment_pipeline, feedback)

        results.append({
            "Published Date": row.get("Published Date", "Unknown"),
            "Review Source": row.get("Review Source", "Unknown"),
            "Review Summary": summary,
            "Detailed Feedback": feedback,
            "Sentiment": sentiment_result.get("label", "N/A"),
            "Confidence": sentiment_result.get("score", 0.0),
            "Tag": generate_tag(llm, summary) if include_tag else "N/A",
            "AI Recommendation": generate_recommendation(llm, summary) if include_recommendation else "N/A",
        })

        if progress_callback:
            progress_callback(position, total)

    return pd.DataFrame(results)


def generate_final_summary(processed_df):
    llm = get_llm()
    all_summaries = "\n".join(processed_df["Review Summary"].dropna().astype(str))
    return llm.invoke(FINAL_SUMMARY_PROMPT.format(all_summaries=all_summaries))


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
st.title("GenAI Customer Intelligence")
st.write("Upload raw review data, run AI summarization/sentiment/tagging, and explore the results below.")

if "processed_df" not in st.session_state:
    st.session_state.processed_df = None
if "final_summary" not in st.session_state:
    st.session_state.final_summary = None

with st.sidebar:
    st.header("1. Upload & Run")
    uploaded_file = st.file_uploader("Upload raw Excel file", type=["xlsx", "xls"])

    raw_df = None
    if uploaded_file is not None:
        raw_df = pd.read_excel(uploaded_file)
        st.caption(f"{len(raw_df)} rows loaded.")

        default_col = "Detailed Feedback" if "Detailed Feedback" in raw_df.columns else raw_df.columns[0]
        feedback_col = st.selectbox(
            "Feedback column to summarize", options=list(raw_df.columns),
            index=list(raw_df.columns).index(default_col),
        )
        row_limit = st.number_input("Limit rows to process (0 = all)", min_value=0, value=0, step=1)
        include_tag = st.checkbox("Generate one-word Tag", value=True)
        include_recommendation = st.checkbox("Generate AI Recommendation", value=True)

        if st.button("Run Analysis", type="primary"):
            if not is_ollama_running():
                st.error(
                    "Ollama server not reachable at http://localhost:11434. "
                    "Start it (e.g. `ollama serve`) and make sure the `llama3.2:1b` model is pulled."
                )
            else:
                progress_bar = st.progress(0, text="Processing reviews...")

                def update_progress(position, total):
                    progress_bar.progress(position / total, text=f"Processing review {position}/{total}...")

                processed_df = process_reviews(
                    raw_df, feedback_col, row_limit or None, include_tag, include_recommendation,
                    progress_callback=update_progress,
                )
                st.session_state.processed_df = processed_df
                st.session_state.final_summary = None
                progress_bar.empty()
                st.success(f"Processed {len(processed_df)} reviews.")

processed_df = st.session_state.processed_df

if processed_df is None:
    st.info("Upload a raw Excel file and click **Run Analysis** in the sidebar to get started.")
else:
    df = processed_df.copy()
    df["Published Date"] = pd.to_datetime(df["Published Date"], errors="coerce", utc=True).dt.date

    # --- Filters ---
    st.sidebar.header("2. Filters")
    min_date, max_date = df["Published Date"].min(), df["Published Date"].max()
    selected_dates = st.sidebar.date_input("Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)
    all_sources = sorted(df["Review Source"].dropna().unique())
    selected_sources = st.sidebar.multiselect("Review sources", options=all_sources, default=all_sources)
    all_sentiments = sorted(df["Sentiment"].dropna().unique())
    selected_sentiments = st.sidebar.multiselect("Sentiments", options=all_sentiments, default=all_sentiments)
    all_tags = sorted(t for t in df["Tag"].dropna().unique() if t != "N/A")
    selected_tags = st.sidebar.multiselect("Tags (optional)", options=all_tags, default=[])

    date_range = selected_dates if isinstance(selected_dates, tuple) else (selected_dates, selected_dates)
    filtered_df = df[
        (df["Published Date"] >= date_range[0])
        & (df["Published Date"] <= date_range[-1])
        & (df["Review Source"].isin(selected_sources))
        & (df["Sentiment"].isin(selected_sentiments))
    ]
    if selected_tags:
        filtered_df = filtered_df[filtered_df["Tag"].isin(selected_tags)]

    # --- Key metrics ---
    st.subheader("Key Metrics")
    total_reviews = len(filtered_df)
    positive_pct = (filtered_df["Sentiment"] == "POSITIVE").mean() * 100 if total_reviews else 0
    negative_pct = (filtered_df["Sentiment"] == "NEGATIVE").mean() * 100 if total_reviews else 0
    avg_confidence = filtered_df["Confidence"].mean() if total_reviews else 0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Reviews", total_reviews)
    m2.metric("Positive %", f"{positive_pct:.1f}%")
    m3.metric("Negative %", f"{negative_pct:.1f}%")
    m4.metric("Avg. Sentiment Confidence", f"{avg_confidence:.2f}")

    st.download_button(
        "Download processed CSV",
        data=processed_df.to_csv(index=False, quoting=csv.QUOTE_MINIMAL),
        file_name="Individual_Reviews_Summaries.csv",
        mime="text/csv",
    )

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Sentiment Distribution", "Sentiment Over Time", "Source Insights", "Tag Insights", "Top Reviews & Final Summary",
    ])

    with tab1:
        st.subheader("Sentiment Distribution")
        sentiment_counts = filtered_df["Sentiment"].value_counts()
        fig1, ax1 = plt.subplots(figsize=(4, 4))
        ax1.pie(sentiment_counts, labels=sentiment_counts.index, autopct="%1.1f%%", startangle=90,
                colors=[COLOR_MAP.get(s, "#CCCCCC") for s in sentiment_counts.index])
        ax1.axis("equal")
        col1, col2 = st.columns([3, 2])
        with col1:
            st.pyplot(fig1)
        with col2:
            st.dataframe(sentiment_counts)

        st.subheader("Sentiment Count by Review Source")
        sentiment_by_source = pd.crosstab(filtered_df["Review Source"], filtered_df["Sentiment"])
        fig2, ax2 = plt.subplots(figsize=(6, 3))
        sentiment_by_source.plot(kind="barh", stacked=True, ax=ax2,
                                  color=[COLOR_MAP.get(s, "#CCCCCC") for s in sentiment_by_source.columns])
        st.pyplot(fig2)

    with tab2:
        st.subheader("Sentiment Over Time")
        df_time = filtered_df.copy()
        df_time["Published Date"] = pd.to_datetime(df_time["Published Date"])
        df_time["month_year"] = df_time["Published Date"].dt.to_period("M").astype(str)
        sentiment_over_time = pd.crosstab(df_time["month_year"], df_time["Sentiment"])
        fig3, ax3 = plt.subplots(figsize=(10, 4))
        sentiment_over_time.plot(kind="bar", stacked=True, ax=ax3,
                                  color=[COLOR_MAP.get(s, "#CCCCCC") for s in sentiment_over_time.columns])
        plt.xticks(rotation=45)
        st.pyplot(fig3)

    with tab3:
        st.subheader("Review Source Insights")
        source_counts = filtered_df["Review Source"].value_counts()
        fig4, ax4 = plt.subplots(figsize=(6, 3))
        source_counts.plot(kind="bar", ax=ax4)
        plt.xticks(rotation=45)
        st.pyplot(fig4)

        avg_confidence_by_source = filtered_df.groupby("Review Source")["Confidence"].mean().sort_values()
        fig5, ax5 = plt.subplots(figsize=(6, 3))
        avg_confidence_by_source.plot(kind="barh", ax=ax5)
        st.pyplot(fig5)

    with tab4:
        st.subheader("Tag Distribution")
        tag_counts = filtered_df.loc[filtered_df["Tag"] != "N/A", "Tag"].value_counts()
        if tag_counts.empty:
            st.info("No tags available. Enable tag generation before running analysis.")
        else:
            fig6, ax6 = plt.subplots(figsize=(6, 4))
            tag_counts.plot(kind="bar", ax=ax6)
            plt.xticks(rotation=45)
            st.pyplot(fig6)

    with tab5:
        weights = {"POSITIVE": 1, "NEUTRAL": 0, "NEGATIVE": -1, "N/A": 0}
        scored = filtered_df.copy()
        scored["combined_score"] = scored["Confidence"] * scored["Sentiment"].map(weights).fillna(0)

        st.subheader("Top Positive Reviews")
        for _, row in scored.nlargest(5, "combined_score").iterrows():
            with st.expander(f"{row['Review Source']} — {row['Tag']} (Score: {row['combined_score']:.2f})"):
                st.markdown(f"**Summary:** {row['Review Summary']}")
                st.markdown(f"**AI Recommendation:** {row['AI Recommendation']}")

        st.subheader("Top Negative Reviews")
        for _, row in scored.nsmallest(5, "combined_score").iterrows():
            with st.expander(f"{row['Review Source']} — {row['Tag']} (Score: {row['combined_score']:.2f})"):
                st.markdown(f"**Summary:** {row['Review Summary']}")
                st.markdown(f"**AI Recommendation:** {row['AI Recommendation']}")

        st.subheader("Final Comprehensive Summary")
        if st.button("Generate Final Summary"):
            with st.spinner("Generating final comprehensive summary..."):
                st.session_state.final_summary = generate_final_summary(processed_df)
        if st.session_state.final_summary:
            st.write(st.session_state.final_summary)
