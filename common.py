import requests
import json
import time

MAX_TRIES = 10


def get_json(url, headers={}):
    n = 0
    while n < MAX_TRIES:
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == requests.codes.ok:
                return response.json()
            elif response.status_code == requests.codes.not_found:
                return None
            else:
                print("[bot]", url, response.text)
        except requests.exceptions.RequestException as e:
            print("[bot] ", url, e)
        except json.decoder.JSONDecodeError as e:
            print("[bot] ", url, e)
        time.sleep(10)
        n += 1

    return None