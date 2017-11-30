# -*- coding: utf-8 -*-

from flask import Flask
from flask import request
from flask import make_response
from newsapi.articles import Articles
from google.appengine.api import app_identity
from random import shuffle

import json
import logging as l
import random
import numpy as np
import os
import cloudstorage as gcs
import webapp2

app = Flask(__name__)

news_api_key = "663733985a214ef5aa4ee7372ab3e223"
bucket_name = "/sportsfeed-21790.appspot.com/{}.pro"

sports = np.array(['sports', 'warriors', 'minnisota fc', 'kings', 'orlando city', 'maple leafs', 'knicks', 'argonauts',
            'brewers', 'dodgers', 'grizzlies', 'toronto fc', '76ers', 'columbus crew', 'bulls', 'redskins', 'eskimos', 'magic',
            'sounders', 'tigers', 'pacers', 'sox', 'astros', 'union', 'rockies', 'timbers', 'coyotes', 'saints', 'wizards', 
            'heat', 'ducks', 'cowboys', 'mets', 'marlins', 'dolphins', 'rapids', 'lions', 'fire', 'predators', 'flames',
            'pistons', 'rockets', 'devils', 'blackhawks', 'suns', 'diamondbacks', 'sharks', 'golden knights', 'raiders', 
            'senators', 'revolution', 'mavericks', 'jackets', 'seahawks', 'mariners', 'ravens', 'browns', 'giants', 'lakers',
            'cubs', 'colts', 'angels', 'royals', 'la fc', 'eagles', 'rangers', 'padres', 'twins', 'galaxy', 'nationals',
            'chiefs', 'texans', 'alouettes', 'blue jays', 'rams', 'dynamo', 'pelicans', 'red bulls', 'thunder', 'falcons', 
            'timberwolves', 'redblacks', 'canadiens', 'bills', 'blue bombers', 'hawks', 'raptors', 'bears', 'packers', 
            'real salt lake', 'avalanche', 'patriots', 'bengals', 'jets', 'flyers', 'celtics', 'bruins', 'hornets', 'bucks', 
            'lightning', 'jazz', '49ers', 'buccaneers', 'cardinals', 'wild', 'tiger-cats', 'rays', 'orioles', 'vikings', 
            'hurricanes', 'white sox', 'penguins', 'panthers', 'impact', 'islanders', 'pirates', 'oilers', 'nyc fc', 
            'clippers', 'roughriders', 'yankees', 'indians', 'fc dallas', 'atlanta fc', 'phillies', 'nuggets', 'stars',
            'athletics', 'steelers', 'city', 'reds', 'braves', 'broncos', 'd.c. united', 'blues', 'jaguars', 'stampeders',
            'spurs', 'titans', 'nets', 'sabres', 'whitecaps', 'wings', 'trail blazers', 'canucks', 'earthquakes', 'cavaliers', 
            'gilmore', 'upton', 'sabathia', 'miller', 'love', 'kohli', 'fielder', 'ramirez', 'durant', 'batum', 'derozan', 
            'mauer', 'conley', 'reyes', 'murray', 'mcilroy', 'cox', 'irving', 'neymar', 'nadal', 'mcgregor', 'hamels', 'lillard',
            'aldridge', 'ellsbury', 'wilkerson', 'lopez', 'bolt', 'pujols', 'rose', 'pierre-paul', 'rooney', 'westbrook', 
            'vettel', 'whiteside', 'paul', 'george', 'kershaw', 'tanaka', 'decastro', 'newton', 'nishikori', 'brees', 
            'hamilton', 'johnson', 'gonzalez', 'nowitzki', 'kalil', 'williams', 'luck', 'drummond', 'messi', 'cabrera', 'wade', 
            'anthony', 'alvarez', 'federer', 'djokovic', 'ronaldo', 'woods', 'jordan', 'mickelson', 'horford', 'davis',
            'brown', 'berry', 'barnes', 'james', 'klitschko', 'bale', 'cano', 'rodriguez', 'hernandez', 'harden', 'joshua', 
            'alonso', 'beal', 'jones', 'suarez', 'parsons', 'posey', 'price', 'manning', 'spieth', 'kemp', 'perry', 'curry',
            'greinke', 'bosh', 'verlander', 'aguero', 'thompson', 'earnhardt', 'howard', 'gasol', 'ibrahimovic', 'griffin',
            'chargers', 'capitals', ])

politics = np.array(['politics', 'ten commandments', 'sales tax', 'affirmative action', 'campaign finance', 'bilingualism', 
            'medicare', 'medicaid', 'sdi missile defense', 'terrorism', 'patient rights', 'juvenile justice', 'litmus test', 
            'nafta', 'universal health care', 'politics', 'tort reform', 'vouchers', 'china', 'united nations',
            'global warming', 'privacy', 'faith-based organizations', 'drug war', 'israel', 'palestine', 'disabled rights', 
            'internet', 'veterans', 'cuba', 'flat tax', 'gay rights', 'kyoto treaty', 'balkans', 'foreign aid',
            'death penalty', 'three strikes', 'armed forces', 'urban issues', 'energy', 'mideast', 'sovereignty',
            'nuclear energy', 'weapons', 'tobacco', 'farm policy', 'illegal immigrants', 'privatization', 'second amendment', 
            'net neutrality', 'school prayer'])

def get_bucket():
    return os.environ.get('BUCKET_NAME', app_identity.get_default_gcs_bucket_name())
   
def create_file(filename, all_articles, article, profiles):
    """Create a file.

    The retry_params specified in the open call will override the default
    retry params for this particular file handle.

    Args:
      filename: filename.
    """

    out_string = '||'.join([','.join(['%.5f' % num for num in profile]) for profile in profiles])

    all_articles = [a.decode("utf-8") for a in all_articles]
    all_articles = "||".join(all_articles) + "\n"

    if len(article[1]) > 0:
        last_article = article[0] + "||" + article[1] + "\n"
    else:
        last_article = article[0] + "\n"
    
    gcs_file = gcs.open(filename, 'w')
    gcs_file.write(all_articles.encode('utf-8'))
    	
    if article[2] == 'sports':
        gcs_file.write('s: ')
    elif article[2] == 'politics':
        gcs_file.write('p: ')
    
    gcs_file.write(last_article.encode('utf-8'))

    gcs_file.write(out_string)
    gcs_file.close()

def read_file(filename):
    try:
        gcs_file = gcs.open(filename)
    except:
        return ([], "", [np.zeros(len(sports)), np.zeros(len(politics))])
        
    all_articles = str.encode(gcs_file.readline()).rstrip().split("||")
    last_article = str.encode(gcs_file.readline()).rstrip()

    text_profiles = str.encode(gcs_file.read())
    profiles = [np.fromstring(profile, sep=',') for profile in text_profiles.rstrip().split("||")]
    gcs_file.close()
    
    return (all_articles, last_article, profiles)
    
def remove_unicode_bs(s):
	return s.encode('ascii', 'ignore').decode('utf-8')

def get_news():
    a = Articles(API_KEY=news_api_key)
    
    news = []
    
    # retrieve sports news
    source_ids = ['espn', 'espn-cric-info', 'fox-sports', 'nfl-news']
    for source in source_ids:
        articles = a.get(source)["articles"]
        for article in articles:
            if not (article["title"] is None or article["description"] is None or len(article["title"]) == 0):
                news.append((remove_unicode_bs(article["title"]), remove_unicode_bs(article["description"]), "sports"))
    
    # retrieve political news
    articles = a.get("breitbart-news")["articles"]
    for article in articles:
        if not (article["title"] is None or article["description"] is None or len(article["title"]) == 0):
            news.append((remove_unicode_bs(article["title"]), remove_unicode_bs(article["description"]), "politics"))
    
    shuffle(news)
    
    return news
    
def process_articles(news):
    # create profiles for all of the articles gathered by the news api
    
    keep_chars = set('abcdefghijklmnopqrstuvwxyz ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    articles = []
    
    for article in news:
        # tokenize the words of the article
        words = set("".join(c for c in article[0].lower() + " " + article[1].lower() if c in keep_chars).split())
        genre = sports
        
        if article[2] == 'politics':
            genre = politics
            
        article_profile = np.zeros(len(genre))
        article_profile[0] += 0.1

        for i, topic in enumerate(genre):
            if topic in words:
                article_profile[i] += 1

        articles.append(article_profile)

    return articles

def get_similar_news(article_profiles, news, my_profile):
    distances = []

    for profile in article_profiles:
        cur_profile = my_profile[0].astype(float) if len(profile) == len(sports) else my_profile[1].astype(float)
        distances.append(np.dot(cur_profile, profile) / (np.linalg.norm(cur_profile) * np.linalg.norm(profile)))

    distances = np.nan_to_num(distances)
    closest_articles = np.argsort(distances)[::-1]
    
    return list(np.array(news)[closest_articles])
    
def contains(article, article_list):
    title = article[0].encode("utf-8")

    for a in article_list:
        if title == a[:len(title)]:
            return True
    return False
    
def describe_profile(profile):
    likes = list(sports[np.where(profile[0]>0, True, False)]) + list(politics[np.where(profile[1]>0, True, False)])
    dislikes = list(sports[np.where(profile[0]<0, True, False)]) + list(politics[np.where(profile[1]<0, True, False)])
    return (likes , dislikes)

def news_response(user_id):
    news = get_news()
    article_profiles = process_articles(news)
    (all_articles, last_article, user_profile) = read_file(bucket_name.format(user_id))

    ordered_news = get_similar_news(article_profiles, news, user_profile)
    ordered_news = [article for article in ordered_news if not contains(article, all_articles)]
	
    if len(ordered_news) > 0:
        i = min(len(ordered_news) - 1, int(np.random.exponential(5)))
        all_articles.append(ordered_news[i][0])
            
        create_file(bucket_name.format(user_id), all_articles, ordered_news[i], user_profile)

        return ordered_news[i][0] + "\nDo you like this article?"

    return "Sorry, no more news left."

def likes_article(user_id):
    l.info("in likes article")
    (all_articles, last_article, user_profile) = read_file(bucket_name.format(user_id))
    
    if len(last_article) > 0 and last_article[0] == "s":
    	genre = "sports"
    	genre_id = 0
    else:
    	genre = "politics"
    	genre_id = 1
    
    last_article = last_article[3:]
    article_profile = process_articles([(last_article, "", genre)])
    user_profile[genre_id] += article_profile[0]
    create_file(bucket_name.format(user_id), all_articles, (last_article, "", genre), user_profile)
    
    details = last_article.split("||")[-1]
    
    return "Nice! Updated results.\nMore details about the article: " + details

def dislikes_article(user_id):
    l.info("in dislikes article")
    (all_articles, last_article, user_profile) = read_file(bucket_name.format(user_id))
    
    if len(last_article) > 0 and last_article[0] == "s":
    	genre = "sports"
    	genre_id = 0
    else:
    	genre = "politics"
    	genre_id = 1
    
    last_article = last_article[3:]
    article_profile = process_articles([(last_article, "", genre)])
    user_profile[genre_id] -= article_profile[0]
    create_file(bucket_name.format(user_id), all_articles, (last_article, "", genre), user_profile)
    
    return "Sorry about that. Updated profile."

def reset(user_id):
    l.info("in reset")

    user_profile = [np.zeros(len(sports)), np.zeros(len(politics))] 
    create_file(bucket_name.format(user_id), [], ("","",""), user_profile) 
    
    return "Resetting user profile..."

def get_profile(user_id):
    l.info("in describe")
    (all_articles, last_article, user_profile) = read_file(bucket_name.format(user_id))

    (likes, dislikes) = describe_profile(user_profile)
    
    if len(likes) > 0 and len(dislikes) > 0:
        return "You like: " + ", ".join(likes) + ". You dislike: " + ", ".join(dislikes)
    elif len(likes) > 0:
        return "You like: " + ", ".join(likes)
    elif len(dislikes) > 0:
        return "You dislike: " + ", ".join(dislikes)
    else:
        return "You have no likes or dislikes."
        
@app.route('/')
def hello():
    return 'Hello World!\n'

@app.route('/webhook', methods=['POST'])
def apiai_response():
    req = request.get_json(silent=True, force=True)

    try:
        user_id = req.get("originalRequest").get("data").get("user").get("userId")
    except:
        user_id = "guest"
    
    speech = "updated results"
    if req.get("result").get("action") == "get_news":   
        speech = news_response(user_id)
    elif req.get("result").get("action") == "likesArticle":
        speech = likes_article(user_id)
    elif req.get("result").get("action") == "dislikesArticle":
        speech = dislikes_article(user_id)
    elif req.get("result").get("action") == "reset":
        speech = reset(user_id)
    elif req.get("result").get("action") == "getProfile":
        speech = get_profile(user_id)
            
    my_response = {
     "speech" : speech,
     "displayText " : speech,
    } 

    res = json.dumps(my_response)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'

    return r

@app.errorhandler(404)
def page_not_found(e):
    """Return a custom 404 error."""
    return 'Sorry, nothing at this URL.', 404