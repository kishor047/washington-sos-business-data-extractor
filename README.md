# Washington SOS Business Data Extractor

This project is a Python-based web automation and scraping tool for collecting  
business entity data from the **Washington Secretary of State (SOS) – Corporation Search** portal.

The project is divided into **two separate scripts**:
- One script extracts **structured data and saves it in JSON format**
- Another script crawls and saves **raw HTML pages** for archival and debugging

Both scripts are **run independently**.

---

## 📂 Project Structure

```text
washington-sos-business-data-extractor/
│
├── data_extract.py          # Extracts structured business data (JSON)
├── crawling_data.py         # Crawls and saves raw HTML pages
│
├── data_extract/            # JSON output folder
│   ├── 123456789.json
│   └── 987654321.json
│
├── crawling_data/           # HTML crawling output
│   ├── 123456789.html
│   └── 987654321.html
│
├── requirements.txt
