import os
import pandas
import pandas as pd

def analyze_links(path_to_junk_data_folder: os.path, min_occurrences):
    if not os.path.exists(path_to_junk_data_folder):
        print('Path does not exist!')
        return

    junk_data_frames: list[(pandas.DataFrame, os.path)] = load_data_frames(path_to_junk_data_folder)

    print_lengths(junk_data_frames)

    bad_links: list[str] = find_urls_with_min_occurrence(junk_data_frames, min_occurrences)
    print(f"len of urls that occurred at least {min_occurrences}x: {len(bad_links)}")
    return bad_links

def load_data_frames(path_to_junk_data_folder: os.path) -> list[(pandas.DataFrame, os.path)]:
    junk_data_frames: list[(pandas.DataFrame, os.path)] = []

    for datafolder in os.listdir(path_to_junk_data_folder):
        datafolder_path = os.path.join(path_to_junk_data_folder, datafolder)
        if os.path.isdir(datafolder_path):
            junk_list_csv = os.listdir(datafolder_path).pop(0)
            junk_list_csv_path = os.path.join(datafolder_path, junk_list_csv)
            df = pd.read_csv(junk_list_csv_path)
            junk_data_frames.append((df, junk_list_csv_path))

    return junk_data_frames

def print_lengths(data_frames: list[(pandas.DataFrame, os.path)]):
    for data_frame, path_to_df in data_frames:
        print(f"{path_to_df} +  {len(data_frame)}")

def find_urls_with_min_occurrence(data_frames: list[(pandas.DataFrame, os.path)], min_amount):
    url_counts = {}
    for data_frame, df_path in data_frames:
        for url in data_frame['link']:
            url_counts[url] = url_counts.get(url, 0) + 1

    filtered_bad_links = []
    for key, value in url_counts.items():
        if value >= min_amount:
            filtered_bad_links.append(key)

    return filtered_bad_links

if __name__ == '__main__':
    path = os.path.join(os.getcwd() + "/AppleScrape/Junkdata")
    analyze_links(path, 4)
