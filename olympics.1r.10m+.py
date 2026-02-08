#!/usr/bin/env python3
"""
Argos plugin: 2026 Winter Olympics Medal Tracker
Place in ~/.config/argos/ with a name like:
    olympics.1r.10m+.py

Filename breakdown:
    olympics  = name
    1r        = position: just right of the clock
    10m+      = refresh every 10 minutes, also refresh on dropdown open
    .py       = extension
"""

import json
import re
import sys
import urllib.request

API_URL = (
    "https://en.wikipedia.org/w/api.php"
    "?action=parse"
    "&page=2026_Winter_Olympics_medal_table"
    "&prop=wikitext"
    "&section=2"
    "&format=json"
)
USER_AGENT = "OlympicMedalTracker/1.0 (Linux; Fedora; personal project)"

IOC_CODES = {
    "AIN": "Neutral Athletes", "ALB": "Albania", "AND": "Andorra",
    "ARG": "Argentina", "ARM": "Armenia", "AUS": "Australia",
    "AUT": "Austria", "AZE": "Azerbaijan", "BEL": "Belgium",
    "BIH": "Bosnia & Herzegovina", "BLR": "Belarus", "BOL": "Bolivia",
    "BRA": "Brazil", "BUL": "Bulgaria", "CAN": "Canada",
    "CHI": "Chile", "CHN": "China", "COL": "Colombia",
    "CRO": "Croatia", "CYP": "Cyprus", "CZE": "Czech Republic",
    "DEN": "Denmark", "ERI": "Eritrea", "ESP": "Spain",
    "EST": "Estonia", "FIN": "Finland", "FRA": "France",
    "GBR": "Great Britain", "GEO": "Georgia", "GER": "Germany",
    "GRE": "Greece", "HUN": "Hungary", "ICE": "Iceland",
    "IND": "India", "IRI": "Iran", "IRL": "Ireland",
    "ISR": "Israel", "ITA": "Italy", "JAM": "Jamaica",
    "JPN": "Japan", "KAZ": "Kazakhstan", "KGZ": "Kyrgyzstan",
    "KOR": "South Korea", "KOS": "Kosovo", "LAT": "Latvia",
    "LBN": "Lebanon", "LIE": "Liechtenstein", "LTU": "Lithuania",
    "LUX": "Luxembourg", "MDA": "Moldova", "MEX": "Mexico",
    "MGL": "Mongolia", "MKD": "North Macedonia", "MLT": "Malta",
    "MNE": "Montenegro", "MON": "Monaco", "NED": "Netherlands",
    "NEP": "Nepal", "NGR": "Nigeria", "NOR": "Norway",
    "NZL": "New Zealand", "PAK": "Pakistan", "PER": "Peru",
    "PHI": "Philippines", "POL": "Poland", "POR": "Portugal",
    "PRK": "North Korea", "PUR": "Puerto Rico", "ROU": "Romania",
    "RSA": "South Africa", "RUS": "Russia", "SLO": "Slovenia",
    "SMR": "San Marino", "SRB": "Serbia", "SUI": "Switzerland",
    "SVK": "Slovakia", "SWE": "Sweden", "THA": "Thailand",
    "TPE": "Chinese Taipei", "TUR": "Turkey", "UKR": "Ukraine",
    "USA": "United States", "UZB": "Uzbekistan",
}

# ---- Change this to your country's IOC code to highlight it ----
MY_COUNTRY = "USA"
# ----------------------------------------------------------------


def fetch_medals():
    req = urllib.request.Request(API_URL, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            wikitext = data["parse"]["wikitext"]["*"]
    except Exception:
        return None

    clean = re.sub(r'<!--.*?-->', '', wikitext, flags=re.DOTALL)

    golds = {m.group(1): int(m.group(2)) for m in re.finditer(r'\|\s*gold_(\w+)\s*=\s*(\d+)', clean)}
    silvers = {m.group(1): int(m.group(2)) for m in re.finditer(r'\|\s*silver_(\w+)\s*=\s*(\d+)', clean)}
    bronzes = {m.group(1): int(m.group(2)) for m in re.finditer(r'\|\s*bronze_(\w+)\s*=\s*(\d+)', clean)}

    all_codes = set(golds.keys()) | set(silvers.keys()) | set(bronzes.keys())

    results = []
    for code in all_codes:
        g = golds.get(code, 0)
        s = silvers.get(code, 0)
        b = bronzes.get(code, 0)
        total = g + s + b
        if total == 0:
            continue
        results.append({
            "code": code,
            "country": IOC_CODES.get(code, code),
            "gold": g,
            "silver": s,
            "bronze": b,
            "total": total,
        })

    results.sort(key=lambda x: (-x["gold"], -x["silver"], -x["bronze"], x["code"]))

    for i, entry in enumerate(results):
        if i == 0:
            entry["rank"] = 1
        else:
            prev = results[i - 1]
            if (entry["gold"] == prev["gold"] and
                entry["silver"] == prev["silver"] and
                entry["bronze"] == prev["bronze"]):
                entry["rank"] = prev["rank"]
            else:
                entry["rank"] = i + 1

    return results


def find_country(medals, code):
    """Find a specific country in the results."""
    for m in medals:
        if m["code"] == code:
            return m
    return None


def main():
    medals = fetch_medals()

    if not medals:
        print("🏅 ??? | refresh=true")
        print("---")
        print("Failed to fetch medal data | color=#ff0000")
        print("Click to retry | refresh=true")
        return

    # === TOP BAR LINE ===
    # Show your country if they have medals, otherwise show the leader
    mine = find_country(medals, MY_COUNTRY)
    leader = medals[0]

    if mine and mine["total"] > 0:
        top_text = f"🏅 {MY_COUNTRY} {mine['gold']}🥇 {mine['silver']}🥈 {mine['bronze']}🥉"
    else:
        top_text = f"🏅 {leader['code']} {leader['gold']}🥇 {leader['silver']}🥈 {leader['bronze']}🥉"

    print(f"{top_text} | refresh=true")

    # === DROPDOWN ===
    print("---")
    print("🏔️  Milano Cortina 2026 | href=https://www.olympics.com/en/milano-cortina-2026/medals size=12")
    print("---")

    # Column headers
    print(f"{'#':<3}  {'Country':<20} {'🥇':>3} {'🥈':>3} {'🥉':>3} {'Tot':>4} | font=monospace size=11")
    print("---")

    for m in medals:
        # Highlight your country
        color = ""
        if m["code"] == MY_COUNTRY:
            color = " color=#3584e4"

        line = f"{m['rank']:<3}  {m['country']:<20} {m['gold']:>3} {m['silver']:>3} {m['bronze']:>3} {m['total']:>4}"
        print(f"{line} | font=monospace size=11{color}")

    # Totals
    total_g = sum(m["gold"] for m in medals)
    total_s = sum(m["silver"] for m in medals)
    total_b = sum(m["bronze"] for m in medals)
    total_t = sum(m["total"] for m in medals)
    print("---")
    print(f"{'':3}  {'Total':<20} {total_g:>3} {total_s:>3} {total_b:>3} {total_t:>4} | font=monospace size=11")

    print("---")
    print("Open Medal Table | href=https://www.olympics.com/en/milano-cortina-2026/medals")
    print("Open Wikipedia | href=https://en.wikipedia.org/wiki/2026_Winter_Olympics_medal_table")
    print("Refresh | refresh=true")


if __name__ == "__main__":
    main()
