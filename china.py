import common
from tokens import *
from watchlist import NOTABLE_BY_REGION


def get_pros():
    result = common.get_json("https://api.opendota.com/api/proPlayers")
    if result is None:
        return []
    return result

PROS = get_pros()
PROS_ACCOUNT_ID = {}
PROS_STEAM_ID = {}
for pro in PROS:
    PROS_STEAM_ID[pro["steamid"]] = pro["name"]
    if pro.get("loccountrycode", "").lower() == "cn" or pro.get("country_code", "").lower() == "cn":
        PROS_ACCOUNT_ID[pro["account_id"]] = pro["name"]


def _is_notable(game):
    def _is_notable_team(team):
        return team["team_id"] in NOTABLE_BY_REGION["China"]

    if "dire_team" in game and _is_notable_team(game["dire_team"]):
        return True
    if "radiant_team" in game and _is_notable_team(game["radiant_team"]):
        return True

    for p in game.get("players", []):
        if p["account_id"] in PROS_ACCOUNT_ID:
            return True
    return False

def _get_name(game):
    radiant_players = []
    dire_players = []
    for p in game["players"]:
        if p["account_id"] not in PROS_ACCOUNT_ID:
            continue
        if p["team"] == 0:
            radiant_players.append(PROS_ACCOUNT_ID[p["account_id"]])
        if p["team"] == 1:
            dire_players.append(PROS_ACCOUNT_ID[p["account_id"]])

    def to_name(players):
        if len(players) == 5:
            return ", ".join(players)
        else:
            return ", ".join(players) + " +%d" % (5 - len(players))

    dire = to_name(dire_players) if len(dire_players) > 0 else "Dire"
    radiant = to_name(radiant_players) if len(radiant_players) > 0 else "Radiant"
    dire = game.get("dire_team", {}).get("team_name", dire)
    radiant = game.get("radiant_team", {}).get("team_name", radiant)
    return "%s vs. %s" % (dire, radiant)

def get_matches():
    uri = "https://api.steampowered.com/IDOTA2Match_570/GetLiveLeagueGames/v0001/?key=%s" % (STEAM_KEY)
    result = common.get_json(uri)
    if result is None or "result" not in result:
        return "No notable teams detected in live matches.\n\n"

    match_str = ""
    for game in result["result"]["games"]:
        if int(game["league_id"]) == LEAGUE_ID and _is_notable(game):
            match_str += "[**%s**](http://www.trackdota.com/matches/%s) \n\n" % (_get_name(game), game["match_id"])

    if len(match_str) == 0:
        match_str = "No notable teams detected in live matches."

    return match_str

