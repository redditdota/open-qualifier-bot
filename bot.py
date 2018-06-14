import sys
import praw
import urllib, json
from tokens import *
from watchlist import NOTABLE_BY_REGION
import time
import china
import twitch

# how often to update thread
REFRESH_RATE = 60 * 3

START_TAG = '[](#start-list-matches)'

END_TAG = '[](#end-list-matches)'

REGION = None

def get_matches():
    try:
        with urllib.request.urlopen(FACEIT_API) as faceit:
            return json.loads(faceit.read().decode('utf-8'))
    except IOError as e:
        print(e)
        return []


def is_notable(match, region):
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
        if steam_id in NOTABLE_BY_REGION[region]:
            return True

        #if steam_id in china.PROS_STEAM_ID:
        #    return True

    return False


def get_name(match, region):
    faceit_name = match['Config']['name']
    players = match['Config']['players']
    radiant = filter(lambda player: player['team'] == 0, players)
    dire = filter(lambda player: player['team'] == 1, players)
    team1 = None
    team2 = None
    for player in radiant:
        if player['steam'] in NOTABLE_BY_REGION[region]:
            team1 = NOTABLE_BY_REGION[region][player['steam']]
            break

    if team1 is None:
        team1 = faceit_name[0: faceit_name.find("VS")]

    for player in dire:
        if player['steam'] in NOTABLE_BY_REGION[region]:
            team2 = NOTABLE_BY_REGION[region][player['steam']]
            break

    if team2 is None:
        team2 = faceit_name[faceit_name.find("VS") + 2:]

    return "%s vs. %s" % (team1, team2)


def get_match_text(region):
    if region.lower() == "china":
        return china.get_matches()

    match_str = ''
    matches_json = get_matches()
    matches_json = list(filter(lambda match: is_notable(match, region), matches_json))
    print("[bot] num matches = " + str(len(matches_json)))
    for match in matches_json:
        match_str += "[**%s**](http://www.trackdota.com/matches/%s):     " % (get_name(match, region), match['State']['MatchId'])
        match_str += '`watch_server "%s"`\n\n' % match['State']['ServerSteamID'][1:-1]

    if (len(matches_json) == 0):
        match_str = "No notable teams detected in live matches.\n\n"

    return match_str


def main():
    assert(len(sys.argv) == 3)

    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent="TI8 OQ Bot",
        username=USERNAME,
        password=PASSWORD)

    global REGIONS
    REGIONS = sys.argv[2].split(",")

    while (True):
        print("[bot] refreshing...")
        post = reddit.submission(id=sys.argv[1])
        assert(post.author.name.lower() == USERNAME)
        text = post.selftext
        assert(START_TAG in text and END_TAG in text)

        start = text.find(START_TAG) + len(START_TAG)
        end = text.find(END_TAG)
        match_text = "# Live Matches\n\n"
        for region in REGIONS:
            match_text += "## " + region + "\n\n"
            match_text += get_match_text(region) + "\n\n"

        match_text += "----\n\n"
        match_text += twitch.get_text(REGIONS)

        new_text = text[0:start] + "\n\n" + match_text + "\n\n" + text[end:]
        post.edit(new_text)
        time.sleep(REFRESH_RATE)

if __name__ == '__main__':
    main()
