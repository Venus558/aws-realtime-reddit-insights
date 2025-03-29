import json
import boto3
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from datetime import datetime

# Create a boto3 S3 client
s3 = boto3.client('s3')

# Set your bucket name
BUCKET_NAME = "reddit-sentiment-dashboard-2025"

def lambda_handler(event, context):
    # Initialize the VADER Sentiment analyzer
    analyzer = SentimentIntensityAnalyzer()

    # 1. List objects in the S3 bucket (raw data)
    response = s3.list_objects_v2(Bucket=BUCKET_NAME)
    files = [obj['Key'] for obj in response.get('Contents', []) if obj['Key'].endswith('.json') and 'processed' not in obj['Key']]

    if not files:
        return {"statusCode": 404, "body": "No files found in S3"}

    for filename in files:
        print(f"📥 Processing: {filename}")
        
        # 2. Get the object and check metadata
        obj = s3.get_object(Bucket=BUCKET_NAME, Key=filename)
        metadata = obj.get('Metadata', {})
        
        # Check if the file has already been processed using metadata
        if metadata.get('processed', 'false') == 'true':
            print(f"⚠️ Skipping already processed file: {filename}")
            continue
        
        # Read the raw data
        raw_data = json.loads(obj['Body'].read())

        processed = []
        for post in raw_data:
            # Analyze sentiment using VADER
            sentiment = analyzer.polarity_scores(post['title'])
            post.update(sentiment)
            processed.append(post)

        # 3. Save the processed sentiment results to S3 under /processed/
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        new_key = f"processed/reddit_sentiment_{timestamp}.json"

        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=new_key,
            Body=json.dumps(processed, indent=2),
            Metadata={'processed': 'true'}  # Add metadata here
        )

        # After processing, update the metadata of the original file
        s3.copy_object(
            Bucket=BUCKET_NAME,
            CopySource={'Bucket': BUCKET_NAME, 'Key': filename},
            Key=filename,
            Metadata={'processed': 'true'},
            MetadataDirective='REPLACE'  # This tells S3 to replace the metadata
        )

        print(f"✅ Saved {len(processed)} posts → {new_key}")
        
    return {
        "statusCode": 200,
        "body": f"Processed {len(files)} file(s) and saved sentiment results"
    }
