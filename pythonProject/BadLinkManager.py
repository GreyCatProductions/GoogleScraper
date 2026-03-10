import pandas as pd
import os
import logging

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

def prepareDirectories(save_path, file_name):
    if save_path is None or file_name is None:
        logging.critical("must provide save_path and file_name")
        return
    full_path = os.path.join(save_path, file_name)
    if os.path.exists(full_path):
        return

    os.makedirs(save_path, exist_ok=True)
    df = pd.DataFrame(columns=['link'])
    df.to_csv(full_path, index=False)


# Add junk links to the file
def addJunkLinks(full_path, links):
    if full_path is None or not os.path.exists(full_path):
        print("must provide valid full_path")
        return

    if links is None or len(links) == 0:
        logging.warning("No links provided to add.")
        return

    links = set(links)
    df_new = pd.DataFrame(links, columns=['link'])
    df_new.to_csv(full_path, mode='a', header=False, index=False)
    logging.info(f"{len(links)} junk link(s) saved.")


def removeJunkLinks(filePathToRemoveFrom, columnNameToRemoveFrom, filePathOfLinksToRemove):
    if filePathToRemoveFrom is None or columnNameToRemoveFrom is None or filePathOfLinksToRemove is None:
        logging.error("File path, column name, and file path of linksToRemove (the full path) must be provided.")
        return

    if not os.path.exists(filePathToRemoveFrom):
        logging.error(f"File {filePathToRemoveFrom} does not exist.")
        return

    if not os.path.exists(filePathOfLinksToRemove):
        logging.error(f"File {filePathOfLinksToRemove} does not exist.")
        return

    try:
        df = pd.read_csv(filePathToRemoveFrom)
        to_remove_df = pd.read_csv(filePathOfLinksToRemove)

        if columnNameToRemoveFrom not in df.columns:
            logging.error(f"Column {columnNameToRemoveFrom} does not exist in the file.")
            return

        if 'link' not in to_remove_df.columns:
            logging.error("The file containing links to remove must have a 'link' column.")
            return

        to_remove_links = to_remove_df['link'].tolist()
        initial_count = len(df)
        df = df[~df[columnNameToRemoveFrom].isin(to_remove_links)]
        removed_count = initial_count - len(df)

        df.to_csv(filePathToRemoveFrom, index=False)

        logging.info(f"{removed_count} junk link(s) removed from {filePathToRemoveFrom}.")
    except Exception as e:
        logging.error(f"An error occurred while removing links: {e}")





