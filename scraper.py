from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import json
import time

# Define input and output file paths (use relative paths for Gitpod)
input_file = "converted_data.json"  # Make sure this file is in the same Gitpod directory
output_file = "scraped_contractor_data.json"

# Load JSON data
with open(input_file, "r", encoding="utf-8") as f:
    data = json.load(f)

# Filter data (numbers 1-5)
filtered_data = [entry for entry in data if 1 <= entry["Number"] <= 1000]

# Function to scrape each contractor page
def scrape_contractor(entry):
    grid_url = "http://localhost:4444/wd/hub"  # Selenium Grid Hub URL
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    
    driver = webdriver.Remote(command_executor=grid_url, options=chrome_options)
    wait = WebDriverWait(driver, 3)

    url = entry["contractor"]
     number = entry["Number"]
            page = entry['page']
    try:
        driver.get(url)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        try:
            contractor_name = wait.until(EC.presence_of_element_located(
                (By.CLASS_NAME, "card-title")
            )).text
        except TimeoutException:
            contractor_name = None

        info = {
             "URL": url,
                "Contractor Name": contractor_name,
                "page": page,
                "number":number,
                "رقم العضويه": None,
                "حجم المنشأة": None,
                "عدد الساعات التدريبية": None,
                "العضوية": None,
                "المدينة": None,
                "المنطقه": None,
                "رقم الجوال": None,
                "الخدمة": None,
                "عنوان": None,
                "عضو منذ": None,
                "البريد الإلكترونى": None,
        }

        info_elements = driver.find_elements(By.CLASS_NAME, "info-name")
        
        for element in info_elements:
            key = element.text.strip()
            try:
                value_element = element.find_element(By.XPATH, "following-sibling::div[@class='info-value']")
                value = value_element.text.strip()
                
                if key in info:
                    info[key] = value
            except NoSuchElementException:
                continue

        try:
            activities_table = driver.find_element(By.CSS_SELECTOR, "table.table")
            activities = [row.text for row in activities_table.find_elements(By.TAG_NAME, "tr")[1:]]
            info["الأنشطة"] = activities
        except NoSuchElementException:
            info["الأنشطة"] = []

    except Exception as e:
        print(f"Error processing {url}: {str(e)}")
    finally:
        driver.quit()
    
    return info

# Use ThreadPoolExecutor to run scraping concurrently
scraped_data = []
with ThreadPoolExecutor(max_workers=10) as executor:
    future_to_entry = {executor.submit(scrape_contractor, entry): entry for entry in filtered_data}
    for future in as_completed(future_to_entry):
        scraped_data.append(future.result())
        print(f"Successfully scraped data for: {future_to_entry[future]['contractor']}")

# Save scraped data
with open(output_file, "w", encoding="utf-8") as json_outfile:
    json.dump(scraped_data, json_outfile, ensure_ascii=False, indent=4)

print(f"Scraping complete. Data saved to '{output_file}'")
