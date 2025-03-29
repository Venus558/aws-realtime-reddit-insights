# AI-Powered Reddit Analysis

## Overview
**This project leverages the power of AWS and AI to deliver real-time Reddit insights**. **Using GPT-4** for **advanced natural language analysis and AWS services like Lambda, S3, DynamoDB, and EventBridge** for scalable, serverless architecture, it continuously ingests Reddit data, detects trends, sentiment, and engagement, and presents it all through an interactive Streamlit dashboard.

## Features
- Real-time Reddit ingestion via the Reddit API (PRAW)
- Serverless architecture using **AWS Lambda (multiple functions), EventBridge triggers, S3 buckets, and DynamoDB tables**
- **Natural Language Processing** and **AI summarization** using **OpenAI’s GPT-4**
- Dynamic, interactive dashboards for visualizing subreddit trends, sentiment, and activity at [brendandidier.com](https://brendandidier.com)
- **Ongoing ingestion**: the NoSQL database is being populated continuously with Reddit front-page posts and grows every day
- The entire pipeline runs in the **cloud** — from AWS Lambda ingestion to a live dashboard hosted on a **cloud-based VPS** — allowing the project to **continuously update, process, and serve real-time** Reddit insights with zero manual intervention.

## Tech Stack

**Frontend**: **Streamlit** (deployed via self-hosted VPS for full control and flexibility)

**Backend**: **AWS Lambda (Python)** functions triggered by **EventBridge** for **real-time ingestion and processing**, plus a custom-configured **VPS (cPanel/WHM)** for hosting and serving Streamlit apps with NGINX and reverse proxies

**Data Storage**: **DynamoDB (real-time NoSQL), S3** (raw JSON backups)

**AI/NLP**: **Native NLP processing (key phrase extraction, sentiment analysis)**, **OpenAI GPT-4** for intelligent summarization and insight generation

**Others**: PRAW (Reddit API), Matplotlib, Boto3, Python

## Installation

**Requirements**:
- A Reddit account and API credentials for data ingestion via PRAW (insert into `ingest/lambda_function.py` or wherever used)
- An AWS account with configured credentials to use Lambda, S3, DynamoDB, and EventBridge
- An OpenAI API key for summarization

```bash
git clone https://github.com/Venus558/aws-realtime-reddit-insights.git
cd aws-realtime-reddit-insights
pip install -r requirements.txt
```

Create a `.streamlit/secrets.toml` file with your OpenAI key:

```toml
OPENAI_API_KEY = "your-openai-key"
```

## Running the App

```bash
streamlit run visualization/Home.py
```

**Other Dashboard Pages**:
- `Weekly_Summary.py`
- `Keyphrase_Trends.py`
- `Subreddit_Insights.py`
- `Sentiment_Overview.py`

## Dashboard Pages

| Page                | Description                                                                 |
|---------------------|-----------------------------------------------------------------------------|
| Weekly Summary      | AI-powered bullet point summaries of Reddit activity with GPT-generated insights |
| Keyphrase Trends    | Real-time keyphrase tracking and side-by-side comparison                     |
| Subreddit Insights  | Compare subreddit sentiment, score, comments, and post volume                |
| Sentiment Overview  | Aggregated sentiment breakdown by subreddit                                 |

## Architecture

```
Reddit API → AWS Lambda → S3 / DynamoDB → Streamlit Dashboards (Self-hosted VPS)
                                 ↓
                          OpenAI GPT-4 API (on-demand)
```

- Fully modular and serverless backend
- Streamlit frontend runs on a secure, self-hosted VPS
- Data flows from Reddit ingestion to real-time rendering with no manual steps

## Example Use

You can take a look at the live project at [brendandidier.com](https://brendandidier.com))

## License

MIT License
