import os
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import html, json

# --------------------------------------------------
# Helper functions
# --------------------------------------------------

def clean_text(text):
    """Remove HTML tags and decode entities."""
    if not text:
        return ""
    text = html.unescape(text)
    return text.strip()

def extract_doi_and_pmid(item):
    """Extract DOI and PMID from dc:identifier fields."""
    dois, pmids = [], []
    for elem in item.findall(".//{*}identifier"):
        val = elem.text.strip()
        if val.startswith("doi:"):
            dois.append(val.replace("doi:", "").strip())
        elif val.startswith("pmid:"):
            pmids.append(val.replace("pmid:", "").strip())
    return (dois[0] if dois else ""), (pmids[0] if pmids else "")

# --------------------------------------------------
# Fetch and parse feed
# --------------------------------------------------

def fetch_pubmed_feed(feed_name, url):
    """Fetch and parse a PubMed RSS feed."""
    print(f"\n=== Fetching {feed_name.upper()} feed ===")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
    except Exception as e:
        print(f"❌ Error fetching {feed_name}: {e}")
        return []

    root = ET.fromstring(data)
    items = root.findall(".//item")

    results = []
    for item in items:
        title = clean_text(item.findtext("title", ""))
        abstract = clean_text(item.findtext("description", ""))
        pubdate = clean_text(item.findtext("{*}date", "") or item.findtext("pubDate", ""))
        journal = clean_text(item.findtext("{*}source", ""))
        doi, pmid = extract_doi_and_pmid(item)
        results.append({
            "title": title,
            "abstract": abstract,
            "date": pubdate,
            "journal": journal,
            "pmid": pmid,
            "doi": doi
        })
    print(f"✅ {len(results)} items parsed from {feed_name}")
    return results

# --------------------------------------------------
# Main workflow
# --------------------------------------------------

feeds = {
    "general": "https://pubmed.ncbi.nlm.nih.gov/rss/search/1b7rv9zNdqwv4DwC9pDjXKQAZH0MXsZGaBfVarIwOKOpgqHQy6/?limit=200",
    "immune": "https://pubmed.ncbi.nlm.nih.gov/rss/search/1ZOXa2PYRt-OlyyGkx28QJAQ_fXoQVYyQVLqj2sT7-CEDm4YbG/?limit=200",
    "cancer": "https://pubmed.ncbi.nlm.nih.gov/rss/search/1nQmw1FvDkC1rwg15ohSrbNEmZQtnwqCr3-xVkm2BnVJrWyMfO/?limit=200",
}

timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")

for feed_name, feed_url in feeds.items():
    entries = fetch_pubmed_feed(feed_name, feed_url)
    if not entries:
        print(f"⚠️ No entries found for {feed_name}.")
        continue

    digest_file = f"WeeklyDigest_{feed_name}_{timestamp}.txt"
    with open(digest_file, "w", encoding="utf-8") as f:
        f.write(f"# 🧠 Weekly Research Digest — {feed_name.capitalize()} ({timestamp})\n\n")
        for e in entries:
            f.write(f"**Title:** {e['title']}\n")
            f.write(f"**Abstract:** {e['abstract'] if e['abstract'] else 'N/A'}\n")
            f.write(f"**Publication Date:** {e['date']}\n")
            f.write(f"**Journal:** {e['journal']}\n")
            f.write(f"**PubMed ID:** {e['pmid']}\n")
            f.write(f"**DOI:** {e['doi']}\n")
            f.write("-" * 60 + "\n\n")

    print(f"📝 Saved digest file: {digest_file}")

    # --------------------------------------------------
    # Upload to Dropbox (if token provided)
    # --------------------------------------------------
    token = os.environ.get("DROPBOX_TOKEN")
    if token and os.path.exists(digest_file):
        date_dir = timestamp  # e.g. "2025-11-04"
        dropbox_path = f"/{date_dir}/{digest_file}"

        print(f"📤 Uploading {feed_name} digest to Dropbox → {dropbox_path}")

        url = "https://content.dropboxapi.com/2/files/upload"
        headers = {
            "Authorization": f"Bearer {token}",
            "Dropbox-API-Arg": json.dumps({
                "path": dropbox_path,
                "mode": "overwrite",
                "mute": False
            }),
            "Content-Type": "application/octet-stream",
        }

        with open(digest_file, "rb") as f:
            data = f.read()

        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req) as resp:
                result = json.loads(resp.read().decode())
                print(f"✅ Uploaded to Dropbox: {result['path_display']}")
        except urllib.error.HTTPError as e:
            print(f"⚠️ Dropbox upload failed ({e.code} {e.reason}) — check token or app folder.")
        except Exception as e:
            print(f"⚠️ Dropbox upload error: {e}")
    else:
        print(f"⚠️ Dropbox upload skipped for {feed_name} (no token found).")


print("\n✅ All feeds processed successfully.")