import time
import csv
import re
import logging
import wikipedia
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

"""
This script is our attempt to parse AllSides site, that features political bias asessment for most of the popular western media sites.
This cite is protected by CloudFlare, so we couldn't parse it through code. 
The data in news_sources was collected manually by our team.
"""

# Configure logging to output to the console.
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def get_country(source_name):
    """
    Attempts to determine the country of the company that owns the news site.
    It does so by:
      1. Searching for the news site's Wikipedia page.
      2. Extracting the owner name using phrases like 'owned by' or 'parent company'.
      3. Searching for the owner's Wikipedia page.
      4. Extracting the country from the owner's page summary using phrases like 'based in' or 'headquartered in'.
    """
    logging.info(f"Attempting to determine country for: {source_name}")
    try:
        results = wikipedia.search(source_name)
        if results:
            news_page = wikipedia.page(results[0])
            summary = news_page.summary
            # Look for ownership information
            owner_match = re.search(r"(?:owned by|parent company) (?:the )?([^,.]+)", summary, re.IGNORECASE)
            if owner_match:
                owner_name = owner_match.group(1).strip()
                logging.info(f"Found owner: {owner_name} for {source_name}")
                owner_results = wikipedia.search(owner_name)
                if owner_results:
                    owner_page = wikipedia.page(owner_results[0])
                    owner_summary = owner_page.summary
                    country_match = re.search(r"(?:based in|headquartered in) ([A-Z][a-zA-Z\s,]+)", owner_summary)
                    if country_match:
                        country = country_match.group(1).strip()
                        logging.info(f"Determined country: {country} for owner: {owner_name}")
                        return country
    except Exception as e:
        logging.error(f"Error determining country for {source_name}: {e}")
    return "Unknown"


def main():
    url = (
        "https://www.allsides.com/media-bias/ratings?"
        "field_featured_bias_rating_value=All&"
        "field_news_source_type_tid[1]=1&"
        "field_news_source_type_tid[2]=2&"
        "field_news_source_type_tid[3]=3&"
        "field_news_source_type_tid[4]=4"
    )

    # Set up Selenium without headless mode so the browser is visible.
    options = Options()
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    logging.info("Launching browser...")
    driver = webdriver.Chrome(options=options)
    driver.get(url)

    logging.info(
        "Waiting for user to pass Cloudflare test. Please complete the challenge in the opened browser, then press Enter here."
    )
    input("Press Enter after you have passed the Cloudflare test...")

    logging.info("User passed Cloudflare test. Proceeding with parsing.")
    time.sleep(3)  # Wait a moment to ensure page stability

    html = driver.page_source
    driver.quit()

    soup = BeautifulSoup(html, "html.parser")

    # Locate the news source entries (adjust the selector if needed)
    rows = soup.find_all("div", class_="views-row")
    logging.info(f"Found {len(rows)} news source rows.")

    data = []

    for row in rows:
        title_div = row.find("div", class_="views-field-title")
        if title_div:
            a_tag = title_div.find("a")
            if a_tag:
                name = a_tag.get_text(strip=True)
                link = "https://www.allsides.com" + a_tag["href"]
                logging.info(f"Parsing news source: {name}")
            else:
                logging.warning("No anchor tag found in title_div; skipping row.")
                continue
        else:
            logging.warning("No title_div found; skipping row.")
            continue

        bias_div = row.find("div", class_="views-field-field-media-bias-rating-value")
        political_bias = bias_div.get_text(strip=True) if bias_div else "N/A"

        # Determine the country of the owning company
        country = get_country(name)

        data.append({"Name": name, "Link": link, "Country": country, "Political Bias": political_bias})

    logging.info(f"Writing {len(data)} entries to CSV.")
    with open("media_bias.csv", "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["Name", "Link", "Country", "Political Bias"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for entry in data:
            writer.writerow(entry)

    logging.info("CSV file 'media_bias.csv' written successfully.")


if __name__ == "__main__":
    main()
