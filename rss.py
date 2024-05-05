import datetime  # noqa: D100
import json
import operator
from pathlib import Path

import requests
from bs4 import BeautifulSoup

TIMEOUT = 30

def save_data(data: list[dict], file_name: str) -> None:
    """Save file with products to folder data_rss."""
    if not Path("data_rss/").exists():
        Path("data_rss").mkdir()

    with Path(f"data_rss/{file_name}").open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def get_page_count(sale: bool) -> int:  # noqa: FBT001
    """Get pages count."""
    response = requests.get(
        f"https://www.indiegala.com/store_games_rss?sale={sale}",
        timeout=TIMEOUT,
    )
    soup = BeautifulSoup(response.content, "xml")

    return int(soup.find("totalPages").text)


def get_data(*, only_sale_games: bool = True) -> list[dict]:
    """Scrap all data."""
    sale = "true" if only_sale_games else "false"

    data = []

    total_pages = get_page_count(sale)

    for i in range(1, total_pages + 1):
        print(f"Scraping: {i}/{total_pages}")

        response = requests.get(
            f"https://www.indiegala.com/store_games_rss?page={i}&sale={sale}",
            timeout=TIMEOUT,
        )
        soup = BeautifulSoup(response.content, "xml")

        products = soup.find_all("item")

        for product in products:
            product_title = product.find("title").text
            product_url = product.find("link").text
            product_discount = product.find("discountPercentUSD").text
            product_price_with_discount = product.find("discountPriceUSD").text
            product_price_without_discount = product.find("priceUSD").text
            product_discount_end = product.find("discountEnd").text
            blacklisted_countries = product.find("notAvailableRegions").text

            data.append(
                {
                    "product_title": product_title,
                    "product_url": product_url,
                    "product_discount": f"{float(product_discount)}%",
                    "product_price_without_discount": f"{product_price_without_discount}$",
                    "product_price_with_discount": f"{product_price_with_discount}$",
                    "product_discount_end": datetime.datetime.fromisoformat(
                        product_discount_end,
                    ).strftime("%d/%m/Y"),
                    "blacklisted_countries": blacklisted_countries,
                },
            )
    data.sort(key=operator.itemgetter("product_price_with_discount"))

    return data


def main() -> None:
    """Run the script."""
    print("Scraping...")
    data = get_data()

    print("Saving...")
    file_name = f"{datetime.datetime.now(tz=datetime.UTC).strftime("%d_%m_%Y")}.json"
    save_data(data, file_name)

    print(f"Done! Total products: {len(data)}")

if __name__ == "__main__":
    main()
