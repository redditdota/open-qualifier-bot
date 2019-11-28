import common
from tokens import *
import re
import sys
import praw
import time

BLACKLIST = [r"\bsolo\W", r"\bplayer\W", r"\WRU\W", r"\WRUS\W", r"\WFR\W", r"\WUA\W", r"\WFIL\W", r"\brerun\W"]
WHITELIST = [r"\bquals\W", r"\bqualifier*", r"\bti8\W", r"\binternational\W", r"\bdreamleague\W"]

REGION_KEYWORDS = {
   "SEA" : ["Southeast", "Asia", "SEA"],
   "EU" : ["Europe", "EU", "Alliance", "Bulldog", "OG", "Secret", "OG", "Nigma"],
   "NA" : ["North", "America", "NA", "EG", "VGJ", "col", "complexity", "LvR"],
   "SA" : ["SA", "South", "America"],
   "China" : ["CN", "China"],
   "CIS" : ["CIS", "Spirit", "Navi", "Na'Vi"]
}

# how often to update thread
REFRESH_RATE = 60 * 5

START_TAG = '[](#start-streams)'

END_TAG = '[](#end-streams)'


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

def get_oq_streams():
    streams = get_streams()

    def is_oq(stream):
        if stream["language"] != "en":
            return False

        title = stream["title"]
        if (re.search(r'[\u0400-\u04FF]', title, re.IGNORECASE)) is not None:
            return False

        if (re.search(r'[áéíñóúüÁÉÍÑÓÚÜ]', title, re.IGNORECASE)) is not None:
            return False

        for b in BLACKLIST:
            search_result = re.search(b, title, re.IGNORECASE)
            if search_result is not None:
                return False

        for r in REGION_KEYWORDS:
            for b in REGION_KEYWORDS[r]:
                search_result = re.search(r'\b' + b + '\W', title, re.IGNORECASE)
                if search_result is not None:
                    return True

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

def get_text():
    streams = get_oq_streams()
    print("num streams =", len(streams))

    text = "# Twitch Streams \n\n"
    if len(streams) == 0:
        text += "No live streams found. \n\n"
    else:
        for stream in streams:
            text += "* [%d Viewers] [**%s**](%s)\n\n" % (stream["viewer_count"], stream["title"].strip(), get_link(stream["user_id"]))
    return text


def main():
    assert(len(sys.argv) == 3)

    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent="TI8 OQ Bot",
        username=USERNAME,
        password=PASSWORD)

    while (True):
        print("[bot] refreshing...")
        post = reddit.submission(id=sys.argv[1])
        assert(post.author.name.lower() == USERNAME)
        text = post.selftext
        assert(START_TAG in text and END_TAG in text)

        start = text.find(START_TAG) + len(START_TAG)
        end = text.find(END_TAG)
        new_text = text[0:start] + "\n\n" + get_text() + "\n\n" + text[end:]
        post.edit(new_text)
        time.sleep(REFRESH_RATE)

if __name__ == '__main__':
    main()

