import os
import datetime
from time import sleep
import numpy as np
from unidecode import unidecode
import requests
import re
import time
import random
import traceback
import pandas as pd
from tqdm import tqdm
from bs4 import BeautifulSoup
from Get_All_Apple import get_links
from Apple_Ranker import get_rank_apple
import pickle
import json
import logging
import threading
from EmailSender import send_email
import BadLinkManager
from urllib.parse import urlparse

#region loggingsystem
class ListHandler(logging.Handler):
    def __init__(self, log_list):
        super().__init__()
        self.log_list = log_list

    def emit(self, record):
        log_entry = self.format(record)
        self.log_list.append(log_entry)

log_list = []

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%d/%m/%Y %H:%M:%S')

logger = logging.getLogger()

list_handler = ListHandler(log_list)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s',
                              datefmt='%d/%m/%Y %H:%M:%S')
list_handler.setFormatter(formatter)
logger.addHandler(list_handler)  #
#endregiont

def apple(folder_name: str, use_link_list: bool, test: bool, specify_categories: list[str], all_categories: bool, country:str):
    all_categories_list = ["books", "business", "catalogs", "developer_tools", "education", "entertainment",
                      "finance", "food_drink", "games", "graphics_design", "health", "lifestyle",
                      "magazines", "medical", "music", "navigation", "news", "photo", "productivity",
                      "reference", "shopping", "social", "sports", "stickers", "travel", "utilities", "weather"]

    logging.info("Creating directories")

    save_path = "AppleScrape/Junkdata/" + folder_name + "/"
    file_name = "JunkLinks.csv"
    full_path_junkdata = os.path.join(save_path, file_name)
    BadLinkManager.prepareDirectories(save_path=save_path, file_name=file_name)

    os.makedirs("./data/Apple/", exist_ok=True)
    out_path = "./data/Apple/" + folder_name
    source_path = out_path + "/source/"
    os.makedirs(out_path, exist_ok=True)
    os.makedirs(source_path, exist_ok=True)
    logging.info("Directories created")
    logging.info("Loading links")

    apple_apps = []
    if all_categories:
        specify_categories = all_categories_list

    if use_link_list:
        target_categories = ["Health & Fitness", "Medical"]
        logging.info(f"Loading links of categories {target_categories}")
        df = pd.read_csv("./filtered_links.csv")
        df2 = pd.read_csv("./filtered_links2.csv")
        combined_df = pd.concat([df, df2], ignore_index=True)
        filtered_df = combined_df[combined_df['category'].isin(target_categories)]
        apple_apps = filtered_df['link'].tolist()
    else:
        for category in specify_categories:
            logging.info("Loading " + category)
            tries = 0
            while True:
                if tries > 3:
                    break
                try:
                    if os.path.exists(out_path + "/" + category + ".pkl"):
                        with open(out_path + "/" + category + ".pkl", "rb") as f:
                            temp_links = pickle.load(f)
                    else:
                        temp_links = get_links(category)
                        with open(out_path + "/" + category + ".pkl", "wb") as f:
                            pickle.dump(temp_links, f)
                    apple_apps += temp_links
                    break
                except Exception as e:
                    logging.error(f"Failed to load category: {category} {e}\nretrying")
                    tries += 1

    logging.info(f"{len(apple_apps)} app links loaded.")
    logging.info("Loading rank information")

    if os.path.exists(out_path + "/Apple_Rank.csv"):
        logging.info("Rank information already stored.")
    else:
        tries = 0
        while True:
            if tries >= 5:
                logging.critical("Failed to load rank information. Apple Scrape stopped")
                return
            try:
                get_rank_apple(folder_name=folder_name, language=country, all_categories=all_categories)
                logging.info("Rank information stored")
                break
            except Exception as e:
                logging.error(f"Failed to load rank information: {e}\nretrying")
                tries += 1
                sleep(60)

    if np.nan in apple_apps:
        apple_apps.remove(np.nan)
    apple_apps = [x.split("?")[0] if "?" in x else x for x in apple_apps]
    apple_apps = list(set(apple_apps))

    if country != "us":
        apple_apps = [app.replace("us", country) for app in apple_apps]
        apple_apps = [app.replace("de", country) for app in apple_apps]

    def get_attributes(soup, link):
        def size_to_bytes(txt: str) -> int:
            s = txt.replace("\xa0", " ").replace(",", ".").strip()
            # join split unit tokens, e.g., "M B" -> "MB"
            s = s.replace(" K B", " KB").replace(" M B", " MB").replace(" G B", " GB")
            s = s.replace("KB", " KB").replace("MB", " MB").replace("GB", " GB")

            parts = s.split()
            if not parts:
                return 0
            num = parts[0]
            unit = parts[1].upper() if len(parts) > 1 else "B"

            v = float(num)
            mult = {"B": 1, "KB": 1_000, "MB": 1_000_000, "GB": 1_000_000_000}
            return int(v * mult.get(unit, 1))
        try:
            app_name = json.loads(soup.find("script", id="software-application", type="application/ld+json").string)["name"]
        except AttributeError:
            return None
        developer = json.loads(soup.find("script", id="software-application", type="application/ld+json").string)["author"]["name"]
        category = json.loads(soup.find("script", id="software-application", type="application/ld+json").string)[
            "applicationCategory"]
        price = f"{json.loads(soup.find('script', id='software-application', type='application/ld+json').string)['offers']['price']} {json.loads(soup.find('script', id='software-application', type='application/ld+json').string)['offers']['priceCurrency']}"
        description = json.loads(soup.find("script", id="software-application", type="application/ld+json").string)[
            "description"]
        review_average = json.loads(soup.find("script", id="software-application", type="application/ld+json").string)[
            "aggregateRating"]["ratingValue"]
        review_count = json.loads(soup.find("script", id="software-application", type="application/ld+json").string)[
            "aggregateRating"]["reviewCount"]

        try:
            rating_bars = soup.select('div[data-testid^="star-row-"]')
            ratings = []
            if rating_bars:
                for el in rating_bars:
                    percentage = float(el["style"].split(" ")[1].replace("%", ""))
                    ratings.append(round(percentage / 100 * review_count, 0))
            else:
                review_count = 0
                review_average = "None"
                ratings = [0] * 5
        except AttributeError:
            review_count = 0
            review_average = "None"
            ratings = [0] * 5

        try:
            languages = soup.find("dt", string=lambda s: s and s.strip().lower() == "languages").find_next(
                "details").select_one("ul li .styled-text").get_text(strip=True)
        except AttributeError:
            try:
                languages = soup.find("dt", string=lambda s: s and s.strip().lower() == "sprachen").find_next(
                    "details").select_one("ul li .styled-text").get_text(strip=True)
            except AttributeError:
                languages = "None"

        try:
            size = size_to_bytes(
                soup.find("dt", string=lambda s: s and s.strip().lower() == "size").find_next("ul").select_one(
                    "li .styled-text").get_text(strip=True))
        except AttributeError:
            try:
                size = size_to_bytes(
                    soup.find("dt", string=lambda s: s and s.strip().lower() == "größe").find_next("ul").select_one(
                        "li .styled-text").get_text(strip=True))
            except AttributeError:
                size = "None"

        try:
            versions = soup.find("dt", string=lambda s: s and s.strip().lower() in (
            "kompatibilität", "compatibility")).find_next("details").select("ul li .styled-text")
            versions = [block.get_text("\n", strip=True) for block in versions]
            versions = "|".join(versions)
        except AttributeError:
            versions = "None"

        try:
            in_app_purchases = soup.find("dt", string=lambda s: s and s.strip().lower() in (
            "in‑app purchases", "in-app-käufe")).find_next("details").select("ul li")
            in_app_purchases = [block.get_text("\n", strip=True) for block in in_app_purchases]
            in_app_purchases = "|".join(in_app_purchases)
        except AttributeError:
            in_app_purchases = "None"

        try:
            age_restriction = soup.find("dt", string=lambda s: s and s.strip().lower() in (
            "age rating", "altersfreigabe")).find_next(lambda n: n.name in ("div", "span") and n.get_text(
                strip=True) and "Altersfreigabe" not in n.get_text() and "Age Rating" not in n.get_text()).get_text(
                strip=True)
        except AttributeError:
            age_restriction = "None"

        try:
            age_restriction_reasons = soup.find("dt", string=lambda s: s and s.strip().lower() in (
            "age rating", "altersfreigabe")).find_next("details")
            age_restriction_reasons = [li.get_text(" ", strip=True) for li in age_restriction_reasons.select("ul li")]
        except AttributeError:
            age_restriction_reasons = "None"

        try:
            similar_apps = [a["href"] for a in soup.find("h2", string=lambda s: s and s.strip().lower() in (
            "you might also like", "das gefällt dir vielleicht auch")).find_next("ul").select("li a[aria-label][href]")]
        except AttributeError:
            similar_apps = []

        # Privacy
        if "/us/" in link:
            privacy_strings = {"linked": "Data Linked to You",
                               "unlinked": "Data Not Linked to You",
                               "not_collected": "Data Not Collected",
                               "tracked": "Data Used to Track You"}
        else:
            privacy_strings = {"linked": "Mit dir verknüpfte Daten",
                               "unlinked": "Nicht mit dir verknüpfte Daten",
                               "not_collected": "Keine Daten erfasst",
                               "tracked": "Daten, die zum Tracking deiner Person verwendet werden"}

        try:
            unlinked_h2 = soup.find_all("h2", string=privacy_strings["unlinked"])[1].find_next("ul")
            unlinked = [li.get_text(" ", strip=True) for li in unlinked_h2.select("li")] if unlinked_h2 else []
        except (AttributeError, IndexError):
            unlinked = []

        try:
            linked_h2 = soup.find_all("h2", string=privacy_strings["linked"])[1].find_next("ul")
            linked = [li.get_text(" ", strip=True) for li in linked_h2.select("li")] if linked_h2 else []
        except (AttributeError, IndexError):
            linked = []

        try:
            tracked_h2 = soup.find_all("h2", string=privacy_strings["tracked"])[1].find_next("ul")
            tracked = [li.get_text(" ", strip=True) for li in tracked_h2.select("li")] if tracked_h2 else []
        except (AttributeError, IndexError):
            tracked = []

        not_collected = soup.find("h2", string=privacy_strings["not_collected"])
        if not_collected:
            not_collected = "True"

        try:
            privacy_policy_link = \
            soup.find("a", string=lambda s: s and ("datenschutz" in s.lower() or "privacy policy" in s.lower()))["href"]
        except (AttributeError, TypeError):
            privacy_policy_link = "None"

        # version history
        lis = soup.select('dialog ul li')
        VERSION_RE = re.compile(r"\b(?:Version\s*)?(\d+\.\d+(?:\.\d+)?)\b")
        version_history = []
        for li in lis:
            heading = li.find(["h3", "h4", "h5"])
            time = li.find("time")
            notes = li.find("p")
            m = VERSION_RE.search((heading.get_text(" ", strip=True) if heading else ""))
            if m and time:
                version_history.append({
                    "version": m.group(1),
                    "date": time.get("datetime") or time.get_text(strip=True),
                    "notes": notes.get_text(" ", strip=True) if notes else None
                })

        out = [link, app_name, developer, category, price, description, similar_apps, review_count, review_average,
               ratings[4], ratings[3], ratings[2], ratings[1], ratings[0], versions, size, languages, age_restriction,
               age_restriction_reasons, linked, unlinked, tracked, not_collected, str(version_history),
               in_app_purchases, privacy_policy_link]

        # Cleaning
        for index, element in enumerate(out):
            out[index] = unidecode(str(element)).strip()
        return out

    all_apps = []

    # Test mode potentially here
    how_far_to_scrape = len(apple_apps) if not test else 50
    logging.info(f"Starting to scrape {how_far_to_scrape} apps")
    for i, link in tqdm(enumerate(apple_apps[:how_far_to_scrape]), total=how_far_to_scrape):
        if not is_valid_url(link):
            logging.error(f"Invalid URL: {link}")
            continue

        if i % 100 == 0 :
            logging.info(f"Current progress: {i}/{how_far_to_scrape}")

        not_loaded_fail_counter, reset_fail_counter = 0, 0
        if i % 10000 == 0:
            with open(out_path + "/all_scraped" + str(i) + ".pkl", "wb") as f:
                pickle.dump(all_apps, f)
            if os.path.exists(out_path + "/all_scraped" + str(i - 10000) + ".pkl"):
                os.remove(out_path + "/all_scraped" + str(i - 10000) + ".pkl")

        while True:
            if reset_fail_counter >= 3:
                logging.warning("Too many retries. Skip link. " + link)
                break
            if not_loaded_fail_counter >= 3:
                logging.warning("Does not load. Skipping: " + link + " and adding to junk data.")
                BadLinkManager.addJunkLinks(full_path=full_path_junkdata, links=[link])
                break
            try:
                r = requests.get(link)
                if r.status_code == 429:
                    reset_fail_counter += 1
                    logging.warning("Reset Limit. Waiting 5 Minutes.")
                    time.sleep(300)
                    continue
                time.sleep(random.randint(5, 10))
                soup = BeautifulSoup(r.content, "html.parser")
                attributes = get_attributes(soup, link)
                if not attributes:
                    not_loaded_fail_counter += 1
                    logging.warning("Name not found. Retry in 5 seconds: " + link)
                    time.sleep(5)
                    continue
                all_apps.append(attributes)
                break
            except OSError:
                reset_fail_counter += 1
                time.sleep((3600 * 12))
                pass
            except Exception as e:
                logging.warning(e)
                reset_fail_counter += 1
                logging.warning(link)
                logging.warning(traceback.format_exc())
                time.sleep(random.randint(5, 10))
                pass

    columns = ["link", "app_name", "developer_name", "category", "price", "description", "similar_apps", "review_count",
               "review_average", "review_one", "review_two", "review_three", "review_four", "review_five",
               "versions", "size", "languages", "age", "age_reasons",
               "privacy_linked", "privacy_unlinked", "privacy_tracked", "privacy_not_collected", "version_history", "in_app_purchases", "privacy_policy_link"]

    all_apps = pd.DataFrame(all_apps, columns=columns)
    all_apps.to_csv(out_path + "/Apple.csv", index=False)
    logging.info(f"Apple Scrape Finished scraping successfully")
    return 77

def is_valid_url(url):
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)

def start_apple_until_success():
    initial_date = datetime.date.today()
    send_email(["workstationemailsender@gmail.com"], "Apple Scrape Started!", "Apple Scrape Started!")
    tries = 0
    while True:
        tries += 1
        try:
            logging.info("Apple Scrape Started")
            result = apple(folder_name=str(initial_date), use_link_list=True, test=False, specify_categories=["Health & Fitness", "Medical"], all_categories=True, country="us")
            if result == 77:
                logging.info(f"Apple function completed successfully! With {tries} tries.")
                send_email(["workstationemailsender@gmail.com"], "\n\n".join(log_list) + f"\n\nApple Scrape completed successfully! With {tries} tries.",
                           f"Apple scrape finished")
                exit(0)
        except Exception as e:
            logging.critical(f"Apple function crashed with error: {e}. Restarting...")
            send_email(["workstationemailsender@gmail.com"],
                       "\n\n".join(log_list) + f"\n\nApple Scrape crashed! try #{tries}.",
                       f"Apple scrape crashed")


def hourlyEmail():
    while True:
        time.sleep(3600)
        send_email(["workstationemailsender@gmail.com"], "\n\n".join(log_list),
                   f"Apple Hourly Update {len(log_list)} messages")
        log_list.clear()


email_thread = threading.Thread(target=hourlyEmail)
email_thread.daemon = True
email_thread.start()

start_apple_until_success()