import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.append('.')
import config
from services.upos_auth import call_with_auth

resp = call_with_auth("GET", config.UPOS_SEARCH_PRODUCT_URL)
body = resp.json()
raw_items = body.get("data", [])

query = "áo hoodie"
keywords = [k.lower() for k in query.split() if k]

print("Keywords:", keywords)
print("Total raw items:", len(raw_items))

matched = []
for item in raw_items:
    name = str(item.get("name", "") or item.get("product_name", "")).lower()
    item_status = str(item.get("status", "1"))
    
    # Let's print matches for keywords
    if "hoodie" in name:
        print(f"Found hoodie product: '{name}' | Status: {item_status}")
        matches = [kw in name for kw in keywords]
        print(f"  Keywords match: {matches} -> all: {all(matches)}")
        if item_status in ("0", "inactive", "disabled"):
            print("  Filtered out: status inactive")
