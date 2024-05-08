import datetime
import json
import re
import time
import urllib.parse
from pathlib import Path
from random import randint

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By

NUMBER_REGEX = re.compile(r"[+-]?([0-9]*[.])?[0-9]+") # Reference: https://stackoverflow.com/a/12643073

def save_data(data: json, file_name: str) -> None:
    """Create JSON file with json data."""
    if not Path("data/").exists():
        Path("data").mkdir()

    with Path(f"data/{file_name}").open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

def check_price(price: str) -> bool:
    """Return True if all okay. Return False if prices in wrong format."""
    match = re.search(NUMBER_REGEX, price)

    if not match:
        return False

    return True

def check_discount(discount: str) -> bool:
    """Return true/false if discount is okay."""
    match = re.search(r"\d+", discount)

    if match and int(match[0]) <= 100 and int(match[0]) >= 0:  # noqa: PLR2004
        return True

    return False

def find_numbers(price: str) -> float:
    """Return founded number in str."""
    match = re.search(NUMBER_REGEX, price)

    if not match:
        return -1

    return float(match[0])

def remove_duplicates_and_sort(products: list[dict]) -> list[dict]:
    """Return sorted products and removed duplicate products."""
    products = sorted(products, key=lambda x: find_numbers(x["product_price_with_discount"]))

    products_title = []

    for i, product in enumerate(products):
        if product["product_title"] in products_title:
            del products[i]

    return products

# Reference: https://stackoverflow.com/a/63220249
def add_cookie(driver: webdriver.Chrome, cookie: dict) -> None:
    """That function add cookie before visiting first time site."""
    driver.execute_cdp_cmd("Network.enable", {})
    driver.execute_cdp_cmd("Network.setCookie", cookie)
    driver.execute_cdp_cmd("Network.disable", {})

def parse_page(html: str) -> tuple[int, list[dict]]:
    """Scrap current page HTML. Return page count and products."""
    parsed_products = []
    soup = BeautifulSoup(html, "lxml")

    products = soup.find_all("div", class_="main-list-results-item")

    for product in products:
        try:
            product_info = product.find("h3", class_="bg-gradient-red").find("a")
        except AttributeError as E:
            print(f"product_info can't be founded. {E}")
            continue
        product_title = product_info.text
        product_url = f"https://www.indiegala.com{product_info.get('href')}"

        product_discount = product.find(
            "div",
            class_="main-list-results-item-discount",
        )

        if not product_discount:
            print(f"Skipped: {product_title}")
            continue

        product_discount = product_discount.text.replace(" ", "")

        if not check_discount(product_discount):
            product_discount = None

        product_price_without_discount = product.find(
            "div",
            class_="main-list-results-item-price-old",
        ).text

        product_price_with_discount = product.find(
            "div",
            class_="main-list-results-item-price-new",
        ).text

        if not check_price(product_price_with_discount) or not check_price(product_price_without_discount):
            print(f"Skipped product: {product_title} | Price With Discount: {product_price_with_discount.strip()} | Price Without Discount: {product_price_without_discount.strip()}")
            continue

        parsed_products.append(
            {
                "product_title": product_title,
                "product_url": product_url,
                "product_discount": product_discount,
                "product_price_with_discount": product_price_with_discount,
                "product_price_without_discount": product_price_without_discount,
            },
        )

    pages_count = int(
        soup.find_all("div", class_="page-link-cont")[-1]
        .find("a")
        .get("onclick")
        .split("/")[-1]
        .split("'")[0],
    )

    return pages_count, parsed_products

def get_all_data(filters: str | None = None) -> list[dict]:
    """Get all products from all pages."""
    data = []

    current_page_number = 1
    pages_count = 1

    try:
        options = webdriver.ChromeOptions()
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36",
        )
        options.add_argument("--headless=new")
        driver = webdriver.Chrome(options=options)

        if filters:
            filters = urllib.parse.quote(filters)
            add_cookie(driver, {"name": "search-params", "value": filters, "domain" : "www.indiegala.com"})

            # driver.get("https://www.indiegala.com/games/ajax/on-sale/ranking/")
            # driver.add_cookie({"name": "search-params", "value": filters})

        while current_page_number <= pages_count:
            print(f"Scraping: {current_page_number}/{pages_count}")
            driver.get(f"https://www.indiegala.com/games/ajax/on-sale/lowest-price/{current_page_number}")

            pre_element = driver.find_element(By.TAG_NAME, "pre")
            if not pre_element:
                print("Page can't be loaded")
                break

            current_page_data = json.loads(pre_element.text)

            pages_count, products = parse_page(current_page_data["html"])

            data.extend(products)

            current_page_number += 1

            time.sleep(randint(3, 6))  # noqa: S311

    finally:
        driver.quit()

    return data


def main() -> None:
    """Run the script."""
    print("Scraping...")
    data = get_all_data() # Cookie example: '{"platform":["steam"],"product_type":"game"}'

    print("Sorting products...")

    data = remove_duplicates_and_sort(data)

    print("Saving file...")
    file_name = f"{datetime.datetime.now().strftime('%d_%m_%Y')}.json"  # noqa: DTZ005
    save_data(data, file_name)

    print(f"Done! Total products: {len(data)}")

if __name__ == "__main__":
    main()
