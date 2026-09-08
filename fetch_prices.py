#!/usr/bin/env python3
"""Fetch gold/USD prices from tgju.org and write them to data.json.
Runs on GitHub Actions (server-side) so the visitor's browser never has
to reach tgju.org directly -- it only reads data.json from GitHub Pages.
"""
import json
import urllib.request
from datetime import datetime, timezone

KEYS = ["price_dollar_rl", "geram18", "ons"]
URL = "https://api.tgju.org/v1/market/tmp?keys=" + ",".join(KEYS)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}


def fetch():
    req = urllib.request.Request(URL, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def parse_num(v):
    if v is None:
        return None
    try:
        return float(str(v).replace(",", ""))
    except ValueError:
        return None


def extract(indicators, name):
    for ind in indicators:
        if ind.get("name") == name:
            return {
                "price": parse_num(ind.get("p")),
                "change": parse_num(ind.get("d")),
                "direction": ind.get("dt"),  # "high" | "low"
            }
    return None


def load_previous():
    try:
        with open("data.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def main():
    now = datetime.now(timezone.utc).isoformat()
    try:
        raw = fetch()
        indicators = raw.get("response", {}).get("indicators", [])
        data = {
            "ok": True,
            "generated_at": now,
            "ounce": extract(indicators, "ons"),
            "usd_rial": extract(indicators, "price_dollar_rl"),
            "gold18_rial": extract(indicators, "geram18"),
        }
        if not any([data["ounce"], data["usd_rial"], data["gold18_rial"]]):
            raise RuntimeError("none of the expected keys were found in the response")
    except Exception as e:
        prev = load_previous() or {}
        data = {
            "ok": False,
            "error": str(e),
            "last_attempt_at": now,
            "generated_at": prev.get("generated_at"),
            "ounce": prev.get("ounce"),
            "usd_rial": prev.get("usd_rial"),
            "gold18_rial": prev.get("gold18_rial"),
        }

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
