import os
import datetime
import pandas as pd
import numpy as np
import time
from selenium.common.exceptions import NoSuchElementException
from selenium import webdriver
from selenium.webdriver.common.by import By
import random
from tqdm import tqdm
from Utils import wait_for_ajax
import unicodedata
from Utils import get_all_apps_of_category_google
from EmailSender import send_email
from Google_Ranker import get_google_ranking_all
import logging
import threading

#region loggingsystem
class ListHandler(logging.Handler):
    def __init__(self, log_list):
        super().__init__()
        self.log_list = log_list  # This will hold the logs

    def emit(self, record):
        log_entry = self.format(record)  # Format the log message
        self.log_list.append(log_entry)  # Append to the log list

# Initialize the log list
log_list = []

# Set up the basic logging configuration
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%d/%m/%Y %H:%M:%S')

# Get the root logger
logger = logging.getLogger()

# Create and add the custom ListHandler
list_handler = ListHandler(log_list)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s',
                              datefmt='%d/%m/%Y %H:%M:%S')
list_handler.setFormatter(formatter)  # Apply the same formatter as in basicConfig
logger.addHandler(list_handler)  # Add the handler to the logger
#endregion

def Google(categories, test=False, country="DE", initial_date = str(datetime.datetime.now().date())):
    os.makedirs("./data/Google/", exist_ok=True)
    out_path = "./data/Google/" + initial_date + "/" + country + "/"
    privacy_path = out_path + "/privacy/"
    source_path = out_path + "/source/"
    os.makedirs(out_path, exist_ok=True)
    os.makedirs(privacy_path, exist_ok=True)
    os.makedirs(source_path, exist_ok=True)

    base_url = "https://play.google.com"

    driver = webdriver.Firefox()

    logging.info(f"starting google ranking")
    try:
        rank_info, all_rank_links = get_google_ranking_all(country=country, driver=driver, out_path=out_path, app_categories=categories)
    except Exception as e:
        logging.critical(f"google ranking failed {e}")
        driver.close()
        return

    logging.info("google ranking finished.")
    logging.info("getting all apps of category google")

    all_google_scrape = get_all_apps_of_category_google(categories=categories, country=country)
    google_apps = list(set(all_rank_links + all_google_scrape))
    pd.DataFrame(google_apps, columns=["links"]).to_csv(out_path + "/google_apps.csv", index=False)
    logging.info("loaded all apps of category google")

    if np.nan in google_apps:
        google_apps.remove(np.nan)
    google_apps = [base_url + x if base_url not in x else x for x in google_apps]
    google_apps = [x for x in google_apps if x != "https://play.google.com/store/games"]

    def get_values(driver):
        try:
            app_name = driver.find_element(By.TAG_NAME, "h1").text
        except NoSuchElementException:
            return []
        try:
            dev = driver.find_element(By.XPATH, "//a[contains(@href, '/store/apps/developer?id=')]").text
        except NoSuchElementException:
            try:
                dev = driver.find_element(By.XPATH, "//a[contains(@href, '/store/apps/dev?id=')]").text
            except NoSuchElementException:
                dev = ""

        try:
            tags = driver.find_elements(By.XPATH,
                                        "//a[contains(@href, '/store/apps/developer?id=')]/parent::div/following-sibling::div/div/span")
            tags = "|".join([x.text for x in tags])
        except NoSuchElementException:
            try:  # hier auch
                tags = driver.find_elements(By.XPATH,
                                            "//a[contains(@href, '/store/apps/dev?id=')]/parent::div/following-sibling::div/div/span")
                tags = "|".join([x.text for x in tags])
            except NoSuchElementException:
                tags = ""
        if not tags:
            tags = ""

        try:
            categories = driver.find_elements(By.XPATH,
                                              "//a[contains(@href, '/store/apps/category/')]/preceding-sibling::span")
            categories = "|".join([x.text for x in categories])
        except NoSuchElementException:
            categories = ""

        try:
            price = driver.find_element(By.XPATH,
                                        "//button[contains(@aria-label, 'Buy')]/preceding-sibling::span").text
        except NoSuchElementException:
            try:
                price = driver.find_element(By.XPATH,
                                        "//button[contains(@aria-label, 'Install')]/preceding-sibling::span").text
            except NoSuchElementException:
                    price = ""

        try:
            description = driver.find_element(By.XPATH,
                                              "//meta[contains(@itemprop,'description')]/following-sibling::div[1]").text
        except NoSuchElementException:
            description = ""

        # TODO: Nimmt aktuell nur Bewertungen vom Handy
        try:
            review_count = driver.find_element(By.XPATH,
                                               "//h2[text() = 'Ratings and reviews']/../../../following-sibling::div/div/div/div/div/div/div[3]").text
        except NoSuchElementException:
            review_count = ""

        try:
            review_average = driver.find_element(By.XPATH,
                                                 "//h2[text() = 'Ratings and reviews']/../../../following-sibling::div/div/div/div/div/div/div[1]").text
        except NoSuchElementException:
            review_average = ""

        review_stars = driver.find_elements(By.XPATH,
                                            "//h2[text() = 'Ratings and reviews']/../../../following-sibling::div/div/div/div/div/div[2]/div")

        if not review_stars:
            review_stars = [""] * 5
        if review_stars[0] != "":
            review_stars = [x.get_attribute("aria-label") for x in review_stars][::-1]
            review_stars = [unicodedata.normalize("NFKD", x) for x in review_stars]
        try:
            downloads = driver.find_element(By.XPATH, "//div[text() = 'Downloads']/preceding-sibling::div").text
        except NoSuchElementException:
            downloads = ""

        try:
            usk = driver.find_element(By.XPATH, "//span[contains(@itemprop,'contentRating')]/span").text
        except NoSuchElementException:
            usk = ""
        try:
            updated = driver.find_element(By.XPATH, "//div[contains(., 'Updated on')]/following-sibling::div").text
        except NoSuchElementException:
            updated = ""

        driver.find_element(By.XPATH, "//i[text() = 'expand_more']").click()
        time.sleep(1)

        try:
            website = driver.find_element(By.XPATH, "//div[text()='Website']/following-sibling::div").text
        except NoSuchElementException:
            website = ""

        try:
            email = driver.find_element(By.XPATH, "//div[text()='Email']/following-sibling::div").text
        except NoSuchElementException:
            try:
                email = driver.find_element(By.XPATH, "//div[text()='Support email']/following-sibling::div").text
            except NoSuchElementException:
                email = ""

        try:
            privacy_policy_page = driver.find_element(By.XPATH, "//a[contains(@aria-label,'Privacy Policy')]").get_attribute("href")
        except NoSuchElementException:
            privacy_policy_page = ""

        try:
            similar_apps = driver.find_elements(By.XPATH,
                                                "//span[text() = 'Similar apps']/../../../../following-sibling::div/div/div/a")
            similar_apps = "|".join([x.get_attribute("href") for x in similar_apps])
        except NoSuchElementException:
            similar_apps = ""

        out = [driver.current_url, app_name, categories, tags, similar_apps, dev, website, email, price, description,
               review_count, review_average, review_stars[0], review_stars[1], review_stars[2], review_stars[3],
               review_stars[4], updated, downloads, usk, privacy_policy_page]
        return out

    columns = ["app_link", "app_name", "category", "tags", "similar_apps", "developer_name", "developer_website", "developer_email", "price", "description", "review_count", "review_average", "review_one", "review_two", "review_three", "review_four", "review_five", "updated", "n_installations", "content_rating", "privacy_policy_link"]
    all_apps = []

    # Test mode potentially here
    how_far_to_scrape = len(google_apps) if not test else 3

    for i, link in tqdm(enumerate(google_apps[:how_far_to_scrape]), total=how_far_to_scrape):
        fail_counter = 0
        while True:
            if fail_counter > 10:
                print("Too many tries in google app: " + str(link))
                break
            try:
                driver.get(link)
                if "We're sorry, the requested URL was not found on this server." in driver.page_source:
                    break
                id = link.split("?")[1]

                wait_for_ajax(driver)
                with open(source_path + id + ".html", "w", encoding="utf-8") as f:
                    f.write(driver.page_source)

                time.sleep(random.randint(5, 10))
                all_apps.append(get_values(driver))

                driver.get(link.replace("details", "datasafety"))
                wait_for_ajax(driver)
                if "We're sorry, the requested URL was not found on this server." not in driver.page_source:
                    with open(privacy_path + id + ".html", "w", encoding="utf-8") as f:
                        f.write(driver.page_source)
                break
            except Exception as e:
                fail_counter += 1
                print(e)
                time.sleep(60)
                pass

    all_apps = pd.DataFrame(all_apps, columns=columns)
    all_apps.to_csv(out_path + "Google.csv", index=False)
    driver.close()
    logging.info(f"Google scraper finished successfully")
    return 77


def start_google_until_success():
    send_email(["workstationemailsender@gmail.com"], "Google Scrape Started!", "Google Scrape Started!")
    tries = 0
    while True:
        tries += 1
        try:
            logging.info("Google Scrape Started")
            result = Google(["MEDICAL", "HEALTH_AND_FITNESS"], test = False)
            if result == 77:
                logging.info(f"Google function completed successfully! With {tries} tries.")
                send_email(["workstationemailsender@gmail.com"], "\n\n".join(log_list) + f"\n\nGoogle function completed successfully! With {tries} tries.",
                           f"Google scrape finished")
                exit(0)
        except Exception as e:
            logging.critical(f"Google function crashed with error: {e}. Restarting...")

def hourlyEmail():
    while True:
        time.sleep(3600)
        send_email(["workstationemailsender@gmail.com"], "\n\n".join(log_list), f"Google Hourly Update {len(log_list)} messages")
        log_list.clear()

email_thread = threading.Thread(target=hourlyEmail)
email_thread.daemon = True
email_thread.start()

start_google_until_success()