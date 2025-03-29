import streamlit as st
import boto3
import pandas as pd
from decimal import Decimal
from collections import Counter
import requests
import time
import os

def animated_typing(text, delay=0.0045):
    container = st.empty()
    typed = ""
    for char in text:
        typed += char
        container.markdown(f"\U0001F4CB **Generated Summary**\n\n{typed}")
        time.sleep(delay)

# Set Page Titile
st.set_page_config(page_title="Weekly Summary", layout="wide")

# Timeframe and UI state setup
timeframe_placeholder = st.empty()

if "timeframe" not in st.session_state:
    st.session_state.timeframe = "Last 7 Days"

if "previous_timeframe" not in st.session_state:
    st.session_state.previous_timeframe = st.session_state.timeframe

if "summary" not in st.session_state:
    st.session_state.summary = None

# Timeframe selection logic
with timeframe_placeholder:
    selected = st.selectbox(
        "Select Time Range",
        ["Last 7 Days", "Last 30 Days", "Last 90 Days"],
        index=["Last 7 Days", "Last 30 Days", "Last 90 Days"].index(st.session_state.timeframe)
    )

if selected != st.session_state.timeframe:
    st.session_state.previous_timeframe = st.session_state.timeframe
    st.session_state.timeframe = selected
    st.session_state.summary = None

# Assign final timeframe to use
timeframe = st.session_state.timeframe

title_map = {
    "Last 7 Days": "📝 Weekly Reddit Summary",
    "Last 30 Days": "📅 Monthly Reddit Summary",
    "Last 90 Days": "📊 Quarterly Reddit Summary"
}

st.subheader(title_map[timeframe])

# Connect to DynamoDB (NoSQL Sever) to extract data
dynamodb = boto3.resource("dynamodb", region_name="us-east-2")
post_table = dynamodb.Table("RedditPosts")
phrase_table = dynamodb.Table("KeyPhraseIdentificationTableV2")

@st.cache_data(ttl=300)
def fetch_data():
    post_resp = post_table.scan()
    phrase_resp = phrase_table.scan()

    post_items = post_resp.get("Items", [])
    phrase_items = phrase_resp.get("Items", [])

    for item in post_items:
        for k, v in item.items():
            if isinstance(v, Decimal):
                item[k] = float(v)
    for item in phrase_items:
        for k, v in item.items():
            if isinstance(v, Decimal):
                item[k] = float(v)

    post_df = pd.DataFrame(post_items)
    phrase_df = pd.DataFrame(phrase_items)

    if not post_df.empty:
        post_df["created_utc"] = pd.to_datetime(post_df["created_utc"], unit="s")
    if not phrase_df.empty:
        phrase_df["created_utc"] = pd.to_datetime(phrase_df["created_utc"], unit="s")

    return post_df, phrase_df

# Load data
post_df, phrase_df = fetch_data()
if post_df.empty or phrase_df.empty:
    st.warning("Not enough data available to summarize.")
    st.stop()

days = {"Last 7 Days": 7, "Last 30 Days": 30, "Last 90 Days": 90}[timeframe]
summary_type = {7: "weekly", 30: "monthly", 90: "quarterly"}.get(days, "summary")
period_noun = {"weekly": "this week", "monthly": "this month", "quarterly": "this quarter"}[summary_type]

cutoff = (pd.Timestamp.utcnow() - pd.Timedelta(days=days)).replace(tzinfo=None)

filtered_posts = post_df[post_df["created_utc"] >= cutoff]
filtered_phrases = phrase_df[phrase_df["created_utc"] >= cutoff]

# Top subreddits
top_subs = filtered_posts["subreddit"].value_counts().head(5).to_dict()
top_subs_str = ", ".join([f"r/{sub} ({count} posts)" for sub, count in top_subs.items()])

# Sentiment breakdown
sentiment_summary = filtered_posts.groupby("subreddit")[["positive_sentiment", "neutral_sentiment", "negative_sentiment"]].mean()
sentiment_lines = [
    f"r/{sub}: \ud83d\udc4d {row['positive_sentiment']:.2f}, \ud83d\ude10 {row['neutral_sentiment']:.2f}, \ud83d\udc4e {row['negative_sentiment']:.2f}"
    for sub, row in sentiment_summary.iterrows()
]
sentiment_str = "\n".join(sentiment_lines)

# Top key phrases
all_phrases = []
for row in filtered_phrases["key_phrases"]:
    if isinstance(row, list):
        all_phrases.extend(row)
phrase_counts = Counter(all_phrases)
top_phrases = [f"{p} ({c})" for p, c in phrase_counts.most_common(10)]
top_phrases_str = ", ".join(top_phrases)

# Top post by comments
top_comment_post = filtered_posts.loc[filtered_posts["num_comments"].idxmax()]
top_comment_line = f"The post with the most comments was from r/{top_comment_post['subreddit']}, discussing {top_comment_post['title']}, which garnered {int(top_comment_post['num_comments'])} comments."

# Top post by score
top_score_post = filtered_posts.loc[filtered_posts["score"].idxmax()]
top_score_line = f"A post from r/{top_score_post['subreddit']} about {top_score_post['title']} reached {int(top_score_post['score'])} upvotes."

# Prompt for GPT4
dynamic_prompt = f"""
You are an intelligent summarization model. Write a short, clear, insightful {summary_type} summary of Reddit activity based on this data:

- Time period: Last {days} days
- Top subreddits: {top_subs_str}
- Trending key phrases: {top_phrases_str}
- Average sentiment per subreddit:
{sentiment_str}
- Post with most comments: \"{top_comment_post['title']}\" from r/{top_comment_post['subreddit']} ({int(top_comment_post['num_comments'])} comments)
- Post with highest score: \"{top_score_post['title']}\" from r/{top_score_post['subreddit']} ({int(top_score_post['score'])} upvotes)

Give a concise bullet point summary highlighting interesting insights and patterns. Keep it around 10 bullets or less.
Depending on the amount of days 7, 30, 90, use langaguge to match it. As in 7 days is a week, 30 is a month, 90 is quarterly
"""

OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

def generate_summary(text):
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": text}],
        "max_tokens": 500,
        "temperature": 0.7
    }

    response = requests.post(OPENAI_API_URL, headers=headers, json=payload)

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f"\u274c Error: {response.status_code} - {response.text}"

# Generate summary if it's not cached
if st.session_state.summary is None:
    with st.spinner("🌀 Analysing Reddit data and generating your summary..."):
        st.session_state.summary = generate_summary(dynamic_prompt)

# Show Summary
animated_typing(st.session_state.summary)

# Regenerate Button
if st.button("🔁 Regenerate Summary"):
    st.session_state.summary = None
    st.rerun()

st.markdown("✨ Powered by [OpenAI GPT-4o-mini](https://platform.openai.com/)")
