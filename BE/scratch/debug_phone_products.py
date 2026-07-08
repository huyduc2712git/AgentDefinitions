import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.append('.')
import requests
import config
from services.upos_auth import call_with_auth

# Gọi API UPOS TRUYỀN THAM SỐ keyword giống hệt như Postman/Screenshot của user
print("Fetching from UPOS with keyword='điện thoại'...")
resp = call_with_auth('GET', f"{config.UPOS_SEARCH_PRODUCT_URL}?keyword=điện thoại")
data = resp.json().get('data', [])
if isinstance(data, dict):
    data = data.get('data', [])

print(f"UPOS API returned {len(data)} items:")
for idx, item in enumerate(data):
    print(f"{idx+1}. Name: {item.get('product_name') or item.get('name')} | Status: {item.get('status')}")
