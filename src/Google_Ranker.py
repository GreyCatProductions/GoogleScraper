import os
import time
from time import sleep
from numpy.f2py.auxfuncs import throw_error
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from Utils import wait_for_ajax
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd

from logger import get_logger

log = get_logger(__name__)


def get_google_ranking_health(initial_date, driver, out_path):
    if not out_path:
        throw_error("no path provided")

    locations = ["DE", "AT", "CH", "US"]
    categories = [
        "https://play.google.com/store/apps/category/MEDICAL?hl=de&gl=",
        "https://play.google.com/store/apps/category/HEALTH_AND_FITNESS?hl=de&gl=",
    ]

    all_links = []
    rank_info = []

    if not os.path.exists(out_path + "/Google_rank_info.csv"):
        if not driver:
            driver = webdriver.Firefox() # type: ignore
        for category in categories:
            for location in locations:
                driver.get(category + location)
                xpath_list = [
                    '//*[@id="ct|apps_topselling_free"]/div[2]/span[2]',
                    '//*[@id="ct|apps_topgrossing"]/div[2]/span[2]',
                    '//*[@id="ct|apps_topselling_paid"]/div[2]/span[2]',
                ]
                for xpath in xpath_list:
                    sub_category = driver.find_element(By.XPATH, xpath)
                    sub_category.click()
                    time.sleep(2)
                    wait_for_ajax(driver)
                    links = [
                        x.get_attribute("href")
                        for x in WebDriverWait(driver, 20).until(
                            EC.visibility_of_all_elements_located(
                                (
                                    By.XPATH,
                                    "//a[contains(@href,'/store/apps/details?id')]",
                                )
                            )
                        )
                    ]
                    all_links += links
                    rank_info.append(
                        [
                            [location, category, sub_category.text, j + 1, link]
                            for j, link in enumerate(links)
                        ]
                    )

        rank_info = [item for sublist in rank_info for item in sublist]
        rank_info = pd.DataFrame(
            rank_info,
            columns=["country", "app_category", "rank_category", "rank", "url"],
        )
        rank_info.to_csv(out_path + "/Google_rank_info.csv", index=False, sep=";")

        return rank_info, all_links

    else:
        log.info("information already exists.")
        rank_info = pd.read_csv(out_path + "/Google_rank_info.csv", sep=";")
        return rank_info, list(rank_info["url"])


def get_google_ranking_all(
    country, driver, out_path, app_categories
):
    if not out_path:
        throw_error("no path provided")
    if not app_categories:
        throw_error("no categories provided")

    categories = [
        "https://play.google.com/store/apps/category/" + cat + "?hl=en&gl=" + country
        for cat in app_categories
    ]

    all_links = []
    rank_info = []

    if not os.path.exists(out_path + "/Google_rank_info_all.csv"):
        if not driver:
            driver = webdriver.Firefox() # type: ignore
        for category in categories:
            tries = 0
            log.info("current category: " + category)
            driver.get(category)
            xpath_list = [
                '//*[@id="ct|apps_topselling_free"]/div[2]/span[2]',
                '//*[@id="ct|apps_topgrossing"]/div[2]/span[2]',
                '//*[@id="ct|apps_topselling_paid"]/div[2]/span[2]',
            ]
            for xpath in xpath_list:
                tries = 0
                while True:
                    if tries >= 5:
                        break
                    try:
                        sub_category = driver.find_element(By.XPATH, xpath)
                        sub_category.click()
                        time.sleep(2)
                        wait_for_ajax(driver)
                        links = [
                            x.get_attribute("href")
                            for x in WebDriverWait(driver, 30).until(
                                EC.visibility_of_all_elements_located(
                                    (
                                        By.XPATH,
                                        "//a[contains(@href,'/store/apps/details?id')]",
                                    )
                                )
                            )
                        ]
                        all_links += links
                        rank_info.append(
                            [
                                [country, category, sub_category.text, j + 1, link]
                                for j, link in enumerate(links)
                            ]
                        )
                        break
                    except NoSuchElementException:
                        log.warning(
                            "No category found for: " + country + " " + category
                        )
                        break
                    except TimeoutException:
                        log.warning(
                            "No links found after 30s for: " + country + " " + category
                        )
                        break
                    except Exception as e:
                        log.warning(f"Category failed. refreshing {category} {e}")
                        driver.refresh()
                        sleep(10)
                        tries += 1

        rank_info = [item for sublist in rank_info for item in sublist]
        rank_info = pd.DataFrame(
            rank_info,
            columns=["country", "app_category", "rank_category", "rank", "url"],
        )
        rank_info.to_csv(out_path + "/Google_rank_info_all.csv", index=False, sep=";")

        return rank_info, all_links

    else:
        log.info("Information already exists")
        rank_info = pd.read_csv(out_path + "/Google_rank_info_all.csv", sep=";")
        return rank_info, list(rank_info["url"])
