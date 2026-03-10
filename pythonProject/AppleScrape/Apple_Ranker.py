import requests
from bs4 import BeautifulSoup
import pandas as pd
from Get_All_Apple import category_dict
import logging
import certifi


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
logger.addHandler(list_handler)
#endregion

def get_rank_apple(folder_name: str, language: str, all_categories: bool):
    base_link = "https://apps.apple.com/de/charts/"
    devices = ["ipad/", "iphone/"]
    categories = ["ios-medizin-apps/6020", "ios-gesundheit-und-fitness-apps/6013"]
    charts = ["?chart=top-free", "?chart=top-paid"]

    if all_categories:
        categories = []
        for key, value in category_dict.items():
            last_parts = value.split("/")[-2:]
            categories.append(last_parts[0] + "/" + last_parts[1].replace("id", ""))

    links = []
    for device in devices:
        for category in categories:
            for chart in charts:
                links.append(base_link + device + category + chart)

    languages = ["de", "at", "ch", "us"]
    if language != "us":
        languages = [language]
    all_ranks = []

    for language in languages:
        for link in links:
            try:
                r = requests.get(link.replace("de", language), verify=certifi.where())
                soup = BeautifulSoup(r.content, "html.parser")
                apps = soup.find_all("a")

                df = pd.DataFrame(columns=["Link", "Language", "Category_Paid", "Device", "Rank", "Category"])
                df["Link"] = [app["href"] for app in apps if "https://apps.apple.com/" + language + "/app" in app["href"]]
                df["Language"] = [language] * df.shape[0]
                df["Category_Paid"] = ["top-free" if "top-free" in link else "top-paid"] * df.shape[0]
                df["Device"] = ["iphone" if "iphone" in link else "ipad"] * df.shape[0]
                df["Rank"] = range(1, df.shape[0] + 1)
                df["Category"] = [link.split('ios-')[1].split('/')[0] if 'ios-' in link else "None"] * df.shape[0]
                all_ranks.append(df)
            except Exception as e:
                logging.error(f"failed to load link: {link}\nError message: {e}")

    ranks = pd.concat(all_ranks)
    out_path = "./data/Apple/" + folder_name
    ranks.to_csv(out_path + "/Apple_Rank.csv")
    return ranks