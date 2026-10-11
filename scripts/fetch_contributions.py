"""Scrape the public contribution calendar and derive streak/total stats."""
import json
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USER = "RINNECODER"
OUT = Path(__file__).resolve().parent.parent / "data" / "contributions.json"


def fetch():
    html = requests.get(
        f"https://github.com/users/{USER}/contributions", timeout=30
    ).text
    soup = BeautifulSoup(html, "html.parser")
    tips = {t.get("for"): t.get_text(strip=True) for t in soup.find_all("tool-tip")}
    days = []
    for td in soup.select("td.ContributionCalendar-day[data-date]"):
        tip = tips.get(td.get("id"), "")
        m = re.match(r"(\d[\d,]*) contribution", tip)
        days.append({
            "date": td["data-date"],
            "count": int(m.group(1).replace(",", "")) if m else 0,
            "level": int(td.get("data-level", 0)),
        })
    days.sort(key=lambda d: d["date"])
    if not days:
        raise SystemExit("no contribution cells found; GitHub markup changed?")
    return days


def stats(days):
    longest = run = 0
    for d in days:
        run = run + 1 if d["count"] else 0
        longest = max(longest, run)
    # Current streak: today may still be empty, so start from yesterday then.
    current = 0
    i = len(days) - 1
    if days[i]["count"] == 0:
        i -= 1
    while i >= 0 and days[i]["count"]:
        current += 1
        i -= 1
    best = max(days, key=lambda d: d["count"])
    months = {}
    for d in days:
        months[d["date"][:7]] = months.get(d["date"][:7], 0) + d["count"]
    return {
        "total": sum(d["count"] for d in days),
        "current_streak": current,
        "longest_streak": longest,
        "best_day": {"date": best["date"], "count": best["count"]},
        "months": months,
    }


def main():
    days = fetch()
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps({"user": USER, "days": days, "stats": stats(days)}, indent=1) + "\n")
    print(f"{len(days)} days, total {sum(d['count'] for d in days)}")


if __name__ == "__main__":
    main()
