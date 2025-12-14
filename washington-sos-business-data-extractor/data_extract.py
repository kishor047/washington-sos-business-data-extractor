import os
import json
import time
import datetime
import re
import random
import string
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import *
import undetected_chromedriver as uc

# Create output directory
os.makedirs("companies_json", exist_ok=True)

def create_web_driver():
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")

    driver = uc.Chrome(
        options=options,
        headless=False,
        use_subprocess=True,
        version_main=142,
    )
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def random_delay(min_sec=1, max_sec=3):
    time.sleep(random.uniform(min_sec, max_sec))

def wait_for_page_load(driver, timeout=10):
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
    except:
        pass

def click_element(driver, element):
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
    random_delay(0.5, 1)
    driver.execute_script("arguments[0].click();", element)
    random_delay(1, 2)

def navigate_and_search(driver, wait, letter):
    print("* * " * 15)
    print(f"Starting search for letter  with: '{letter}'")
    print("* * " * 15)

    print("Opening  website...")
    driver.get("https://ccfs.sos.wa.gov/")
    wait_for_page_load(driver)

    print("\n" + "=" * 60)
    print("Please watch the browser Dont Close:")
    print("* * " * 15)

    random_delay(3, 5)
    print(f"Current URL: {driver.current_url}")

    # Try to enter search section if needed
    if "BusinessSearch" not in driver.current_url and "#/" not in driver.current_url:
        print("Attempting to open search form...")
        try:
            search_header = driver.find_element(By.XPATH, "//h3[contains(text(), 'Corporation Search')]")
            click_element(driver, search_header)
            random_delay(2, 4)
        except:
            pass

    # Select "Contains With"
    try:
        begins_with = driver.find_element(By.ID, "rdoContains")
        click_element(driver, begins_with)
        print("Selected 'Contains With' option")
    except:
        try:
            begins_with = driver.find_element(By.XPATH, "//input[@value='StartsWith']")
            click_element(driver, begins_with)
            print("Selected 'Contains With' (alternative)")
        except:
            print("Warning: Could not select 'Contains With'")

    random_delay(1, 2)

    # Type the letter
    search_input = driver.find_element(By.ID, "BusinessName")
    search_input.clear()
    for char in letter:
        search_input.send_keys(char)
        time.sleep(0.1)

    random_delay(1, 2)

    # Click search
    search_btn = driver.find_element(By.CSS_SELECTOR, ".btn-search")
    print("Performing search...")
    click_element(driver, search_btn)

    print("Waiting for results (may take time due to Cloudflare)...")
    time.sleep(15)
    wait_for_page_load(driver)

    # Check results
    for _ in range(5):
        if "Business Search Results" in driver.page_source:
            print("Results page loaded successfully.")
            return True
        if "No Value Found" in driver.page_source:
            print(f"No companies found for letter '{letter}'")
            return False
        time.sleep(3)

    print("Failed to load results. Saving debug page...")

    return False

def extract_company_basic_data(driver):
    data = {
        "company_name": "Unknown Company",
        "ubi": "000000000",
        "business_information": {},
        "registered_agent": {},
        "governors": [],
    }

    # Company Name
    try:
        el = driver.find_element(By.XPATH, "//div[contains(text(), 'Business Name:')]/following-sibling::div//strong")
        data["company_name"] = el.text.strip()
    except:
        try:
            el = driver.find_element(By.XPATH, "//strong[@data-ng-bind='businessInfo.BusinessName']")
            data["company_name"] = el.text.strip()
        except:
            pass

    # UBI
    try:
        el = driver.find_element(By.XPATH, "//div[contains(text(), 'UBI Number:')]/following-sibling::div//strong")
        data["ubi"] = re.sub(r"\D", "", el.text.strip())
    except:
        try:
            el = driver.find_element(By.XPATH, "//strong[@data-ng-bind='businessInfo.UBINumber']")
            data["ubi"] = re.sub(r"\D", "", el.text.strip())
        except:
            pass

    # Business Information
    try:
        rows = driver.find_elements(By.XPATH, "//div[contains(text(), 'Business Information')]/following-sibling::div//div[@class='row']")
        for row in rows:
            cols = row.find_elements(By.CSS_SELECTOR, "div")
            if len(cols) >= 4:
                label1 = cols[0].text.strip().rstrip(":").strip()
                value1 = cols[1].text.strip()
                label2 = cols[2].text.strip().rstrip(":").strip()
                value2 = cols[3].text.strip()
                if label1 and value1:
                    data["business_information"][label1] = value1
                if label2 and value2:
                    data["business_information"][label2] = value2
    except Exception as e:
        print(f"    Warning: Business info extraction issue: {e}")

    # Registered Agent
    try:
        if "Registered Agent Information" in driver.page_source:
            section = driver.find_element(By.XPATH, "//div[contains(text(), 'Registered Agent Information')]/following-sibling::div")
            rows = section.find_elements(By.CSS_SELECTOR, ".row")
            for row in rows:
                text = row.text
                if "Registered Agent Name:" in text:
                    try:
                        data["registered_agent"]["name"] = row.find_element(By.TAG_NAME, "b").text.strip()
                    except:
                        data["registered_agent"]["name"] = text.split("Registered Agent Name:")[1].strip()
                if "Street Address:" in text:
                    try:
                        data["registered_agent"]["street_address"] = row.find_element(By.TAG_NAME, "strong").text.strip()
                    except:
                        data["registered_agent"]["street_address"] = text.split("Street Address:")[1].strip()
    except Exception as e:
        print(f"    Warning: Agent extraction issue: {e}")

    # Governors
    try:
        if "Governors" in driver.page_source:
            table = driver.find_element(By.XPATH, "//div[contains(text(), 'Governors')]/following-sibling::div//table")
            rows = table.find_elements(By.TAG_NAME, "tr")
            for row in rows[1:]:
                cols = row.find_elements(By.TAG_NAME, "td")
                if len(cols) >= 5:
                    gov = {
                        "title": cols[0].text.strip(),
                        "type": cols[1].text.strip(),
                        "entity_name": cols[2].text.strip(),
                        "first_name": cols[3].text.strip(),
                        "last_name": cols[4].text.strip(),
                    }
                    if gov["first_name"] or gov["last_name"] or gov["entity_name"]:
                        data["governors"].append(gov)
    except Exception as e:
        print(f"    Warning: Governors extraction issue: {e}")

    return data


def get_filing_history(driver):
    filings = []
    try:
        # Check if Filing History button exists
        btn = driver.find_element(By.ID, "btnFilingHistory")
        print("    Loading Filing History...")
        click_element(driver, btn)
        time.sleep(10)  # Give time for the section to load
        wait_for_page_load(driver)

        # Try primary table locator (most common)
        try:
            table = driver.find_element(By.XPATH, "//table[.//th[contains(text(), 'Filing Number') or contains(text(), 'Filing Date')]]")
            rows = table.find_elements(By.TAG_NAME, "tr")
            for row in rows[1:]:  # Skip header row
                cols = row.find_elements(By.TAG_NAME, "td")
                if len(cols) >= 4:
                    filing = {
                        "filing_number": cols[0].text.strip(),
                        "filing_date_time": cols[1].text.strip(),
                        "effective_date": cols[2].text.strip(),
                        "filing_type": cols[3].text.strip(),
                    }
                    if len(cols) > 4:
                        filing["action"] = cols[4].text.strip()
                    filings.append(filing)
            print(f"    Successfully extracted {len(filings)} filing records.")
        
        except NoSuchElementException:
            # Fallback: Try any table that mentions common filing keywords
            print("    Primary filing table not found. Trying alternative tables...")
            tables = driver.find_elements(By.TAG_NAME, "table")
            for table in tables:
                table_text = table.text.lower()
                if any(keyword in table_text for keyword in ["filing number", "annual report", "filing date", "filing type"]):
                    rows = table.find_elements(By.TAG_NAME, "tr")
                    for row in rows[1:]:
                        cols = row.find_elements(By.TAG_NAME, "td")
                        if len(cols) >= 4:
                            filing = {
                                "filing_number": cols[0].text.strip(),
                                "filing_date_time": cols[1].text.strip(),
                                "effective_date": cols[2].text.strip(),
                                "filing_type": cols[3].text.strip(),
                            }
                            filings.append(filing)
                    if filings:
                        print(f"    Extracted {len(filings)} filings from alternative table.")
                        break

        # Return to company detail page
        print("    Returning from Filing History...")
        try:
            back_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Back') or contains(text(), 'Return')]")
            click_element(driver, back_btn)
        except:
            driver.back()
        time.sleep(5)

    except NoSuchElementException:
        print("    No Filing History button found (some entities may not have detailed filings).")
    
    except Exception as e:
        print(f"    Error accessing Filing History: {e}")
        # Attempt recovery
        try:
            driver.back()
            time.sleep(5)
        except:
            pass

    return filings

def get_name_change_history(driver):
    changes = []
    try:
        # Try to open Name History if the button exists
        btn = driver.find_element(By.ID, "btnNameHistory")
        print("    Loading Name History (dedicated section found)...")
        click_element(driver, btn)
        time.sleep(10)
        wait_for_page_load(driver)

        # Try to extract from dedicated name history table
        try:
            table = driver.find_element(By.XPATH, "//table[.//th[contains(text(), 'Old Name') or contains(text(), 'Previous Name')]]")
            rows = table.find_elements(By.TAG_NAME, "tr")
            for row in rows[1:]:
                cols = row.find_elements(By.TAG_NAME, "td")
                if len(cols) >= 3:
                    changes.append({
                        "old_name": cols[1].text.strip() if len(cols) > 1 else "",
                        "new_name": cols[2].text.strip() if len(cols) > 2 else "",
                        "created_date": cols[3].text.strip() if len(cols) > 3 else "",
                        "filing_number": cols[0].text.strip() if len(cols) > 0 else "",
                    })
            print(f"    Found {len(changes)} name changes in dedicated section.")
        except:
            print("    No name history table found even after clicking button.")

        # Return to main page
        back_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Back')]")
        click_element(driver, back_btn)
        time.sleep(5)

    except NoSuchElementException:
        # No dedicated Name History button - this is normal for most companies
        print("    No dedicated Name History section (common - company likely never changed name).")
    
    except Exception as e:
        print(f"    Error accessing dedicated Name History: {e}")
        try:
            driver.back()
            time.sleep(5)
        except:
            pass

    # Fallback: Scan Filing History for name change filings (if we already have it or can get it)
    # Note: If you already extracted filing_history earlier, you could pass it in, but for simplicity we skip re-extracting here
    # Or add a quick check if "name change" appears in any filing type on the main page source
    if not changes and "name change" in driver.page_source.lower():
        print("    Hint: Possible name change mentioned, but no dedicated history - check Filing History manually for 'AMENDMENT' or 'NAME CHANGE' filings.")

    return changes

# def get_name_change_history(driver):
#     changes = []
#     try:
#         btn = driver.find_element(By.ID, "btnNameHistory")
#         print("    Loading Name History...")
#         click_element(driver, btn)
#         time.sleep(10)
#         wait_for_page_load(driver)

#         table = driver.find_element(By.XPATH, "//table[.//th[contains(text(), 'Old Name')]]")
#         rows = table.find_elements(By.TAG_NAME, "tr")
#         for row in rows[1:]:
#             cols = row.find_elements(By.TAG_NAME, "td")
#             if len(cols) >= 4:
#                 changes.append({
#                     "filing_number": cols[0].text.strip(),
#                     "old_name": cols[1].text.strip(),
#                     "new_name": cols[2].text.strip(),
#                     "created_date": cols[3].text.strip(),
#                 })

#         back_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Back')]")
#         click_element(driver, back_btn)
#         time.sleep(5)
#     except Exception as e:
#         print(f"    Error in name history: {e}")
#         try:
#             driver.back()
#             time.sleep(5)
#         except:
#             pass
#     return changes

def process_single_company(driver, link, idx):
    try:
        company_name = link.text.strip()
        print(f"\n  [{idx}] Processing: {company_name}")

        click_element(driver, link)
        time.sleep(8)

        basic_data = extract_company_basic_data(driver)
        filing_history = get_filing_history(driver)
        name_history = get_name_change_history(driver)

        full_data = {
            "company_name": basic_data["company_name"],
            "ubi": basic_data["ubi"],
            "business_information": basic_data["business_information"],
            "registered_agent": basic_data["registered_agent"],
            "governors": basic_data["governors"],
            "filing_history": filing_history,
            "name_change_history": name_history,
        }

        ubi = basic_data["ubi"] if basic_data["ubi"] != "000000000" else f"unknown_{int(time.time())}"
        filename = f"companies_json/{ubi}.json"

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(full_data, f, indent=4, ensure_ascii=False)

        print(f"  Saved: {ubi}.json | Governors: {len(basic_data['governors'])}, Filings: {len(filing_history)}, Name Changes: {len(name_history)}")

        print("  Returning to results...")
        try:
            back_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Back')]")
            click_element(driver, back_btn)
        except:
            driver.back()
        time.sleep(5)
        return True
    except Exception as e:
        print(f"  Failed to process company: {e}")
        try:
            driver.back()
            time.sleep(5)
        except:
            pass
        return False

def process_current_results_page(driver):
    links = driver.find_elements(By.XPATH, "//table//tbody//tr/td[1]/a")
    if not links:
        print("  No companies found on this page.")
        return 0

    print(f"  Found {len(links)} companies on this page.")
    processed = 0

    for i in range(len(links)):
        try:
            current_links = driver.find_elements(By.XPATH, "//table//tbody//tr/td[1]/a")
            if i < len(current_links):
                if process_single_company(driver, current_links[i], i + 1):
                    processed += 1
            if i < len(links) - 1:
                random_delay(2, 4)
        except Exception as e:
            print(f"  Error on company {i+1}: {e}")
    return processed

def go_to_next_page(driver):
    try:
        next_btn = driver.find_element(By.XPATH, "//a[text()='>' and not(contains(@class, 'disabled'))]")
        driver.execute_script("arguments[0].scrollIntoView();", next_btn)
        random_delay(1, 2)
        driver.execute_script("arguments[0].click();", next_btn)
        time.sleep(8)
        wait_for_page_load(driver)
        print("  Moved to next page.")
        return True
    except:
        print("  No more pages.")
        return False

def scrape_companies_for_letter(driver, wait, letter):
    if not navigate_and_search(driver, wait, letter):
        return 0

    total = 0
    page = 1
    while True:
        print(f"\n  --- Processing Page {page} for letter '{letter}' ---")
        count = process_current_results_page(driver)
        total += count
        print(f"  Page {page} done: {count} companies.")
        if not go_to_next_page(driver):
            break
        page += 1
    return total

def main():


    driver = create_web_driver()
    wait = WebDriverWait(driver, 30)
    total_companies = 0
    letter_list=["AA","AAB"]
    for letter in letter_list:
        try:
            count = scrape_companies_for_letter(driver, wait, letter)
            total_companies += count
            print(f"\nLetter '{letter}' completed: {count} companies scraped.")
        except Exception as e:
            print(f"\nError on letter '{letter}': {e}")

    print("SCRAPING FINISHED")
    
    driver.quit()

if __name__ == "__main__":
    main()