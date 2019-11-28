import sys
import praw
import common
from tokens import *
import time
from china import China
import twitch

# how often to update thread
REFRESH_RATE = 60 * 3

START_TAG = '[](#start-list-matches)'

END_TAG = '[](#end-list-matches)'

REGION = None

PRO_PLAYERS = {}

def get_account_id(steamid64):
    return steamid64 - 76561197960265728;

def get_matches():
    matches = common.get_json(FACEIT_API)
    if matches is None:
        return []
    else:
        return matches


def is_notable(match):
    if 'State' not in match:
        return False

    if int(match['State']['State']) == 0:
        return False

    if match['State'].get('ServerSteamID', None) is None:
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
        account_id = get_account_id(int(steam_id))
        if account_id in PRO_PLAYERS:
            return True

    return False


def get_name(match):
    faceit_name = match['Config']['name']

    players = match['Config']['players']
    radiant = filter(lambda player: player['team'] == 0, players)
    dire = filter(lambda player: player['team'] == 1, players)
    team1 = None
    team2 = None

    team1 = [PRO_PLAYERS.get(get_account_id(int(player['steam'])), "") for player in radiant]
    if len(set(team1)) == 1 and len(team1[0]) > 0:
        team1 = team1[0]
    else:
        team1 = faceit_name[0: faceit_name.lower().find("vs")]

    team2 = [PRO_PLAYERS.get(get_account_id(int(player['steam'])), "") for player in dire]
    if len(set(team2)) == 1 and len(team2[0]) > 0:
        team2 = team2[0]
    else:
        team2 = faceit_name[faceit_name.lower().find("vs") + 2:]
        team2 = team2.strip(".").strip()

    return "%s vs. %s" % (team1, team2)


def get_match_text(china):
    match_str = ''
    matches_json = get_matches()
    matches_json = list(filter(lambda match: is_notable(match), matches_json))
    print("[bot] num matches = " + str(len(matches_json)))
    for match in matches_json:
        match_str += "[**%s**](http://www.trackdota.com/matches/%s):     " % (get_name(match), match['State']['MatchId'])
        match_str += '`watch_server "%s"`\n\n' % match['State']['ServerSteamID'][1:-1]

    match_str = match_str + "\n" + china.get_matches()
    if (len(match_str) == 0):
        match_str = "No notable teams detected in live matches.\n\n"

    return match_str

def update_players():
    global PRO_PLAYERS
    info = common.get_json("https://www.dota2.com/webapi/IDOTA2Fantasy/GetProPlayerInfo/v001")
    if info is not None and "player_infos" in info:
        PRO_PLAYERS = {}
        for player in info["player_infos"]:
            if "team_name" in player:
                PRO_PLAYERS[player["account_id"]] = player["team_name"]
    print("pro player updated:", len(PRO_PLAYERS))


def main():
    assert(len(sys.argv) == 2)

    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent="TI8 OQ Bot",
        username=USERNAME,
        password=PASSWORD)

    update_players()
    china = China(PRO_PLAYERS)

    while (True):
        print("[bot] refreshing...")
        post = reddit.submission(id=sys.argv[1])
        assert(post.author.name.lower() == USERNAME)
        text = post.selftext
        assert(START_TAG in text and END_TAG in text)

        start = text.find(START_TAG) + len(START_TAG)
        end = text.find(END_TAG)
        match_text = "# Live Matches\n\n"

        match_text += get_match_text(china) + "\n\n"

        match_text += "----\n\n"
        match_text += twitch.get_text()

        new_text = text[0:start] + "\n\n" + match_text + "\n\n" + text[end:]
        post.edit(new_text)
        time.sleep(REFRESH_RATE)

if __name__ == '__main__':
    main()
