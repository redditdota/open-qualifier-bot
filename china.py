from tokens import *
import common

OPENDOTA_PROS = "https://api.opendota.com/api/proPlayers"
LIVE_GAMES = "https://api.steampowered.com/IDOTA2Match_570/GetLiveLeagueGames/v0001/?key=%s" % STEAM_KEY

class China():

    def __init__(self, pro_teams):

        opendota_pros = common.get_json(OPENDOTA_PROS)
        if opendota_pros is None:
            opendota_pros = []

        self.chinese_pros = {}
        for pro in opendota_pros:
            country = pro.get("loccountrycode", pro.get("country_code", ""))
            if country is not None and country.lower() == "cn":
                self.chinese_pros[pro["account_id"]] = pro["name"]
        self.pro_teams = pro_teams


    def _is_notable(self, game):
        for p in game.get("players", []):
            if p["account_id"] in self.chinese_pros:
                return True
        return False

    def _get_name_helper(players):
        if len(players) == 5:
            return ", ".join(players)
        else:
            return ", ".join(players) + " +%d" % (5 - len(players))


    def _get_name(self, game):
        radiant_players = []
        dire_players = []

        for p in game["players"]:
            if p["account_id"] not in self.chinese_pros:
                continue
            if p["team"] == 0:
                radiant_players.append(self.chinese_pros[p["account_id"]])
            if p["team"] == 1:
                dire_players.append(self.chinese_pros[p["account_id"]])

        dire = _get_name_helper(dire_players) if len(dire_players) > 0 else "Dire"
        radiant = _get_name_helper(radiant_players) if len(radiant_players) > 0 else "Radiant"

        dire = game.get("dire_team", {}).get("team_name", dire)
        radiant = game.get("radiant_team", {}).get("team_name", radiant)
        return "%s vs. %s" % (dire, radiant)



    def get_matches(self):
        result =  common.get_json(LIVE_GAMES)
        if result is None or "result" not in result:
            return ""

        match_str = ""
        for game in result["result"]["games"]:
            if int(game["league_id"]) == LEAGUE_ID and self._is_notable(game):
                match_str += "[**%s**](http://www.trackdota.com/matches/%s) \n\n" % (self._get_name(game), game["match_id"])

        return match_str






