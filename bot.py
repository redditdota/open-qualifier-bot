import sys
import praw
import urllib, json
from tokens import *
from watchlist import PLAYERS_TO_TEAMS
import time

# how often to update thread
REFRESH_RATE = 60 * 3

REDDIT_API = None

START_TAG = '[](#start-list-matches)'

END_TAG = '[](#end-list-matches)'

def setup_connection_reddit(subreddit):
    ''' Creates a connection to the reddit API. '''
    print('[bot] Setting up connection with reddit')
    global REDDIT_API
    REDDIT_API = praw.Reddit('reddit Twitter tool monitoring {}'.format(subreddit))
    subreddit = REDDIT_API.get_subreddit(subreddit)
    REDDIT_API.login(USERNAME, PASSWORD)
    return subreddit

def get_matches():
    try:
        faceit = urllib.urlopen(FACEIT_API)
    except IOError as e:
        print(e)
        return []
    matches_json = json.loads(faceit.read())
    faceit.close()
    return matches_json


def is_notable(match):
    if 'State' not in match:
        return False

    if int(match['State']['State']) == 0:
        return False

    if match['State']['ServerSteamID'] is None:
        return False

    if 'Config' not in match:
        return False

    config = match['Config']
    if 'players' not in config:
        return False

    players = config['players']
    for player in players:
        if 'steam' not in player:
            continue

        steam_id = player['steam']
        if steam_id in PLAYERS_TO_TEAMS:
            return True

    return False


def process(text):
    start = text.find(START_TAG) + len(START_TAG)
    end = text.find(END_TAG)

    match_str = ''
    matches_json = get_matches()
    matches_json = filter(lambda match: is_notable(match), matches_json)
    print("[bot] num matches = " + str(len(matches_json)))
    for match in matches_json:
        match_str += "[**%s**](http://www.trackdota.com/matches/%s):     " % (match['Config']['name'].replace("VS", "vs."), match['State']['MatchId'])
        match_str += '`watch_server "%s"`\n\n' % match['State']['ServerSteamID'][1:-1]

    if (len(matches_json) == 0):
        match_str = "No notable teams are playing right now.\n\n"

    return text[0:start] + "\n\n" + match_str + "\n\n" + text[end:]




def main():
    assert(len(sys.argv) == 2)

    subreddit = setup_connection_reddit(SUBREDDIT)
    post = REDDIT_API.get_submission(submission_id=sys.argv[1])
    assert(post.author.name == USERNAME)

    while (True):
        print("[bot] refreshing...")
        post.refresh()
        text = post.selftext
        new_text = process(text)
        post.edit(new_text)
        time.sleep(REFRESH_RATE)

if __name__ == '__main__':
    main()
