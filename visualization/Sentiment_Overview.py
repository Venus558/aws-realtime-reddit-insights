import streamlit as st
import boto3
import pandas as pd
import matplotlib.pyplot as plt
from decimal import Decimal

# Set Streamlit page config
st.set_page_config(page_title="Reddit Sentiment Dashboard", layout="wide")

# Title
st.title("📊 Reddit Sentiment Dashboard (DynamoDB)")

# Initialize DynamoDB resource
dynamodb = boto3.resource("dynamodb", region_name="us-east-2")
table = dynamodb.Table("RedditPosts")

# Fetch all items from the table
@st.cache_data(ttl=300)
def fetch_data():
    response = table.scan()
    items = response.get("Items", [])

    # Convert Decimal to float
    for item in items:
        for key, value in item.items():
            if isinstance(value, Decimal):
                item[key] = float(value)

    return pd.DataFrame(items)

# Load data
df = fetch_data()

# Check if there's data
if df.empty:
    st.warning("No data found in the table.")
else:
    # Convert created_utc to datetime
    df["created_utc"] = pd.to_datetime(df["created_utc"], unit="s")

    # === Time Range Filter ===
    time_options = {
        "Last 4 Hours": pd.Timedelta(hours=4),
        "Last 24 Hours": pd.Timedelta(days=1),
        "Last 7 Days": pd.Timedelta(days=7),
        "Last 30 Days": pd.Timedelta(days=30),
        "All Time": None
    }

    default_index = list(time_options.keys()).index("Last 7 Days")
    selected_timeframe = st.selectbox("Select Time Range", list(time_options.keys()), index=default_index)

    now = pd.Timestamp.utcnow().replace(tzinfo=None)
    if time_options[selected_timeframe] is not None:
        df = df[df["created_utc"] >= now - time_options[selected_timeframe]]

    st.markdown(f"**{len(df)} posts** in selected time range.")

    # Sentiment Overview Chart
    st.subheader("Sentiment Overview")

    fig, ax = plt.subplots(figsize=(10, 5))
    sentiment_means = df[["positive_sentiment", "neutral_sentiment", "negative_sentiment"]].mean()
    sentiment_means.index = ["Positive", "Neutral", "Negative"]
    sentiment_means.plot(kind="bar", ax=ax, color=["green", "royalblue", "red"])
    ax.set_title("Average Sentiment Scores")
    ax.set_ylabel("Score")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=20)
    st.pyplot(fig)

    subreddits = sorted(df["subreddit"].unique())
    subreddits.insert(0, "All")  # Add "All" to the top

    selected_sub = st.selectbox("Choose a Subreddit", subreddits, index=0)

    if selected_sub != "All":
        filtered_df = df[df["subreddit"] == selected_sub]
    else:
        filtered_df = df
    st.markdown(f"**{len(filtered_df)} posts from r/{selected_sub}**")
    st.dataframe(filtered_df[["title", "score", "num_comments", "compound_sentiment"]])
