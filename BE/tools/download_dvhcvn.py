import urllib.request
import os

def download_data():
    url = "https://raw.githubusercontent.com/daohoangson/dvhcvn/master/data/dvhcvn.json"
    dest_dir = os.path.dirname(os.path.abspath(__file__))
    dest_path = os.path.join(dest_dir, "dvhcvn.json")
    
    print(f"Downloading official dvhcvn.json to {dest_path}...")
    try:
        urllib.request.urlretrieve(url, dest_path)
        print("Download completed successfully!")
    except Exception as e:
        print("Failed to download:", e)

if __name__ == "__main__":
    download_data()
