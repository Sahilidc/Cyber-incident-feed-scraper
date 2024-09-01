import requests
import ssl
import socket
import json
import os
import re
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from pymongo import MongoClient  # Import MongoDB client

def is_https(url):
    """Check if the URL uses HTTPS."""
    return url.startswith('https://')

def is_ssl_certificate_valid(url):
    """Check if the SSL certificate of the URL is valid."""
    try:
        parsed_url = requests.utils.urlparse(url)
        hostname = parsed_url.hostname
        port = parsed_url.port or 443
        context = ssl.create_default_context()
        with socket.create_connection((hostname, port)) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                ssock.getpeercert()
        return True
    except Exception as e:
        print(f"SSL certificate validation failed: {e}")
        return False

# Define the URL of the webpage to scrape
url = "https://cyware.com/search?search=india"

# Check HTTPS and SSL certificate
if not is_https(url):
    print("URL does not use HTTPS.")
else:
    if not is_ssl_certificate_valid(url):
        print("SSL certificate is not valid.")
    else:
        # Initialize the Firefox WebDriver
        driver = webdriver.Firefox()

        # Open the webpage
        driver.get(url)

        # Allow the page to load
        time.sleep(2)

        # Find all the article containers
        articles = driver.find_elements(By.CLASS_NAME, "cy-panel.cy-card.mb-4")

        # Initialize a list to hold the extracted data
        news_data = []

        # Loop through each article and extract the relevant details
        for article in articles:
            # Find the title
            title = article.find_element(By.CLASS_NAME, "cy-card__title").text.strip() if article.find_element(By.CLASS_NAME, "cy-card__title") else None

            # Find the summary
            summary = article.find_element(By.CLASS_NAME, "cy-card__description").text.strip() if article.find_element(By.CLASS_NAME, "cy-card__description") else None

            # Find the link
            link = article.find_element(By.TAG_NAME, "a").get_attribute("href") if article.find_element(By.TAG_NAME, "a") else None

            # Find the date
            date_elements = article.find_elements(By.CLASS_NAME, "cy-card__meta")
            date = None
            for elem in date_elements:
                if re.match(r'\w+ \d{1,2}, \d{4}', elem.text.strip()):
                    date = elem.text.strip()
                    break

            # Create a dictionary for each news article
            news_item = {
                "title": title,
                "summary": summary,
                "link": link,
                "date": date
            }

            # Append the dictionary to the list
            news_data.append(news_item)

        # Get the Desktop path dynamically
        desktop_path = os.path.expanduser("~/Desktop/cyware_news.json")

        # Save the extracted data as a JSON file on your Desktop with formatted output
        with open(desktop_path, "w") as json_file:
            json.dump(news_data, json_file, indent=4, separators=(',', ': '))

        # Connect to MongoDB
        client = MongoClient("mongodb://localhost:27017/")  # Update with your MongoDB URI if different
        db = client["cyber_news_db"]  # Create/use a database named "cyber_news_db"
        collection = db["cyware_news"]  # Create/use a collection named "cyware_news"

        # Insert data into MongoDB
        if news_data:  # Check if there is data to insert
            collection.insert_many(news_data)

        # Close the WebDriver
        driver.close()

        print("Scraping completed, data saved to cyware_news.json, and inserted into MongoDB.")
