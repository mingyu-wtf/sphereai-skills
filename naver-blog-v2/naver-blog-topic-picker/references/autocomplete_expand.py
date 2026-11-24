"""Show Naver autocomplete suggestions for a seed word (no login, no API key).

Usage:
  python autocomplete_expand.py "seed word"

Prints the phrases Naver suggests for the seed. There is no search-volume number.
"""
import json
import sys
import urllib.parse
import urllib.request


def suggest(query):
    params = {
        "q": query, "con": 1, "frm": "nv", "ans": 2, "r_format": "json",
        "r_enc": "UTF-8", "r_unicode": 0, "t_koreng": 1, "run": 2, "rev": 4,
        "q_enc": "UTF-8", "st": 100,
    }
    url = "https://ac.search.naver.com/nx/ac?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.load(r)
    return [item[0] for item in data["items"][0]]


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    seed = sys.argv[1]
    for item in suggest(seed):
        print("-", item)
