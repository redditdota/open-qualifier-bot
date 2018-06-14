import common 
from tokens import *

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
        title = stream["title"].lower()
        return "qual" in title or "ti8" in title or "international" in title

    return list(filter(lambda stream: is_oq(stream), streams))

def get_link(id):
    result = _get("https://api.twitch.tv/helix/users?id=" + id)
    if result is None or len(result) == 0:
        return None
    return "http://www.twitch.tv/" + result[0]["login"]

def get_text():
    streams = get_oq_streams()
    text = "# Twitch Streams \n\n"
    if len(streams) == 0:
        text += "No live streams found. \n\n"
    else:
        for stream in streams:
            text += "* [%d Viewers] [**%s**](%s)\n\n" % (stream["viewer_count"], stream["title"].strip(), get_link(stream["user_id"]))
    return text

