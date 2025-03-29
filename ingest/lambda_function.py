import praw
import boto3
import json
from datetime import datetime, timezone

# Reddit API Credentials (Insert Your Credentials Here)
reddit = praw.Reddit(
    client_id="client_id...",
    client_secret="client_secret...",
    user_agent="DashboardName by U/Username",
    username="Username...",
    password="Password..."
)

# AWS S3 setup (assumes IAM role has permissions)
s3 = boto3.client("s3")
bucket_name = "reddit-sentiment-dashboard-2025"

def lambda_handler(event, context):
    posts = []
    
    # Grab front page or use specific subreddit if needed
    for submission in reddit.front.hot(limit=10):
        posts.append({
            'title': submission.title,
            'score': submission.score,
            'url': submission.url,
            'num_comments': submission.num_comments,
            'created_utc': submission.created_utc,
            'subreddit': submission.subreddit.display_name
        })

    # Convert to JSON
    json_data = json.dumps(posts, indent=2)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"raw_reddit_{timestamp}.json"

    # Upload to S3
    s3.put_object(Bucket=bucket_name, Key=filename, Body=json_data)

    return {
        'statusCode': 200,
        'body': f"✅ Uploaded {filename} to {bucket_name}"
    }
print("good")