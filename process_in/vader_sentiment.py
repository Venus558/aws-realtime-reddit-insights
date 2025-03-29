from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Function to initialize the sentiment analyzer
def analyze_sentiment(text):
    analyzer = SentimentIntensityAnalyzer()
    sentiment = analyzer.polarity_scores(text)
    
    # Returning the sentiment scores
    return sentiment
