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
from Google_Ranker import get_google_ranking_health
from Utils import wait_for_ajax
import unicodedata
from Utils import get_all_apps_of_category_google
from DiGA import DiGA
from logger import get_logger, setup_logging
from schema.Categories import medicalOnly, allCategories

setup_logging()
log = get_logger(__name__)


def Google(
    test=False, initial_date=str(datetime.datetime.now().date()), categories=None
):
    os.makedirs("./data/Google_Health/", exist_ok=True)
    out_path = "./data/Google_Health/" + initial_date + "/"
    privacy_path = out_path + "/privacy/"
    source_path = out_path + "/source/"
    os.makedirs(out_path, exist_ok=True)
    os.makedirs(privacy_path, exist_ok=True)
    os.makedirs(source_path, exist_ok=True)
    base_url = "https://play.google.com"

    driver = webdriver.Firefox() # type: ignore


    log.info(f"starting google ranking")
    try:
        rank_info, all_rank_links = get_google_ranking_health(
            initial_date, driver=driver, out_path=out_path
        )
    except Exception as e:
        log.error(f"google ranking failed {e}")
        driver.close()
        return

    log.info("google ranking finished.")
    log.info("starting to load links")

    try:
        links = pd.read_csv("./data/DiGA/" + str(initial_date) + "/DiGA_links.csv")
    except FileNotFoundError:
        DiGA()
        links = pd.read_csv("./data/DiGA/" + str(initial_date) + "/DiGA_links.csv")
    diga_links = [x for x in list(links["google_link"]) if x is not np.nan]

    log.info("all links loaded")

    log.info("getting all apps of category google")
    try:
        all_google_scrape = get_all_apps_of_category_google(categories=categories)
        long_term = pd.read_csv(
            "./data/Google_Health/google_apps_health(17.09.2024).csv"
        )
        google_apps = list(
            set(
                all_rank_links
                + all_google_scrape
                + diga_links
                + list(long_term["links"])
            )
        )
        pd.DataFrame(google_apps, columns=["links"]).to_csv(
            "./data/Google_Health/google_apps.csv", index=False
        )
        if np.nan in google_apps:
            google_apps.remove(np.nan)
        google_apps = [base_url + x if base_url not in x else x for x in google_apps]
        google_apps = [
            x for x in google_apps if x != "https://play.google.com/store/games"
        ]
        log.info(
            f"loaded all apps of category google. all_rank_links: {len(all_rank_links)} all_scrape: {len(all_google_scrape)} diga links: {len(diga_links)} total: {len(google_apps)}"
        )
    except Exception as e:
        log.critical(f"google getting all apps of category google failed! {e}")
        driver.close()
        return

    def get_values(driver):
        try:
            app_name = driver.find_element(By.TAG_NAME, "h1").text
        except NoSuchElementException:
            return []
        try:
            dev = driver.find_element(
                By.XPATH, "//a[contains(@href, '/store/apps/developer?id=')]"
            ).text
        except NoSuchElementException:
            try:  # Fallback scheint hier nicht sprachenabhängig
                dev = driver.find_element(
                    By.XPATH, "//a[contains(@href, '/store/apps/dev?id=')]"
                ).text
            except NoSuchElementException:
                dev = ""

        try:
            tags = driver.find_elements(
                By.XPATH,
                "//a[contains(@href, '/store/apps/developer?id=')]/parent::div/following-sibling::div/div/span",
            )
            tags = "|".join([x.text for x in tags])
        except NoSuchElementException:
            try:  # hier auch
                tags = driver.find_elements(
                    By.XPATH,
                    "//a[contains(@href, '/store/apps/dev?id=')]/parent::div/following-sibling::div/div/span",
                )
                tags = "|".join([x.text for x in tags])
            except NoSuchElementException:
                tags = ""
        if not tags:
            tags = ""

        try:
            categories = driver.find_elements(
                By.XPATH,
                "//a[contains(@href, '/store/apps/category/')]/preceding-sibling::span",
            )
            categories = "|".join([x.text for x in categories])
        except NoSuchElementException:
            categories = ""

        try:
            price = driver.find_element(
                By.XPATH,
                "//button[contains(@aria-label, 'kaufen')]/preceding-sibling::span",
            ).text
        except NoSuchElementException:
            try:
                price = driver.find_element(
                    By.XPATH,
                    "//button[contains(@aria-label, 'Installieren')]/preceding-sibling::span",
                ).text
            except NoSuchElementException:
                try:
                    price = driver.find_element(
                        By.XPATH,
                        "//button[contains(@aria-label, 'Buy')]/preceding-sibling::span",
                    ).text
                except NoSuchElementException:
                    try:
                        price = driver.find_element(
                            By.XPATH,
                            "//button[contains(@aria-label, 'Install')]/preceding-sibling::span",
                        ).text
                    except NoSuchElementException:
                        price = ""
        try:
            description = driver.find_element(
                By.XPATH,
                "//meta[contains(@itemprop,'description')]/following-sibling::div[1]",
            ).text
        except NoSuchElementException:
            description = ""

        # TODO: Nimmt aktuell nur Bewertungen vom Handy
        try:
            review_count = driver.find_element(
                By.XPATH,
                "//h2[text() = 'Ratings and reviews']/../../../following-sibling::div/div/div/div/div/div/div[3]",
            ).text
        except NoSuchElementException:
            try:
                review_count = driver.find_element(
                    By.XPATH,
                    "//h2[text() = 'Bewertungen und Rezensionen']/../../../following-sibling::div/div/div/div/div/div/div[3]",
                ).text
            except NoSuchElementException:
                review_count = ""

        try:
            review_average = driver.find_element(
                By.XPATH,
                "//h2[text() = 'Ratings and reviews']/../../../following-sibling::div/div/div/div/div/div/div[1]",
            ).text
        except NoSuchElementException:
            try:
                review_average = driver.find_element(
                    By.XPATH,
                    "//h2[text() = 'Bewertungen und Rezensionen']/../../../following-sibling::div/div/div/div/div/div/div[1]",
                ).text
            except NoSuchElementException:
                review_average = ""

        review_stars = driver.find_elements(
            By.XPATH,
            "//h2[text() = 'Ratings and reviews']/../../../following-sibling::div/div/div/div/div/div[2]/div",
        )
        if not review_stars:
            review_stars = driver.find_elements(
                By.XPATH,
                "//h2[text() = 'Bewertungen und Rezensionen']/../../../following-sibling::div/div/div/div/div/div[2]/div",
            )
        if not review_stars:
            review_stars = [""] * 5
        if review_stars[0] != "":
            review_stars = [x.get_attribute("aria-label") for x in review_stars][::-1]  # type: ignore[union-attr]
            review_stars = [unicodedata.normalize("NFKD", x) for x in review_stars]
        try:
            downloads = driver.find_element(
                By.XPATH, "//div[text() = 'Downloads']/preceding-sibling::div"
            ).text
        except NoSuchElementException:
            downloads = ""

        try:
            usk = driver.find_element(
                By.XPATH, "//span[contains(@itemprop,'contentRating')]/span"
            ).text
        except NoSuchElementException:
            usk = ""
        try:
            updated = driver.find_element(
                By.XPATH, "//div[contains(., 'Updated on')]/following-sibling::div"
            ).text
        except NoSuchElementException:
            try:
                updated = driver.find_element(
                    By.XPATH,
                    "//div[contains(text, 'Aktualisiert am')]/following-sibling::div",
                ).text
            except NoSuchElementException:
                updated = ""

        driver.find_element(By.XPATH, "//i[text() = 'expand_more']").click()
        time.sleep(1)

        try:
            website = driver.find_element(
                By.XPATH, "//div[text()='Website']/following-sibling::div"
            ).text
        except NoSuchElementException:
            website = ""

        try:
            email = driver.find_element(
                By.XPATH, "//div[text()='Email']/following-sibling::div"
            ).text
        except NoSuchElementException:
            try:
                email = driver.find_element(
                    By.XPATH, "//div[text()='E-Mail']/following-sibling::div"
                ).text
            except NoSuchElementException:
                try:
                    email = driver.find_element(
                        By.XPATH, "//div[text()='Support email']/following-sibling::div"
                    ).text
                except NoSuchElementException:
                    try:
                        email = driver.find_element(
                            By.XPATH,
                            "//div[text()='Support-E-Mail-Adresse']/following-sibling::div",
                        ).text
                    except NoSuchElementException:
                        email = ""
        try:
            privacy_policy_page = driver.find_element(
                By.XPATH, "//a[contains(@aria-label,'Datenschutzerklärung')]"
            ).get_attribute("href")
        except NoSuchElementException:
            try:
                privacy_policy_page = driver.find_element(
                    By.XPATH, "//a[contains(@aria-label,'Privacy Policy')]"
                ).get_attribute("href")
            except NoSuchElementException:
                privacy_policy_page = ""

        try:
            similar_apps = driver.find_elements(
                By.XPATH,
                "//span[text() = 'Similar apps']/../../../../following-sibling::div/div/div/a",
            )
            similar_apps = "|".join([x.get_attribute("href") for x in similar_apps])
        except NoSuchElementException:
            try:
                similar_apps = driver.find_elements(
                    By.XPATH,
                    "//span[text() = 'Ähnliche Apps']/../../../../following-sibling::div/div/div/a",
                )
                similar_apps = "|".join([x.get_attribute("href") for x in similar_apps])
            except NoSuchElementException:
                similar_apps = ""

        out = [
            driver.current_url,
            app_name,
            categories,
            tags,
            similar_apps,
            dev,
            website,
            email,
            price,
            description,
            review_count,
            review_average,
            review_stars[0],
            review_stars[1],
            review_stars[2],
            review_stars[3],
            review_stars[4],
            updated,
            downloads,
            usk,
            privacy_policy_page,
        ]
        return out

    columns = [
        "app_link",
        "app_name",
        "category",
        "tags",
        "similar_apps",
        "developer_name",
        "developer_website",
        "developer_email",
        "price",
        "description",
        "review_count",
        "review_average",
        "review_one",
        "review_two",
        "review_three",
        "review_four",
        "review_five",
        "updated",
        "n_installations",
        "content_rating",
        "privacy_policy_link",
    ]
    all_apps = []

    # Test mode potentially here
    how_far_to_scrape = len(google_apps) if not test else 3

    log.info("Last phase started, starting to scrape")
    for i, link in tqdm(
        enumerate(google_apps[:how_far_to_scrape]), total=how_far_to_scrape
    ):
        fail_counter = 0
        while True:
            if fail_counter > 10:
                log.warning("Too many tries in google app. Skipping: " + str(link))
                break
            try:
                driver.get(link)
                if (
                    "We're sorry, the requested URL was not found on this server."
                    in driver.page_source
                ):
                    break
                if (
                    "Die angeforderte URL wurde auf diesem Server nicht gefunden."
                    in driver.page_source
                ):
                    break
                id = link.split("?")[1]

                wait_for_ajax(driver)
                with open(source_path + id + ".html", "w", encoding="utf-8") as f:
                    f.write(driver.page_source)

                time.sleep(random.randint(5, 10))
                all_apps.append(get_values(driver))

                driver.get(link.replace("details", "datasafety"))
                wait_for_ajax(driver)
                if (
                    "We're sorry, the requested URL was not found on this server."
                    not in driver.page_source
                ):
                    with open(privacy_path + id + ".html", "w", encoding="utf-8") as f:
                        f.write(driver.page_source)
                break
            except Exception as e:
                fail_counter += 1
                log.error(f"failed to scrape {link}: {e}")
                time.sleep(60)
                pass

    all_apps = pd.DataFrame(all_apps, columns=columns)
    all_apps.to_csv(out_path + "Google.csv", index=False)
    driver.close()
    log.info("scrape finished")
    return 77


def start_google_until_success():
    tries = 0
    while True:
        tries += 1
        try:
            log.info("Google Health Scrape Started")
            result = Google(test=False, categories=medicalOnly)
            if result == 77:
                log.info(f"Google function completed successfully! With {tries} tries.")
                break
        except Exception as e:
            log.critical(f"Google function crashed with error: {e}. Restarting...")


start_google_until_success()
