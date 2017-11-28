from flask import Flask
from flask import request
from flask import make_response
from newsapi.articles import Articles
from google.appengine.api import app_identity

import json
import logging as l
import random
import numpy as np
import os
import cloudstorage as gcs
import webapp2

app = Flask(__name__)

sports = np.array(["Ducks", "Cardinals", "Coyotes", "Diamondbacks", "Braves", "Falcons", "Hawks", "Atlanta FC", "Orioles", 
          "Lions", "Bruins", "Celtics", "Sox", "Nets", "Bills", "Sabres", "Flames", "Stampeders", "Hurricanes", "Panthers", 
          "Hornets", "Bears", "Blackhawks", "Bulls", "Cubs", "Fire", "White Sox", "Bengals", "Reds", "Browns", "Cavaliers",
          "Indians", "Avalanche", "Rapids", "Rockies", "Jackets", "Columbus Crew", "FC Dallas", "Cowboys", "Mavericks", 
          "Stars", "D.C. United", "Broncos", "Nuggets", "Lions", "Pistons", "Wings", "Tigers", "Eskimos", "Oilers", "Panthers", 
          "Warriors", "Packers", "Tiger-Cats", "Astros", "Dynamo", "Rockets", "Texans", "Pacers", "Colts", "Jaguars", "City",
          "Chiefs", "Royals", "Galaxy", "Angels", "Chargers", "Clippers", "Dodgers", "LA FC", "Kings", "Lakers", "Rams",
          "Grizzlies", "Dolphins", "Heat", "Marlins", "Brewers", "Bucks", "Timberwolves", "Twins", "Minnisota FC", "Vikings",
          "Wild", "Alouettes", "Canadiens", "Impact", "Predators", "Patriots", "Revolution", "Devils", "Pelicans", "Saints", 
          "NYC FC", "Giants", "Islanders", "Jets", "Knicks", "Mets", "Rangers", "Red Bulls", "Yankees", "Athletics", "Raiders", 
          "Thunder", "Orlando City", "Magic", "Redblacks", "Senators", "76ers", "Eagles", "Flyers", "Phillies", "Union", 
          "Suns", "Penguins", "Pirates", "Steelers", "Trail Blazers", "Timbers", "Kings", "Real Salt Lake", "Spurs", "Padres",
          "49ers", "Giants", "Earthquakes", "Sharks", "Roughriders", "Blues", "Cardinals", "Mariners", "Seahawks", "Sounders",
          "Buccaneers", "Lightning", "Rays", "Titans", "Rangers", "Argonauts", "Blue Jays", "Toronto FC", "Maple Leafs",
          "Raptors", "Jazz", "Canucks", "Whitecaps", "Golden Knights", "Capitals", "Nationals", "Redskins", "Wizards",
          "Blue Bombers", "Ravens", "Politics"])

def get_bucket():
    return os.environ.get('BUCKET_NAME', app_identity.get_default_gcs_bucket_name())
   
def create_file(filename, all_articles, article, profile):
    """Create a file.

    The retry_params specified in the open call will override the default
    retry params for this particular file handle.

    Args:
      filename: filename.
    """
    outString = ','.join(['%.5f' % num for num in profile])
    
    write_retry_params = gcs.RetryParams(backoff_factor=1.1)
    gcs_file = gcs.open(filename,
                        'w',
                        content_type='text/plain',
                        retry_params=write_retry_params)
    gcs_file.write("||".join(all_articles).encode("utf-8") + "\n")
    gcs_file.write(article.encode("utf-8") + "\n")
    gcs_file.write(outString)
    gcs_file.close()
    
def read_file(filename):
    gcs_file = gcs.open(filename)
    
    all_articles = str(gcs_file.readline()).rstrip().split("||")
    article = str(gcs_file.readline()).rstrip()

    text = gcs_file.read()
    l.info(text)

    gcs_file.close()
    
    return (all_articles, article, text)

news_api_key = "663733985a214ef5aa4ee7372ab3e223"

def get_news():
    a = Articles(API_KEY=news_api_key)
    
    source_ids = ['espn', 'espn-cric-info', 'fox-sports', 'nfl-news']
#    
#    news = []
#    for source in source_ids:
#        articles = a.get(source)["articles"]
#        text = [(article["title"], article["description"]) for article in articles]
#        if text[1] is None:
#        	text[1] = ''
#        news += text
        
    news = []
    for source in source_ids:
        articles = a.get(source)["articles"]
        text = []
        for article in articles:
            if not (article["title"] is None or article["description"] is None or len(article["title"]) == 0):
                text.append((article["title"], article["description"]))
        if len(text) > 0:
            news += text
        
#    articles = a.get("breitbart-news")["articles"]
#    text = [("Politics: " + article["title"], article["description"]) if article["description"] is not None else ("Politics: " + article["title"], "") for article in articles]
#    news += text
    
    return news
    
def process_articles(news):
    articles = []
    for article in news:
        article_profile = np.zeros(len(sports))
        
        for i, sport in enumerate(sports):
            try:
                words = set("".join(c for c in article[0].lower() + " " + article[1] if c.isalnum() or c.isspace()).split())
                if sport.lower() in words:
                    article_profile[i] += 1
            except:
                l.info('skipped')
                if article[0] is None:
                	l.info('article 0 is none')
                if article[1] is None:
                	l.info('article 1 is none')
#                l.info(article[0] + "||||" + article[1])

        articles.append(article_profile)

    return articles
    
def process_one(article):
    article_profile = np.zeros(len(sports))
    for i, sport in enumerate(sports):
        words = set("".join(c for c in article.lower() if c.isalnum() or c.isspace()).split())
        if sport.lower() in words:
            article_profile[i] += 1

    return article_profile

def get_similar_news(article_profiles, news, my_profile):
    l.info(str(len(my_profile)) + "|" + str(len(article_profiles[0])))
    distances = np.nan_to_num([np.dot(my_profile, profile) / (np.linalg.norm(my_profile) * np.linalg.norm(profile)) for profile in article_profiles])
    closest_articles = np.argsort(distances)[::-1]
    
    headlines = []
    for article in news:
        headlines.append(article[0] + ". " + article[1])
            
    return np.array(headlines)[closest_articles]
    
def contains(article, article_list):
    for a in article_list:
        if article.encode("utf-8")[:20] == a[:20]:
            return True
    return False
    
def describe_profile(profile):
    return (list(sports[np.where(profile>0, True, False)]), list(sports[np.where(profile<0, True, False)]))

@app.route('/')
def hello():
    return 'Hello World!\n'

@app.route('/webhook', methods=['POST'])
def apiai_response():
    req = request.get_json(silent=True, force=True)
    l.info("this is the json!!!!!!! \n" + str(req))
    
    try:
        id = req.get("originalRequest").get("data").get("user").get("userId")
    except:
#        l.info(str(req.get("originalRequest")))
#        l.info(str(req.get("originalRequest").get("data")))
#        l.info(str(req.get("originalRequest").get("data").get("conversation")))
#        l.info(str(req.get("originalRequest").get("data").get("conversation").get("user")))
        id = "guest"
    
    l.info("action: " + req.get("result").get("action"))

    speech = "updated results"
    if req.get("result").get("action") == "get_news":   
        news = get_news()
        article_profiles = process_articles(news)
#        i = random.randint(0, len(news)-1)
#        speech = news[i][0] + ". " + news[i][1]
        
        (all_articles, last_article, file_text) = read_file("/sportsfeed-21790.appspot.com/" + id + ".txt")
        user_profile = np.fromstring(file_text, sep=',')

        ordered_news = get_similar_news(article_profiles, news, user_profile)
       
        i = 0
        while contains(ordered_news[i], all_articles):
#            l.info("news: " + ordered_news[i].encode("utf-8") + " articles: " + str(all_articles) + " i: " + str(i))
            i += 1
            if i >= len(ordered_news):
        	    break
        	    
        if i < len(ordered_news):
            speech = ordered_news[i] + "\n\nDo you like this article?"
            all_articles.append(ordered_news[i])
            create_file("/sportsfeed-21790.appspot.com/" + id + ".txt", all_articles, ordered_news[i], user_profile)
        else:
            speech = "Sorry, no more news left."

    elif req.get("result").get("action") == "likesArticle":
        l.info("in likes article")
    	(all_articles, last_article, file_text) = read_file("/sportsfeed-21790.appspot.com/" + id + ".txt")
    	article_profile = process_one(last_article)
    	user_profile = np.fromstring(file_text, sep=',')
    	
    	user_profile += article_profile
    	
    	create_file("/sportsfeed-21790.appspot.com/" + id + ".txt", all_articles, last_article, user_profile)
    	
    elif req.get("result").get("action") == "dislikesArticle":
        speech = "Sorry about that. Updated profile."
        l.info("in dislikes article")
    	(all_articles, last_article, file_text) = read_file("/sportsfeed-21790.appspot.com/" + id + ".txt")
    	article_profile = process_one(last_article)
    	user_profile = np.fromstring(file_text, sep=',')
    	
    	user_profile -= article_profile
    	
    	create_file("/sportsfeed-21790.appspot.com/" + id + ".txt", all_articles, last_article, user_profile)    	
    	
    elif req.get("result").get("action") == "reset":
        l.info("in reset")
        speech = "Resetting user profile..."
        
        user_profile = np.zeros(len(sports))
        create_file("/sportsfeed-21790.appspot.com/" + id + ".txt", "", "", user_profile) 
    
    elif req.get("result").get("action") == "getProfile":
        l.info("in describe")
        (all_articles, last_article, file_text) = read_file("/sportsfeed-21790.appspot.com/" + id + ".txt")
        user_profile = np.fromstring(file_text, sep=',')
        
        (likes, dislikes) = describe_profile(user_profile)
        
        if len(likes) > 0 and len(dislikes) > 0:
            speech = "You like: " + ", ".join(likes) + ". You dislike: " + ", ".join(dislikes)
        elif len(likes) > 0:
            speech = "You like: " + ", ".join(likes)
        elif len(dislikes) > 0:
            speech = "You dislike: " + ", ".join(dislikes)
        else:
            speech = "You have no likes or dislikes."
        
    	
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
