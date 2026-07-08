import requests
import config

def login():
    print(f"Logging in to {config.UPOS_LOGIN_URL}...")
    payload = {
        "username": config.UPOS_USERNAME,
        "password": config.UPOS_PASSWORD
    }
    response = requests.post(config.UPOS_LOGIN_URL, json=payload)
    if response.status_code == 200:
        data = response.json()
        token = data.get("data", {}).get("access_token")
        if token:
            print("Login successful.")
            return token
        else:
            print("Login response did not contain access_token.")
            print(data)
            return None
    else:
        print(f"Login failed: {response.status_code}")
        print(response.text)
        return None

def get_all_products(token):
    print(f"Fetching products from {config.UPOS_GET_ALL_PRODUCT_URL}...")
    headers = {
        "Authorization": f"Bearer {token}"
    }
    # Adjust payload if the API expects pagination or different body
    payload = {
        "page": 1,
        "limit": 10
    }
    response = requests.get(config.UPOS_GET_ALL_PRODUCT_URL, headers=headers, json=payload)
    if response.status_code == 405: # Method not allowed - maybe it's a POST?
        print("GET failed with 405 Method Not Allowed, trying POST...")
        response = requests.post(config.UPOS_GET_ALL_PRODUCT_URL, headers=headers, json=payload)
        
    if response.status_code == 200:
        data = response.json()
        if data.get("auth_status") == 401:
            print(f"Token expired (auth_status 401): {data.get('message')}")
            return False
            
        print("API Response keys:", data.keys())
        # Let's print out the total if it exists
        if "data" in data and isinstance(data["data"], dict):
            total = data["data"].get("total", "Unknown")
            print(f"Fetch successful! Total products: {total}")
        elif "data" in data and isinstance(data["data"], list):
            print(f"Fetch successful! Total products (array): {len(data['data'])}")
        else:
            print("API Response (No standard data format):", data)
        return True
    elif response.status_code == 401:
        print("Unauthorized (401) - Token is invalid or expired.")
        return False
    else:
        print(f"Fetch failed: {response.status_code}")
        print(response.text)
        return False

def main():
    token = config.UPOS_ACCESS_TOKEN
    success = False
    
    if token:
        success = get_all_products(token)
        
    if not success:
        print("\nAttempting to login to get a new token...")
        token = login()
        if token:
            get_all_products(token)

if __name__ == "__main__":
    main()
