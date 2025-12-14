# Washington SOS Business Data Extractor

This project is a Python-based web automation and scraping tool that collects  
business entity information from the **Washington Secretary of State (SOS) – Corporation Search** portal.

The project contains **two independent Python scripts**:
- One script extracts **structured data and saves it in JSON format**
- Another script crawls and saves **raw HTML pages**

Each script is executed **separately**.

---

## 📂 Project Structure

```text
washington-sos-business-data-extractor/
│
├── data_extract.py          # Extracts structured business data (JSON)
├── crawling_data.py         # Crawls and saves raw HTML pages (HTML)
│
├── data_extract/            # JSON output folder
│   ├── 123456789.json
│
├── crawling_data/           # HTML crawling output folder
│   ├── 123456789.html
│
├── requirements.txt

🔍 Features
Business search using name patterns (e.g., AA, AAB)

Handles Cloudflare-protected pages

Pagination handling

Human-like behavior (random delays and JS-based clicks)

Two independent execution modes:

JSON Data Extraction

HTML Crawling & Archiving

🛠 Tech Stack
Python 3.9+

Selenium

Undetected ChromeDriver

BeautifulSoup (bs4)

Google Chrome

📦 Installation
1️⃣ Clone the Repository
bash
Copy code
git clone https://github.com/kishor047/washington-sos-business-data-extractor.git
cd washington-sos-business-data-extractor
2️⃣ Create Virtual Environment (Recommended)
bash
Copy code
python -m venv venv
source venv/bin/activate     # Windows: venv\Scripts\activate
3️⃣ Install Required Packages
bash
Copy code
pip install -r requirements.txt
▶️ How to Run the Scripts
🔹 Run JSON Data Extraction
Extracts structured business information and saves it in JSON format.

bash
Copy code
python data_extract.py
📁 Output directory:

Copy code
data_extract/
🔹 Run HTML Crawling
Crawls and saves complete business pages in HTML format.

bash
Copy code
python crawling_data.py
📁 Output directory:

Copy code
crawling_data/
📤 Output Examples
🔹 JSON Output
json
Copy code
{
  "ubi_number": "123456789",
  "business_name": "ABC TECHNOLOGIES LLC",
  "status": "Active",
  "jurisdiction": "Washington"
}
🔹 HTML Output
Company detail page

Filing history page

Name change history page

Stored as raw HTML for archival and debugging

⚠️ Important Notes
Do not close the browser while the script is running

Cloudflare challenges may take time to resolve

Website structure changes may require selector updates

Large HTML files should be ignored using .gitignore

