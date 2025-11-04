## Overview

This project automatically collects recent research papers from selected journals.  
It downloads new articles, filters for research content, formats them into a digest, and uploads the summary to Dropbox (manually at this moment, but it will be updated to run weekly).

The goal is to stay up to date with major discoveries even when daily workloads are overwhelming — without needing to manually browse journal websites or manage bookmarks.

## Workflow Summary

### 1. GitHub Action Automation

The automation is implemented using **GitHub Actions**, which runs the RSS-fetching script on a set schedule or manually when triggered.

**File structure:**
```
📂 Project Root
├── rss_feed_weekly.py              # Python script that fetches RSS feeds and uploads digest
└── .github/
    └── workflows/
        └── rss_feed_weekly.yaml    # GitHub Action configuration file
```

**Workflow description:**
- The Action installs Python and runs the `rss_feed_weekly.py` script.
- It reads the Dropbox access token from GitHub Secrets (`DROPBOX_TOKEN`).
- The job can be triggered manually (`workflow_dispatch`) or scheduled (e.g., every Monday at 8 AM UTC).
- After execution, a digest file is generated and uploaded to Dropbox automatically.

This setup makes the entire process fully automated and independent of local execution.

### 2. Dropbox Upload Integration

The Python script connects directly to Dropbox using the official REST API.  
After the digest file (`WeeklyDigest_YYYY-MM-DD.txt`) is created, it uploads it to the `/Apps/rss_uploader` folder in Dropbox.  
This allows you to access, read, or search weekly summaries from any synced device.

### 3. Python RSS Fetcher

The core script (`rss_feed_weekly.py`) uses only built-in Python libraries (`urllib`, `xml.etree.ElementTree`, `datetime`).  
It fetches multiple RSS feeds from the selected journals, parses XML data, and merges the results into one unified digest.  

No third-party dependencies or installations are needed, keeping it lightweight and fully compatible with GitHub’s hosted environment.

### 4. Abstract and Feed Validation

Testing confirmed that journal feeds behave differently:
- *Cell* includes abstracts in the `<description>` tag.  
- *Nature* and *Science* mostly include only issue metadata.

This helped determine which feeds provide usable summaries and identified where abstract extraction might need customization in future updates.

### 5. Research Article Filtering

The script filters feed entries to include only research-type content, excluding news or commentary.  
Journal-specific URL patterns are used:
- `/s` for *Nature*  
- `10.1126/science.` for *Science*  
- `/cell/fulltext/S` for *Cell*  

This ensures the digest highlights only original research papers.

### 6. Date Filtering (Past 7 Days)

Each article’s publication date is checked and compared to the current date.  
Only papers published within the last seven days are included.  
This keeps the digest relevant and avoids repeating older entries.

### 7. Digest Generation and Formatting

All selected articles are combined into a single file named `WeeklyDigest_YYYY-MM-DD.txt`.  
Each section of the file lists:
- Journal name  
- Article title  
- Publication date  
- URL  
- Abstract or summary (if available)

The digest is saved locally and automatically uploaded to Dropbox at the end of the run.

## Next Steps

- Optionally replace current journal RSS feeds with PubMed RSS feeds to include full abstracts.  
- Combine with ChatGPT for further analysis.