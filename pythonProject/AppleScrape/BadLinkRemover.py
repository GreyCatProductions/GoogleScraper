import csv
import os
from BadLinkListAnalyzer import analyze_links

def filter_links(csv_main, remove_links_list, csv_output):
    remove_links = set(remove_links_list)

    with open(csv_main, newline='', encoding='utf-8') as infile, \
            open(csv_output, 'w', newline='', encoding='utf-8') as outfile:

        reader = csv.reader(infile)
        writer = csv.writer(outfile)

        unfiltered_amount = 0
        filtered_amount = 0

        for row in reader:
            unfiltered_amount += 1
            if row and row[0] not in remove_links:
                filtered_amount += 1
                writer.writerow(row)

    print(f"Filtered links saved to: {csv_output}. Unfiltered length: {unfiltered_amount} filtered length: {filtered_amount} bad_links_filtered_out: {unfiltered_amount - filtered_amount}")

path = os.path.join(os.getcwd(), "AppleScrape", "Junkdata")
bad_links = analyze_links(path, 4)
filter_links("US_second_half.csv", bad_links, "filtered_links2.csv")
