import json
import re
from collections import Counter

TERMS = [
    "bedaquiline",
    "bpalm",
    "delamanid",
    "cbnaat",
    "truenat",
    "line probe assay",
    "shorter regimen",
    "adverse drug reaction",
    "infection control",
    "nikshay"
]

counts = {y: Counter() for y in ["2016", "2017", "2021", "2025"]}

with open("backend/extracted_pages.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        row = json.loads(line)
        year = str(row.get("year", ""))
        if year not in counts:
            continue
        text = str(row.get("text", "")).lower()
        for term in TERMS:
            occurrences = len(re.findall(r"\b" + re.escape(term) + r"\b", text))
            if occurrences > 0:
                counts[year][term] += occurrences

print("TERM FREQUENCY ACROSS GUIDELINES:")
for term in TERMS:
    print(f"{term:<25}: 2016={counts['2016'][term]:<4} 2017={counts['2017'][term]:<4} 2021={counts['2021'][term]:<4} 2025={counts['2025'][term]:<4}")
