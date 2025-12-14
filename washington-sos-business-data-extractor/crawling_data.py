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
from bs4 import BeautifulSoup
import traceback

# Create output directory
os.makedirs("html", exist_ok=True)

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

def search_to_main_url(driver, wait, letter):
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


def get_filing_history(driver, ubi):
    # filings = []
    try:
        # Check if Filing History button exists
        btn = driver.find_element(By.ID, "btnFilingHistory")
        print("    Loading Filing History...")
        click_element(driver, btn)
        time.sleep(10)  # Give time for the section to load
        wait_for_page_load(driver)
        filling_page = driver.page_source
        if ubi not in filling_page:
            # Return to company detail page
            print("    Returning from Filing History...")
            try:
                back_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Back') or contains(text(), 'Return')]")
                click_element(driver, back_btn)
            except:
                driver.back()
            time.sleep(5)
            return False
        else:
            # Return to company detail page
            print("    Returning from Filing History...")
            try:
                back_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Back') or contains(text(), 'Return')]")
                click_element(driver, back_btn)
            except:
                driver.back()
            time.sleep(5)
            return filling_page

    except NoSuchElementException:
        print("    No Filing History button found (some entities may not have detailed filings).")
        return False
    except Exception as e:
        print(f"    Error accessing Filing History: {e}")
        # Attempt recovery
        try:
            driver.back()
            time.sleep(5)
        except:
            return False


def get_name_change_history(driver, ubi):
    # changes = []
    try:
        # Try to open Name History if the button exists
        btn = driver.find_element(By.ID, "btnNameHistory")
        print("    Loading Name History (dedicated section found)...")
        click_element(driver, btn)
        time.sleep(10)
        wait_for_page_load(driver)
        name_history = driver.page_source
        if ubi not in name_history:
            back_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Back')]")
            click_element(driver, back_btn)
            time.sleep(5)
            return False
        else:
            back_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Back')]")
            click_element(driver, back_btn)
            time.sleep(5)
            return name_history
    except NoSuchElementException:
        print("    No Filing History button found (some entities may not have detailed filings).")
        return False
    except Exception as e:
        print(f"    Error accessing Filing History: {e}")
        # Attempt recovery
        try:
            driver.back()
            time.sleep(5)
        except:
            return False
        

def process_single_company(driver, link, idx):
    try:
        company_name = link.text.strip()
        print(f"\n  [{idx}] Processing: {company_name}")

        click_element(driver, link)
        time.sleep(15)
        main_page = driver.page_source
        soup = BeautifulSoup(main_page, "html.parser")
        ubi = soup.find("strong", attrs={"data-ng-bind": "businessInfo.UBINumber"}).get_text(strip=True)
        print(ubi)
        if ubi:
            filing_history = get_filing_history(driver, ubi)
            name_history = get_name_change_history(driver, ubi)

            all_company_page = main_page + filing_history + name_history
            with open(f"html/{ubi}.html", "w", encoding="utf-8") as f:
                f.write(all_company_page)
                print(f"saved {ubi}.html")

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
        print(traceback.format_exc())
        try:
            driver.back()
            time.sleep(5)
        except:
            pass
        return False

def get_current_page_data(driver):
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

def scrape_companies_by_letter(driver, wait, letter):
    if not search_to_main_url(driver, wait, letter):
        return 0

    total = 0
    page = 1
    while True:
        print(f"\n  --- Processing Page {page} for letter '{letter}' ---")
        count = get_current_page_data(driver)
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
            count = scrape_companies_by_letter(driver, wait, letter)
            total_companies += count
            print(f"\nLetter '{letter}' completed: {count} companies scraped.")
        except Exception as e:
            print(f"\nError on letter '{letter}': {e}")

    print("SCRAPING FINISHED")
    
    driver.quit()

if __name__ == "__main__":
    main()