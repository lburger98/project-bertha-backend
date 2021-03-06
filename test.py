#!/usr/bin/python3
from nltk.corpus import twitter_samples, stopwords
from nltk.tokenize import TweetTokenizer
from nltk.stem import PorterStemmer
from nltk import classify
from nltk import NaiveBayesClassifier
import logging
import tweepy 
import os
import sys
import re
import string
from random import shuffle 
from collections import defaultdict

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# analyzer = SentimentIntensityAnalyzer()

#Twitter API credentials
consumer_key = 'pf14xpY1B4OS6p5NhVvKRDraQ'
consumer_secret = 'mMVDAiMsrTfRqcZjDpUjEV6TMh0qOYhZeUOT6UQH6EcQUKvlKl'
access_key = '634780289-kQIogwhtHfQIhogOfV7meFIJrf2DPGLEhsSlF94m'
access_secret = 'EitrLcZkkZ1FfgTtroB6ETAbalmg7Iul4lAmcPBkucd9m'

tweet_tokenizer = TweetTokenizer(preserve_case=False, strip_handles=True, reduce_len=True)
stemmer = PorterStemmer()

stopwords_english = stopwords.words('english')
pos_tweetss = twitter_samples.strings('positive_tweets.json')
neg_tweetss = twitter_samples.strings('negative_tweets.json')

political_words = defaultdict(str)
sports_words = defaultdict(str)
technology_words = defaultdict(str)
art_words = defaultdict(str)

for line in open('./topics/political.txt'):
    political_words[line.strip().lower()] = True

for line in open('./topics/sports.txt'):
    sports_words[line.strip().lower()] = True

for line in open('./topics/technology.txt'):
    technology_words[line.strip().lower()] = True

for line in open('./topics/art.txt'):
    art_words[line.strip().lower()] = True


# Happy Emoticons
emoticons_happy = set([
    ':-)', ':)', ';)', ':o)', ':]', ':3', ':c)', ':>', '=]', '8)', '=)', ':}',
    ':^)', ':-D', ':D', '8-D', '8D', 'x-D', 'xD', 'X-D', 'XD', '=-D', '=D',
    '=-3', '=3', ':-))', ":'-)", ":')", ':*', ':^*', '>:P', ':-P', ':P', 'X-P',
    'x-p', 'xp', 'XP', ':-p', ':p', '=p', ':-b', ':b', '>:)', '>;)', '>:-)',
    '<3'
    ])
 
# Sad Emoticons
emoticons_sad = set([
    ':L', ':-/', '>:/', ':S', '>:[', ':@', ':-(', ':[', ':-||', '=L', ':<',
    ':-[', ':-<', '=\\', '=/', '>:(', ':(', '>.<', ":'-(", ":'(", ':\\', ':-c',
    ':c', ':{', '>:\\', ';('
    ])
 
# all emoticons (happy + sad)
emoticons = emoticons_happy.union(emoticons_sad)
 
def clean_tweets(tweet):
    # remove stock market tickers like $GE
    tweet = re.sub(r'\$\w*', '', tweet)
 
    # remove old style retweet text "RT"
    tweet = re.sub(r'^RT[\s]+', '', tweet)
 
    # remove hyperlinks
    tweet = re.sub(r'https?:\/\/.*[\r\n]*', '', tweet)
    
    # remove hashtags
    # only removing the hash # sign from the word
    tweet = re.sub(r'#', '', tweet)
 
    # tokenize tweets
    tokenizer = TweetTokenizer(preserve_case=False, strip_handles=True, reduce_len=True)
    tweet_tokens = tokenizer.tokenize(tweet)
 
    tweets_clean = []    
    for word in tweet_tokens:
        if (word not in stopwords_english and # remove stopwords
              word not in emoticons and # remove emoticons
                word not in string.punctuation): # remove punctuation
            stem_word = stemmer.stem(word) # stemming word
            tweets_clean.append(stem_word)
 
    return tweets_clean

def bag_of_words(tweet):
    words = clean_tweets(tweet)
    words_dictionary = dict([word, True] for word in words)
    return words_dictionary

def classify_topic(tweet):
    words = clean_tweets(tweet)

    num_political = 0
    num_sports = 0
    num_tech = 0
      
    for word in words:
        word = word.lower()
        # if word == 'tesla':
        #     print word

        if (political_words[word]):
            num_political += 1

        if (sports_words[word]):
            num_sports += 1

        if (technology_words[word]):
            num_tech += 1

    # max_val = max(num_political, num_sports, num_tech)
    # if max_val == 0:
    #     return "none"

    # if max_val == num_political:
    #     return "political"
    # elif max_val == num_sports:
    #     return "sports"
    # elif max_val == num_tech:
    #     return "num_tech"

def get_all_tweets(screen_name, num_tweets):
    #Twitter only allows access to a users most recent 3240 tweets with this method
    
    #authorize twitter, initialize tweepy
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_key, access_secret)
    api = tweepy.API(auth)
    
    #initialize a list to hold all the tweepy Tweets
    alltweets = []  
    
    #make initial request for most recent tweets (200 is the maximum allowed count)
    new_tweets = api.user_timeline(screen_name = screen_name,count=200)
    
    #save most recent tweets
    alltweets.extend(new_tweets)
    
    #save the id of the oldest tweet less one
    oldest = alltweets[-1].id - 1
    count = 0
    #keep grabbing tweets until there are no tweets left to grab
    while len(new_tweets) > 0 and count <= int(num_tweets):
        count += 100
        #all subsiquent requests use the max_id param to prevent duplicates
        new_tweets = api.user_timeline(screen_name = screen_name,count=100,max_id=oldest)
        #save most recent tweets
        alltweets.extend(new_tweets)

        #update the id of the oldest tweet less one
        oldest = alltweets[-1].id - 1
        
    
    #transform the tweepy tweets into a 2D array that will populate the csv 
    outtweets = [[tweet.id_str, tweet.created_at.strftime('%m/%d/%Y'), tweet.text] for tweet in alltweets]

    return outtweets



username = "elonmusk"
num_tweets = 1000
tweets = get_all_tweets(username, num_tweets)

data = {}

time_series = []

num_pos = 0
num_neg = 0
num_neu = 0
max_pos = 0
max_neg = 0

num_political = 0
num_sports = 0
num_tech = 0
num_art = 0

pos_tweets = []
neg_tweets = []

# sentiment_tweets = []
for tweet in tweets:
    # tweet_words = bag_of_words(tweet[2])
    # topic = classify_topic(tweet[2])
    words = clean_tweets(tweet[2])
      
    for word in words:
        word = word.lower()

        if (political_words[word]):
            num_political += 1

        if (sports_words[word]):
            num_sports += 1
            
        if (technology_words[word]):
            num_tech += 1

        if (art_words[word]):
            num_art += 1


    # if topic == "political":
    #     num_political += 1
    # elif topic == "sports":
    #     num_sports += 1
    # elif topic == "tech":
    #     num_tech += 1

    # prob_result = analyzer.polarity_scores(tweet[2])

    new_data = {}

    new_data['time'] = tweet[1]
    new_data['text'] = tweet[2]

    # if prob_result['compound'] >= 0.1:
    #     pos_tweets.append((tweet, prob_result['compound']))
    #     num_pos += 1
    # elif prob_result['compound'] <= -0.1: 
    #     neg_tweets.append((tweet, prob_result['compound']))
    #     num_neg += 1
    # else:
    #     num_neu += 1

    # if prob_result['compound'] > max_pos:
    #     max_pos = prob_result['compound']
    # elif prob_result['compound'] < max_neg:
    #     max_neg = prob_result['compound']

    # entry = {}
    # entry['time'] = tweet[1]
    # entry['score'] = prob_result['compound']
    # entry['pos'] = prob_result['pos']
    # entry['neg'] = prob_result['neg']
    # entry['neu'] = prob_result['neu']
    # time_series.append(entry)

# data['tweets'] = sentiment_tweets
data['time_series'] = time_series

data['num_pos'] = num_pos
data['num_neg'] = num_neg
data['num_neu'] = num_neu

# pos_tweets = sorted(pos_tweets, key=lambda k: k[1], reverse=True)[:6]
# pos_tweets, _ = zip(*pos_tweets)
# neg_tweets = sorted(neg_tweets, key=lambda k: k[1])[:6]
# neg_tweets, _ = zip(*neg_tweets)
# data['most_positive'] = pos_tweets
# data['most_negative'] = neg_tweets


print num_political, num_sports, num_tech