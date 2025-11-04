# script.py (no pip install needed)
import os, json, urllib.request
from datetime import datetime

token = os.environ["DROPBOX_TOKEN"]

# Create a text file
filename = f"hello_{datetime.utcnow():%Y-%m-%d_%H-%M}.txt"
content = f"Hello from GitHub Actions! Time: {datetime.utcnow()} UTC\n"
with open(filename, "w") as f:
    f.write(content)

# Upload to Dropbox App Folder
url = "https://content.dropboxapi.com/2/files/upload"
headers = {
    "Authorization": f"Bearer {token}",
    "Dropbox-API-Arg": json.dumps({
        "path": f"/{filename}",
        "mode": "overwrite",
        "mute": False
    }),
    "Content-Type": "application/octet-stream",
}

with open(filename, "rb") as f:
    data = f.read()

req = urllib.request.Request(url, data=data, headers=headers, method="POST")
with urllib.request.urlopen(req) as resp:
    result = json.loads(resp.read().decode())
    print(f"✅ Uploaded to: {result['path_display']}")
    