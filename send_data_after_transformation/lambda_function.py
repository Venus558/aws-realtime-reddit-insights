import json
import boto3
from decimal import Decimal

# Initialize boto3 clients for S3, DynamoDB, and Comprehend
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
comprehend = boto3.client('comprehend')  # === NEW SECTION ===

# Reference the primary DynamoDB table
table = dynamodb.Table('RedditPosts')

# Reference the NEW DynamoDB table for key phrases and sentiment
keyphrase_table = dynamodb.Table('KeyPhraseIdentificationTableV2')  # === NEW SECTION ===

def lambda_handler(event, context):
    # The bucket name where your processed files are stored
    bucket_name = 'reddit-sentiment-dashboard-2025'
    folder_prefix = 'processed/'

    # List objects in the 'processed' folder
    try:
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix=folder_prefix)
        files = response.get('Contents', [])
        if not files:
            print("No files found to process.")
            return {
                'statusCode': 200,
                'body': json.dumps("No files found to process.")
            }
    except Exception as e:
        print(f"Error listing objects in S3: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error listing objects in S3: {str(e)}")
        }

    # Loop through the files and process them
    for file in files:
        file_key = file['Key']
        print(f"Processing file {file_key}")

        # Read the file's metadata to check if 'status' is set to 'done'
        try:
            response = s3.head_object(Bucket=bucket_name, Key=file_key)
            metadata = response.get('Metadata', {})
            if metadata.get('status') == 'done':
                print(f"File {file_key} has already been processed. Skipping.")
                continue  # Skip this file if already marked as done
        except Exception as e:
            print(f"Error reading metadata for {file_key}: {str(e)}")
            continue  # Skip this file if we can't read metadata

        # Read the JSON file from S3 if not marked as done
        try:
            response = s3.get_object(Bucket=bucket_name, Key=file_key)
            file_data = json.loads(response['Body'].read())
            print(f"Read {len(file_data)} records from {file_key}.")
        except Exception as e:
            print(f"Error reading file {file_key}: {str(e)}")
            continue  # Skip this file if there is an error reading it

        # Loop through the data and insert it into DynamoDB
        for post in file_data:
            # Log the item before inserting into DynamoDB
            if 'title' not in post or 'created_utc' not in post:
                print(f"Missing 'title' or 'created_utc' in post: {post}")
                continue  # Skip this post if it's missing required fields

            # === ORIGINAL SECTION: insert into RedditPosts table ===
            item = {
                'title': post['title'],  # Partition Key
                'created_utc': Decimal(str(post['created_utc'])),  # Sort Key
                'score': Decimal(str(post['score'])),
                'num_comments': Decimal(str(post['num_comments'])),
                'subreddit': post['subreddit'],
                'url': post['url'],
                'positive_sentiment': Decimal(str(post.get('pos', 0.0))),
                'neutral_sentiment': Decimal(str(post.get('neu', 0.0))),
                'negative_sentiment': Decimal(str(post.get('neg', 0.0))),
                'compound_sentiment': Decimal(str(post.get('compound', 0.0))),
            }

            print(f"Inserting item into DynamoDB: {item}")

            try:
                response = table.put_item(Item=item)
                print(f"Inserted post with title '{post['title']}' into RedditPosts")
            except Exception as e:
                print(f"Error inserting item into RedditPosts table: {str(e)}")
                continue

            # === NEW SECTION: Extract key phrases and sentiment with Comprehend ===
            try:
                title = post['title'].strip()
                utc = int(post['created_utc'])

                # 1. Key Phrase Extraction
                kp_response = comprehend.detect_key_phrases(Text=title, LanguageCode='en')
                key_phrases = [kp['Text'] for kp in kp_response['KeyPhrases']]

                # 2. Sentiment Detection
                sentiment_response = comprehend.detect_sentiment(Text=title, LanguageCode='en')
                sentiment = sentiment_response.get('Sentiment', 'NEUTRAL')

                # 4. Write to separate DynamoDB table
                keyphrase_table.put_item(Item={
                    'post_id': title,
                    'created_utc': utc,
                    'title': title,
                    'key_phrases': key_phrases,
                    'sentiment': sentiment
                })

                print(f"Inserted key phrases and sentiment for '{title}' into KeyPhraseIdentificationTable")

            except Exception as e:
                print(f"Error extracting/storing key phrases or sentiment for post '{title}': {str(e)}")

        # After processing, update the metadata to mark the file as 'done'
        try:
            s3.copy_object(
                Bucket=bucket_name,
                CopySource={'Bucket': bucket_name, 'Key': file_key},
                Key=file_key,
                Metadata={'status': 'done'},
                MetadataDirective='REPLACE'
            )
            print(f"Updated metadata for {file_key} to 'status: done'")
        except Exception as e:
            print(f"Error updating metadata for {file_key}: {str(e)}")
            continue

    return {
        'statusCode': 200,
        'body': json.dumps("Successfully processed all files.")
    }
