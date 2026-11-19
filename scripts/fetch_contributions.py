"""Fetch the contribution calendar and featured-repo stats into data/contributions.json.

Runs daily in the GitHub Action (uses GITHUB_TOKEN). Locally it falls back to `gh auth token`.
Standard library only.
"""
import json
import os
import subprocess
import urllib.request
from pathlib import Path

from config import LOGIN, REPOS

ROOT = Path(__file__).resolve().parent.parent

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
    repositories(first: 100, ownerAffiliations: OWNER, privacy: PUBLIC) {
      nodes { name stargazerCount forkCount pushedAt primaryLanguage { name color } }
    }
  }
}
"""


def token():
    t = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if t:
        return t
    return subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, check=True).stdout.strip()


def main():
    body = json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode()
    req = urllib.request.Request("https://api.github.com/graphql", data=body, headers={
        "Authorization": f"bearer {token()}", "Content-Type": "application/json",
        "User-Agent": "profile-cards"})
    with urllib.request.urlopen(req, timeout=30) as r:
        res = json.load(r)
    if "errors" in res:
        raise SystemExit(f"GraphQL error: {res['errors']}")
    user = res["data"]["user"]
    cal = user["contributionsCollection"]["contributionCalendar"]
    days = [{"date": d["date"], "count": d["contributionCount"]}
            for w in cal["weeks"] for d in w["contributionDays"]]
    wanted = {r["name"] for r in REPOS}
    repos = {n["name"]: {"stars": n["stargazerCount"], "forks": n["forkCount"], "pushed": n["pushedAt"],
                         "language": (n["primaryLanguage"] or {}).get("name"),
                         "language_color": (n["primaryLanguage"] or {}).get("color")}
             for n in user["repositories"]["nodes"] if n["name"] in wanted}
    out = {"login": LOGIN, "total": cal["totalContributions"], "days": days, "repos": repos}
    path = ROOT / "data/contributions.json"
    path.write_text(json.dumps(out, indent=1) + "\n")
    print(f"{len(days)} days, {out['total']} contributions, {len(repos)} repos -> {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
