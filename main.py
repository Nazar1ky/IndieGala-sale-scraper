import os
import json
import time
import random
import datetime

import requests
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Cache-Control': 'max-age=0',
    'Cookie': None,
    'Sec-Ch-Ua': '"Google Chrome";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"Windows"',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
}

def save_data(data, file_name):
    if not os.path.exists("data/"):
        os.mkdir("data")
    
    with open(f"data/{file_name}", "w", encoding = "utf-8") as file:
        json.dump(data, file, ensure_ascii = False, indent = 4)

def get_data(captcha_cookies):
    headers['Cookie'] = f"visid_incap_255598={captcha_cookies['visid_incap_255598']}; incap_ses_1288_255598={captcha_cookies['incap_ses_1288_255598']}"

    data = []
    i = 1
    pages_count = 1

    while i <= pages_count:
        while True: # To make possible make many attempts
            time.sleep(random.randint(7, 12)) # To reduce load for captcha

            response = requests.get(f"https://www.indiegala.com/games/ajax/on-sale/lowest-price/{i}", headers=headers)

            try:
                html = response.json()['html']
            except:
                print(f"Error occurred on page #{i}\n{response.content}")
                time.sleep(random.randint(10, 20))

            print(f"Page #{i} successfully scraped!")

            soup = BeautifulSoup(html, "lxml")

            pages_count = int(soup.find_all("div", class_ = "page-link-cont")[-1].find("a").get("onclick").split("/")[-1].split("'")[0])
            products = soup.find_all("div", class_ = "main-list-results-item")

            for product in products:
                product_info = product.find("h3", class_ = "bg-gradient-red").find("a")
                product_title = product_info.text
                product_url = f"https://www.indiegala.com{product_info.get("href")}"
                product_discount = product.find("div", class_ = "main-list-results-item-discount").text
                product_price_without_discount = product.find("div", class_ = "main-list-results-item-price-old").text
                product_price_with_discount = product.find("div", class_ = "main-list-results-item-price-new").text

                data.append({
                    "product_title": product_title,
                    "product_url": product_url,
                    "product_discount": product_discount,
                    "product_price_without_discount": product_price_without_discount,
                    "product_price_with_discount": product_price_with_discount
                })
            i += 1
            break

    return data

def bypass_captcha():
    captcha_cookies = None

    try:
        options = webdriver.ChromeOptions()
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36")
        options.add_argument("--headless=new")
        driver = webdriver.Chrome(options=options)

        driver.get("https://www.indiegala.com/games/on-sale")

        wait = WebDriverWait(driver, timeout=15)
        element = driver.find_element(By.CSS_SELECTOR, "div.page-link-cont.left a")
        wait.until(lambda d : element.is_displayed())

        # driver.save_screenshot("test.png")

        cookies = driver.get_cookies()
        
        captcha_cookies = {
            "visid_incap_255598": None,
            "incap_ses_1288_255598": None
        }

        for cookie in cookies:
            if cookie['name'] in captcha_cookies:
                captcha_cookies[cookie['name']] = cookie['value']

    except Exception as e:
        print(e)

    finally:
        driver.quit()
        return captcha_cookies

def main():
    print("Bypassing Captcha...")
    page_info = bypass_captcha()
    print("Captcha bypassed! Parsing...")

    data = get_data(page_info)
    if data == 0:
        return
    
    file_name = f"{datetime.datetime.now().strftime("%d_%m_%Y")}.json"

    save_data(data, file_name)
    
if __name__ == "__main__":
    main()