import datetime  # noqa: D100
import json
import re
import time
from pathlib import Path
from random import randint

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By


def save_data(data: json, file_name: str) -> None:
    """Create JSON file with json data."""
    if not Path("data/").exists():
        Path("data").mkdir()

    with Path(f"data/{file_name}").open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def remove_duplicates_and_sort(products: list[dict]) -> list[dict]:
    """Return sorted products and removed duplicate products."""
    products = sorted(products, key=lambda x: float(re.match(r"[+-]?([0-9]*[.])?[0-9]+", x["product_price_with_discount"])[0]))

    products_title = []

    for i, product in enumerate(products):
        if product["product_title"] in products_title:
            del products[i]

    return products

def parse_page(html: str) -> tuple[int, list[dict]]:
    """Scrap current page HTML. Return page count and products."""
    parsed_products = []
    soup = BeautifulSoup(html, "lxml")

    products = soup.find_all("div", class_="main-list-results-item")

    for product in products:
        product_info = product.find("h3", class_="bg-gradient-red").find("a")
        product_title = product_info.text
        product_url = f"https://www.indiegala.com{product_info.get('href')}"
        product_discount = product.find(
            "div",
            class_="main-list-results-item-discount",
        ).text

        product_price_without_discount = product.find(
            "div",
            class_="main-list-results-item-price-old",
        ).text

        product_price_with_discount = product.find(
            "div",
            class_="main-list-results-item-price-new",
        ).text

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

def get_all_data() -> list[dict]:
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

        while current_page_number <= pages_count if pages_count else 1:
            print(f"Scraping: {current_page_number}/{pages_count}")
            driver.get(f"https://www.indiegala.com/games/ajax/on-sale/lowest-price/{current_page_number}")

            current_page_data = json.loads(driver.find_element(By.TAG_NAME, "pre").text)

            _pages_count, products = parse_page(current_page_data["html"])

            pages_count = pages_count or _pages_count

            data.extend(products)

            current_page_number += 1

            time.sleep(randint(3, 6))  # noqa: S311

    finally:
        driver.quit()

    return data


def main() -> None:
    """Run the script."""
    print("Scraping...")
    data = get_all_data()

    print("Sorting products...")
    print(data)
    data = remove_duplicates_and_sort(data)

    print("Saving file...")
    file_name = f"{datetime.datetime.now(tz=datetime.UTC).strftime('%d_%m_%Y')}.json"
    save_data(data, file_name)

    print(f"Done! Total products: {len(data)}")
if __name__ == "__main__":
    main()
