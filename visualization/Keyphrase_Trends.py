import streamlit as st
import boto3
import pandas as pd
from collections import Counter
from decimal import Decimal
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# Page setup
st.set_page_config(page_title="Key Phrase Trends", layout="wide")
st.title("🔑 Key Phrase Trends")

# Connect to DynamoDB (NoSQL Sever) to extract data
dynamodb = boto3.resource("dynamodb", region_name="us-east-2")
table = dynamodb.Table("KeyPhraseIdentificationTableV2")

@st.cache_data(ttl=300)
def fetch_keyphrase_data():
    response = table.scan()
    items = response.get("Items", [])
    for item in items:
        for key, value in item.items():
            if isinstance(value, Decimal):
                item[key] = float(value)
    return pd.DataFrame(items)

# Load data
df = fetch_keyphrase_data()
if df.empty:
    st.warning("No data available.")
    st.stop()

# Convert to datetime
df["created_utc"] = pd.to_datetime(df["created_utc"], unit="s")

# Timeframe filter and Phrase selection inline
st.markdown("<style>.stColumns { align-items: end; }</style>", unsafe_allow_html=True)
col1, col2 = st.columns(2)

# Timeframe dropdown
with col1:
    time_options = {
        "Last 7 Days": pd.Timedelta(days=7),
        "Last 30 Days": pd.Timedelta(days=30),
        "Last 90 Days": pd.Timedelta(days=90)
    }
    selected_time = st.selectbox("Select Time Range", list(time_options.keys()), index=1)
now = pd.Timestamp.utcnow().replace(tzinfo=None)
df = df[df["created_utc"] >= now - time_options[selected_time]]

st.markdown(f"**{len(df)} records** in selected time range.")

# Extract and count phrases
phrases = []
for row in df["key_phrases"]:
    if isinstance(row, list):
        phrases.extend(row)

phrase_counts = Counter(phrases)
top_phrases = [phrase for phrase, _ in phrase_counts.most_common(5)]
phrase_counts_dict = dict(Counter(phrases))

# Map display labels
display_to_actual = {f"{p} ({phrase_counts_dict[p]})": p for p in sorted(phrase_counts_dict)}
all_unique_display_phrases = list(display_to_actual.keys())

# Phrase multiselect (top 5 default)
with col2:
    default_labels = [label for label, actual in display_to_actual.items() if actual in top_phrases]
    selected_labels = st.multiselect("Select Up to 5 Key Phrases to Compare", options=all_unique_display_phrases, default=default_labels, max_selections=5)
    selected_phrases = [display_to_actual[label] for label in selected_labels]

# Stop if none selected
if not selected_phrases:
    st.info("Please select at least one key phrase to display.")
    st.stop()

# Prepare and filter data
df["count"] = 1
df_expanded = df.explode("key_phrases")
df_filtered = df_expanded[df_expanded["key_phrases"].isin(selected_phrases)]

# Bar chart
phrase_counts = Counter(df_filtered["key_phrases"])
top_counts = dict(phrase_counts.most_common())

fig, ax = plt.subplots(figsize=(10, 5))
colors = plt.cm.tab20.colors
phrases = list(top_counts.keys())
counts = list(top_counts.values())

ax.bar(phrases, counts, color=colors[:len(phrases)])
ax.set_title("Top Key Phrases")
ax.set_ylabel("Mentions")
ax.set_xticklabels(phrases, rotation=20)
ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
st.pyplot(fig)

# Table posts
st.subheader("📝 Posts Containing Selected Key Phrases")
st.dataframe(df_filtered[["title", "key_phrases", "sentiment", "created_utc"]].sort_values("created_utc", ascending=False))