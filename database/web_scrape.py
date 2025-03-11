import time
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

# Path to ChromeDriver
driver_path = r"C:\Users\Justinas\Downloads\chromedriver-win64\chromedriver-win64\chromedriver.exe"

# Set up WebDriver
service = Service(driver_path)
driver = webdriver.Chrome(service=service)

# Open the models listing page
homepage_url = 'https://aihub.qualcomm.com/mobile/models?domain=Computer+Vision&useCase=Image+Classification'
driver.get(homepage_url)

# Wait for the page to fully load
wait = WebDriverWait(driver, 5)

# Function to click "Load More" button until all models are loaded
def load_all_models():
    while True:
        try:
            show_more_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, '//button[contains(., "Load More")]'))
            )
            driver.execute_script("arguments[0].scrollIntoView();", show_more_button)
            driver.execute_script("arguments[0].click();", show_more_button)
            time.sleep(2)  # Allow time for new content to load

        except (NoSuchElementException, TimeoutException):
            print("No more 'Load More' button found. All models should be loaded.")
            break
        except Exception as e:
            print(f"Error: {e}")
            break

# Load all models
load_all_models()

# Find all model links
model_links = driver.find_elements(By.XPATH, '//a[contains(@href, "/mobile/models/")]')

# Extract and store the full URLs
model_urls = list(set([link.get_attribute('href') for link in model_links]))  # Remove duplicates

# Prepare CSV file for writing model data
csv_file = 'models_data.csv'

# Function to extract model details dynamically
def extract_model_details():
    """Extracts all model details dynamically and expands 'See More Metrics' if available."""
    details = {}

    try:
        # Click "See More Metrics" if available
        try:
            more_metrics_button = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "See More Metrics")]'))
            )
            driver.execute_script("arguments[0].click();", more_metrics_button)
            time.sleep(2)  # Allow time for new metrics to load
        except (NoSuchElementException, TimeoutException):
            print("No 'See More Metrics' button found. Proceeding with available data.")

        # Find all divs containing model details
        info_divs = driver.find_elements(By.XPATH, '//div[@class="mb-2 last:mb-0"]')

        for div in info_divs:
            try:
                label = div.find_element(By.XPATH, './span[1]').text.strip().replace(":", "")
                value = div.find_element(By.XPATH, './span[2]').text.strip()
                details[label] = value
            except NoSuchElementException:
                continue  # Skip if structure is different

        # Retrieve additional metrics (inference time, memory usage, layers)
        try:
            inference_time = driver.find_element(By.XPATH, '//div[@data-testid="Inference Time"]//span[@class="text-h-xl"]').text.strip()
            details["Inference Time"] = inference_time
        except NoSuchElementException:
            details["Inference Time"] = "N/A"

        try:
            memory_usage = driver.find_element(By.XPATH, '//div[@data-testid="Memory Usage"]//span[@class="text-h-xl"]').text.strip()
            details["Memory Usage"] = memory_usage
        except NoSuchElementException:
            details["Memory Usage"] = "N/A"

        try:
            layers = driver.find_element(By.XPATH, '//div[@data-testid="Layers"]//span[@class="text-h-xl"]').text.strip()
            details["Layers"] = layers
        except NoSuchElementException:
            details["Layers"] = "N/A"

    except Exception as e:
        print(f"Error extracting details: {e}")

    return details

# Open CSV file for writing
with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    header = ["Model URL", "Inference Time", "Input resolution", "Layers", "Memory Usage", "Model checkpoint", "Model size", "Number of parameters"]

    # Write header only if there's data
    writer.writerow(header)

    # Iterate over each model's URL to scrape data
    for model_url in model_urls:
        try:
            driver.get(model_url)
            time.sleep(5)  # Wait for page to load

            # Extract model details
            model_data = extract_model_details()

            # Filter out keys that have no value (remove empty columns)
            model_data = {k: v for k, v in model_data.items() if v != "N/A"}

            # Add model URL to the data and write to CSV
            row = [model_url] + [model_data.get(field, "N/A") for field in header[1:]]
            writer.writerow(row)

            print(f"Scraped: {model_url}")

        except Exception as e:
            print(f"Error scraping {model_url}: {e}")

# Close WebDriver after scraping
driver.quit()

print(f"Data saved to {csv_file}")
