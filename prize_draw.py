import os
import tweepy
from dotenv import load_dotenv
import random
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import webbrowser
from threading import Thread

load_dotenv()

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1' # Allow OAuth2 to work with http for localhost

def read_template(filename):
    with open(os.path.join('templates', filename), 'r', encoding='utf-8') as f:
        return f.read()

class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        CallbackHandler.response_url = f"http://localhost:8000{self.path}"
        query_components = parse_qs(urlparse(self.path).query)
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        html = read_template('callback.html')
        self.wfile.write(html.encode())
        
        if 'code' in query_components:
            CallbackHandler.auth_code = query_components['code'][0]

def get_oauth2_token():
    oauth2_handler = tweepy.OAuth2UserHandler(
        client_id=os.getenv('CLIENT_ID'),
        client_secret=os.getenv('CLIENT_SECRET'),
        redirect_uri="http://localhost:8000",
        scope=["tweet.read", "users.read", "like.read"]
    )
    
    server = HTTPServer(('localhost', 8000), CallbackHandler)
    server_thread = Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    
    auth_url = oauth2_handler.get_authorization_url()
    webbrowser.open(auth_url)
    
    while not hasattr(CallbackHandler, 'response_url'):
        pass
    
    server.shutdown()
    server.server_close()
    
    return oauth2_handler.fetch_token(CallbackHandler.response_url)

def get_eligible_participants(post_url, client, oauth2_client):
    tweet_id = post_url.split('/')[-1]
    
    try:
        # Get likes
        print("\n1. Fetching likes")
        likes = oauth2_client.get_liking_users(
            tweet_id,
            user_fields=['id', 'username', 'name']
        )
        likers = {user.id: f"@{user.username} ({user.name})" for user in (likes.data or [])}
        print(f"Found {len(likers)} users who liked the tweet")
        
        # Get retweets
        print("\n2. Fetching retweets")
        retweets = client.get_retweeters(tweet_id)
        retweeters = set(user.id for user in (retweets.data or []))
        print(f"Found {len(retweeters)} users who retweeted")
        
        # Get replies with mentions
        print("\n3. Fetching replies with mentions")
        replies = client.search_recent_tweets(
            query=f'in_reply_to_tweet_id:{tweet_id}',
            tweet_fields=['author_id', 'entities'],
            expansions=['author_id'],
            max_results=100
        )
        
        valid_commenters = {
            reply.author_id 
            for reply in (replies.data or [])
            if hasattr(reply, 'entities') 
            and 'mentions' in reply.entities 
            and len(reply.entities['mentions']) >= 1
        }
        print(f"Found {len(valid_commenters)} users who replied with mentions")
        
        # Find users who meet all criteria
        eligible_user_ids = set(likers.keys()) & retweeters & valid_commenters
        eligible_users = {id: likers[id] for id in eligible_user_ids}
        
        print(f"\nSummary:")
        print(f"• {len(likers)} users liked")
        print(f"• {len(retweeters)} users retweeted")
        print(f"• {len(valid_commenters)} users replied with mentions")
        print(f"• {len(eligible_users)} users met all criteria")
        
        return eligible_users
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {}

class ResultsHandler(BaseHTTPRequestHandler):
    winners = {}  
    
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        winners_html = ''.join(
            f'<div class="winner" style="animation-delay: {i * 0.5}s" '
            f'data-profile="https://twitter.com/i/user/{id}">'
            f'<h2>{ResultsHandler.winners[id]}</h2></div>'
            for i, id in enumerate(ResultsHandler.winners.keys())
        )
        
        template = read_template('results.html')
        html = template.replace('{winners_html}', winners_html)
        self.wfile.write(html.encode('utf-8'))

def show_results_in_browser(winners):

    ResultsHandler.winners = winners  

    server = HTTPServer(('localhost', 8001), ResultsHandler)
    server_thread = Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    
    webbrowser.open('http://localhost:8001')
    input("\nPress Enter to close the results window...")
    server.shutdown()
    server.server_close()

def draw_winners():
    post_url = os.getenv('TWITTER_POST_URL')
    num_winners = int(os.getenv('MAX_WINNERS')) 
    
    if not post_url:
        raise ValueError("No Twitter post URL provided. Set TWITTER_POST_URL in .env")
    
    token = get_oauth2_token()
    
    client = tweepy.Client(
        bearer_token=os.getenv('BEARER_TOKEN'),
        wait_on_rate_limit=True
    )

    oauth2_client = tweepy.Client(
        bearer_token=token['access_token'],
        wait_on_rate_limit=True
    )
    
    participants = get_eligible_participants(post_url, client, oauth2_client)
    
    if not participants:
        print("No eligible participants found.")
        return
    
    num_winners = min(num_winners, len(participants))
    winner_ids = random.sample(list(participants.keys()), num_winners)
    winners = {id: participants[id] for id in winner_ids}
    
    print(f"\nSelected {num_winners} winner(s):")
    for i, winner_id in enumerate(winner_ids, 1):
        print(f"{i}. {participants[winner_id]}")
        print(f"   Profile: https://twitter.com/i/user/{winner_id}")
    
    show_results_in_browser(winners)

if __name__ == "__main__":
    draw_winners()
