import streamlit as st
import boto3
import pandas as pd
from collections import Counter
from decimal import Decimal
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# Page setup
st.set_page_config(page_title="Subreddit Insights", layout="wide")
st.title("📚 Subreddit Insights")

# Connect to DynamoDB (NoSQL Sever) to extract data
dynamodb = boto3.resource("dynamodb", region_name="us-east-2")
table = dynamodb.Table("RedditPosts")

@st.cache_data(ttl=300)
def fetch_post_data():
    response = table.scan()
    items = response.get("Items", [])
    for item in items:
        for key, value in item.items():
            if isinstance(value, Decimal):
                item[key] = float(value)
    return pd.DataFrame(items)

# Load data
df = fetch_post_data()
if df.empty:
    st.warning("No data available.")
    st.stop()

# Convert timestamps
df["created_utc"] = pd.to_datetime(df["created_utc"], unit="s")

# Layout for controls
col1, col2 = st.columns(2)

# Timeframe filter (left)
time_options = {
    "Last 7 Days": pd.Timedelta(days=7),
    "Last 30 Days": pd.Timedelta(days=30),
    "Last 90 Days": pd.Timedelta(days=90)
}
with col1:
    selected_time = st.selectbox("Select Time Range", list(time_options.keys()), index=1)
now = pd.Timestamp.utcnow().replace(tzinfo=None)
df = df[df["created_utc"] >= now - time_options[selected_time]]

# Auto-select top 5 subreddits by specific criteria
sentiment_avgs = df.groupby("subreddit")[["positive_sentiment", "negative_sentiment"]].mean()
most_positive = sentiment_avgs["positive_sentiment"].idxmax()
most_negative = sentiment_avgs["negative_sentiment"].idxmax()
most_posts = df["subreddit"].value_counts().idxmax()
most_score = df.groupby("subreddit")["score"].sum().idxmax()
most_comments = df.groupby("subreddit")["num_comments"].sum().idxmax()

auto_selected_subs = list(dict.fromkeys([most_positive, most_negative, most_posts, most_score, most_comments]))

# Subreddit selector (right)
with col2:
    selected_subs = st.multiselect(
        "Select Up to 5 Subreddits to Compare",
        sorted(df["subreddit"].unique()),
        default=auto_selected_subs,
        max_selections=5
    )

# Filter data
df_filtered = df[df["subreddit"].isin(selected_subs)]
if df_filtered.empty:
    st.info("No data for selected subreddits.")
    st.stop()

st.markdown(f"**{len(df_filtered)} posts** across selected subreddits.")

# Sentiment comparison
st.subheader("📊 Average Sentiment by Subreddit")
metrics_df = df_filtered.groupby("subreddit").agg({
    "positive_sentiment": "mean",
    "neutral_sentiment": "mean",
    "negative_sentiment": "mean"
})

fig, ax = plt.subplots(figsize=(12, 6))
metrics_df.plot(kind="bar", ax=ax, color=["green", "steelblue", "red"])
ax.set_ylabel("Sentiment Score")
ax.set_title("Average Sentiment Scores by Subreddit")
ax.set_xticklabels(metrics_df.index, rotation=20)

st.pyplot(fig)

# Top posts table
st.subheader("🔥 Top Posts by Score")
top_posts = df_filtered.sort_values("score", ascending=False).head(10)
st.dataframe(top_posts[["subreddit", "title", "score", "num_comments", "compound_sentiment"]])
