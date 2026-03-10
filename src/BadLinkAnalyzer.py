import pandas as pd
import os

def prepareDirectories(save_path, file_name):
    if save_path is None or file_name is None:
        print("must provide save_path and file_name")
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
        print("No links provided to add.")
        return

    links = set(links)
    df_new = pd.DataFrame(links, columns=['link'])
    df_new.to_csv(full_path, mode='a', header=False, index=False)
    print(f"{len(links)} junk link(s) saved.")


def removeJunkLinks(filePathToRemoveFrom, columnNameToRemoveFrom, filePathOfLinksToRemove):
    if filePathToRemoveFrom is None or columnNameToRemoveFrom is None or filePathOfLinksToRemove is None:
        print("File path, column name, and file path of linksToRemove (the full path) must be provided.")
        return

    if not os.path.exists(filePathToRemoveFrom):
        print(f"File {filePathToRemoveFrom} does not exist.")
        return

    if not os.path.exists(filePathOfLinksToRemove):
        print(f"File {filePathOfLinksToRemove} does not exist.")
        return

    try:
        df = pd.read_csv(filePathToRemoveFrom)
        to_remove_df = pd.read_csv(filePathOfLinksToRemove)

        if columnNameToRemoveFrom not in df.columns:
            print(f"Column {columnNameToRemoveFrom} does not exist in the file.")
            return

        if 'link' not in to_remove_df.columns:
            print("The file containing links to remove must have a 'link' column.")
            return

        to_remove_links = to_remove_df['link'].tolist()
        initial_count = len(df)
        df = df[~df[columnNameToRemoveFrom].isin(to_remove_links)]
        removed_count = initial_count - len(df)

        df.to_csv(filePathToRemoveFrom, index=False)

        print(f"{removed_count} junk link(s) removed from {filePathToRemoveFrom}.")
    except Exception as e:
        print(f"An error occurred while removing links: {e}")





