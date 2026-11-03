import json

with open("backend/extracted_pages.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        row = json.loads(line)
        if row.get("year") == "2017" and row.get("page") == 46:
            print("FOUND PAGE 46:")
            print(repr(row.get("text")))
            print("\nPRINTED TEXT:")
            print(row.get("text"))
            break
