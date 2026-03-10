import requests
from bs4 import BeautifulSoup
import string
import time
import logging

from numpy.f2py.auxfuncs import throw_error


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

category_dict = {
    "books": "https://apps.apple.com/us/genre/ios-books/id6018",
    "business": "https://apps.apple.com/us/genre/ios-business/id6000",
    "catalogs": "https://apps.apple.com/us/genre/ios-catalogs/id6022",
    "developer_tools": "https://apps.apple.com/us/genre/ios-developer-tools/id6026",
    "education": "https://apps.apple.com/us/genre/ios-education/id6017",
    "entertainment": "https://apps.apple.com/us/genre/ios-entertainment/id6016",
    "finance": "https://apps.apple.com/us/genre/ios-finance/id6015",
    "food_drink": "https://apps.apple.com/us/genre/ios-food-drink/id6023",
    "games": "https://apps.apple.com/us/genre/ios-games/id6014",
    "graphics_design": "https://apps.apple.com/us/genre/ios-graphics-design/id6027",
    "health": "https://apps.apple.com/us/genre/ios-health-fitness/id6013",
    "lifestyle": "https://apps.apple.com/us/genre/ios-lifestyle/id6012",
    "magazines": "https://apps.apple.com/us/genre/ios-magazines-newspapers/id6021",
    "medical": "https://apps.apple.com/us/genre/ios-medical/id6020",
    "music": "https://apps.apple.com/us/genre/ios-music/id6011",
    "navigation": "https://apps.apple.com/us/genre/ios-navigation/id6010",
    "news": "https://apps.apple.com/us/genre/ios-news/id6009",
    "photo": "https://apps.apple.com/us/genre/ios-photo-video/id6008",
    "productivity": "https://apps.apple.com/us/genre/ios-productivity/id6007",
    "reference": "https://apps.apple.com/us/genre/ios-reference/id6006",
    "shopping": "https://apps.apple.com/us/genre/ios-shopping/id6024",
    "social": "https://apps.apple.com/us/genre/ios-social-networking/id6005",
    "sports": "https://apps.apple.com/us/genre/ios-sports/id6004",
    "stickers": "https://apps.apple.com/us/genre/ios-stickers/id6025",
    "travel": "https://apps.apple.com/us/genre/ios-travel/id6003",
    "utilities": "https://apps.apple.com/us/genre/ios-utilities/id6002",
    "weather": "https://apps.apple.com/us/genre/ios-weather/id6001"
}


def get_links(category):

    uppercase = string.ascii_uppercase
    # There is a special character category, that is described by the '#'
    uppercase += "#"

    try:
        initial_link = category_dict[category]
    except KeyError:
        logging.warning(f"This category does not exit: {category}")
        raise

    all_links = []

    for letter in uppercase:
        i = 1
        while True:
            query = {"letter": letter, "page": i}
            r = requests.get(initial_link, params=query)
            if r.status_code != 200:
                logging.warning("Non-200 status code: " + str(r.status_code) + ". Waiting 5 minutes and retry.")
                time.sleep(300)
                continue

            soup = BeautifulSoup(r.content, "html.parser")
            selected_content = soup.find(id="selectedcontent")

            if selected_content is None:
                logging.error(f"Element with id 'selectedcontent' not found for letter {letter}, page {i}.")
                break

            links = selected_content.find_all("a")

            # If no new links or no links, stop fetching more pages
            if not links or any(link in all_links for link in links):
                all_links += links
                break

            all_links += links
            i += 1

    all_links = [link["href"] for link in all_links]
    all_links = list(set(all_links))
    logging.info(category + ": " + str(len(all_links)))
    return all_links


if __name__ == "__main__":
    get_links("health")
