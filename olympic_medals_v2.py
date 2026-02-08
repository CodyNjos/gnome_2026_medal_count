#!/usr/bin/env python3
"""
Scrapes the 2026 Winter Olympics medal table from Wikipedia's API
and outputs formatted medal counts.

Uses the MediaWiki API to get structured wikitext, which is far more
reliable than HTML scraping.

Usage:
    python3 olympic_medals.py              # pretty print all countries
    python3 olympic_medals.py --json       # raw JSON
    python3 olympic_medals.py --top 5      # top N countries
    python3 olympic_medals.py --country US # filter by country name/code
    python3 olympic_medals.py --oneline    # single line for panel widgets
"""

import argparse
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

# Map IOC country codes to full names
IOC_CODES = {
    "AIN": "Individual Neutral Athletes",
    "ALB": "Albania", "AND": "Andorra", "ARG": "Argentina",
    "ARM": "Armenia", "AUS": "Australia", "AUT": "Austria",
    "AZE": "Azerbaijan", "BEL": "Belgium", "BIH": "Bosnia and Herzegovina",
    "BLR": "Belarus", "BOL": "Bolivia", "BRA": "Brazil",
    "BUL": "Bulgaria", "CAN": "Canada", "CHI": "Chile",
    "CHN": "China", "COL": "Colombia", "CRO": "Croatia",
    "CYP": "Cyprus", "CZE": "Czech Republic", "DEN": "Denmark",
    "ERI": "Eritrea", "ESP": "Spain", "EST": "Estonia",
    "FIN": "Finland", "FRA": "France", "GBR": "Great Britain",
    "GEO": "Georgia", "GER": "Germany", "GRE": "Greece",
    "HUN": "Hungary", "ICE": "Iceland", "IND": "India",
    "IRI": "Iran", "IRL": "Ireland", "ISR": "Israel",
    "ITA": "Italy", "JAM": "Jamaica", "JPN": "Japan",
    "KAZ": "Kazakhstan", "KGZ": "Kyrgyzstan", "KOR": "South Korea",
    "KOS": "Kosovo", "LAT": "Latvia", "LBN": "Lebanon",
    "LIE": "Liechtenstein", "LTU": "Lithuania", "LUX": "Luxembourg",
    "MDA": "Moldova", "MEX": "Mexico", "MGL": "Mongolia",
    "MKD": "North Macedonia", "MLT": "Malta", "MNE": "Montenegro",
    "MON": "Monaco", "NED": "Netherlands", "NEP": "Nepal",
    "NGR": "Nigeria", "NOR": "Norway", "NZL": "New Zealand",
    "PAK": "Pakistan", "PER": "Peru", "PHI": "Philippines",
    "POL": "Poland", "POR": "Portugal", "PRK": "North Korea",
    "PUR": "Puerto Rico", "ROU": "Romania", "RSA": "South Africa",
    "RUS": "Russia", "SLO": "Slovenia", "SMR": "San Marino",
    "SRB": "Serbia", "SUI": "Switzerland", "SVK": "Slovakia",
    "SWE": "Sweden", "THA": "Thailand", "TPE": "Chinese Taipei",
    "TUR": "Turkey", "UKR": "Ukraine", "USA": "United States",
    "UZB": "Uzbekistan",
}


def fetch_wikitext():
    """Fetch the medal table section wikitext from Wikipedia API."""
    req = urllib.request.Request(API_URL, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["parse"]["wikitext"]["*"]
    except Exception as e:
        print(f"Error fetching data: {e}", file=sys.stderr)
        sys.exit(1)


def parse_medals(wikitext):
    """
    Parse medal counts from wikitext.
    Format: | gold_NOR = 1 | silver_NOR = 1 | bronze_NOR = 1
    """
    # Strip HTML comments (which contain commented-out entries like AIN)
    clean = re.sub(r'<!--.*?-->', '', wikitext, flags=re.DOTALL)

    gold_pattern = re.compile(r'\|\s*gold_(\w+)\s*=\s*(\d+)')
    silver_pattern = re.compile(r'\|\s*silver_(\w+)\s*=\s*(\d+)')
    bronze_pattern = re.compile(r'\|\s*bronze_(\w+)\s*=\s*(\d+)')

    golds = {m.group(1): int(m.group(2)) for m in gold_pattern.finditer(clean)}
    silvers = {m.group(1): int(m.group(2)) for m in silver_pattern.finditer(clean)}
    bronzes = {m.group(1): int(m.group(2)) for m in bronze_pattern.finditer(clean)}

    all_codes = set(golds.keys()) | set(silvers.keys()) | set(bronzes.keys())

    results = []
    for code in all_codes:
        g = golds.get(code, 0)
        s = silvers.get(code, 0)
        b = bronzes.get(code, 0)
        total = g + s + b

        if total == 0:
            continue

        country_name = IOC_CODES.get(code, code)

        results.append({
            "rank": None,
            "code": code,
            "country": country_name,
            "gold": g,
            "silver": s,
            "bronze": b,
            "total": total,
        })

    # Sort: gold desc, silver desc, bronze desc, then code alphabetically
    results.sort(key=lambda x: (-x["gold"], -x["silver"], -x["bronze"], x["code"]))

    # Assign ranks with tie handling
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


def format_pretty(medals):
    """Pretty print the medal table."""
    if not medals:
        print("No medal data found.")
        return

    print(f"\n  {'#':<4} {'Country':<25} {'Code':<5} {'🥇':>4} {'🥈':>4} {'🥉':>4} {'Tot':>5}")
    print(f"  {'-' * 58}")

    for m in medals:
        print(
            f"  {m['rank']:<4} {m['country']:<25} {m['code']:<5} "
            f"{m['gold']:>4} {m['silver']:>4} {m['bronze']:>4} {m['total']:>5}"
        )

    total_g = sum(m["gold"] for m in medals)
    total_s = sum(m["silver"] for m in medals)
    total_b = sum(m["bronze"] for m in medals)
    total_t = sum(m["total"] for m in medals)
    print(f"  {'-' * 58}")
    print(
        f"  {'':4} {'Totals (' + str(len(medals)) + ' nations)':<25} {'':5} "
        f"{total_g:>4} {total_s:>4} {total_b:>4} {total_t:>5}"
    )
    print()


def main():
    parser = argparse.ArgumentParser(description="2026 Winter Olympics Medal Tracker")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument("--top", type=int, default=None, help="Show top N countries")
    parser.add_argument(
        "--country", type=str, default=None,
        help="Filter by country name or IOC code (partial match)"
    )
    parser.add_argument(
        "--oneline", action="store_true",
        help="Single line output for panel widgets"
    )
    args = parser.parse_args()

    wikitext = fetch_wikitext()
    medals = parse_medals(wikitext)

    if not medals:
        if args.oneline:
            print("🏅 No data")
        else:
            print("No medal data found.", file=sys.stderr)
        sys.exit(1)

    # Filter by country name or code
    if args.country:
        query = args.country.lower()
        medals = [
            m for m in medals
            if query in m["country"].lower() or query in m["code"].lower()
        ]

    # Limit to top N
    if args.top:
        medals = medals[:args.top]

    if args.oneline:
        show = medals[:3] if not args.country else medals
        parts = []
        for m in show:
            parts.append(f"{m['code']} {m['gold']}🥇{m['silver']}🥈{m['bronze']}🥉")
        print("🏅 " + " | ".join(parts))
    elif args.json:
        print(json.dumps(medals, indent=2, ensure_ascii=False))
    else:
        format_pretty(medals)


if __name__ == "__main__":
    main()
