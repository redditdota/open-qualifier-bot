import common
from tokens import *
import re

BLACKLIST = [r"\bsolo\W", r"\bplayer\W", r"\WRU\W", r"\WRUS\W", r"\WFR\W", r"\WUA\W", r"\WFIL\W"]
WHITELIST = [r"\bquals\W", r"\bqualifier*", r"\bti8\W", r"\binternational\W"]

REGIONS = {
   "SEA" : ["Southeast", "Asia", "SEA"],
   "EU" : ["Europe", "EU", "NA"],
   "NA" : ["NA", "North", "America", "EU"],
   "SA" : ["SA", "South", "America"],
   "China" : ["CN", "China"],
   "CIS" : ["CIS"]
}

def _get(uri):
    headers = {"Client-ID" : TWITCH_CLIENT_ID}
    result = common.get_json(uri, headers=headers)
    if result is None or "error" in result:
        return None
    return result["data"]

def get_streams():
    result = _get("https://api.twitch.tv/helix/streams?game_id=29595&first=100")
    if result is None:
        return []
    return result

def get_oq_streams(regions):
    streams = get_streams()

    other_regions = set(REGIONS.keys())
    for r in regions:
        if r in other_regions:
            other_regions.remove(r)

    def is_oq(stream):
        title = stream["title"]
        if (re.search(r'[\u0400-\u04FF]', title, re.IGNORECASE)) is not None:
            return False

        for b in BLACKLIST:
            search_result = re.search(b, title, re.IGNORECASE)
            if search_result is not None:
                return False

        for other_region in other_regions:
            for b in REGIONS[other_region]:
                search_result = re.search(r'\b' + b.lower() + '\W', title, re.IGNORECASE)
                if search_result is not None:
                    return False

        for w in WHITELIST:
            search_result = re.search(w, title, re.IGNORECASE)
            if search_result is not None:
                return True
        return False

    return list(filter(lambda stream: is_oq(stream), streams))

def get_link(id):
    result = _get("https://api.twitch.tv/helix/users?id=" + id)
    if result is None or len(result) == 0:
        return None
    return "http://www.twitch.tv/" + result[0]["login"]

def get_text(regions):
    streams = get_oq_streams(regions)
    text = "# Twitch Streams \n\n"
    if len(streams) == 0:
        text += "No live streams found. \n\n"
    else:
        for stream in streams:
            text += "* [%d Viewers] [**%s**](%s)\n\n" % (stream["viewer_count"], stream["title"].strip(), get_link(stream["user_id"]))
    return text

