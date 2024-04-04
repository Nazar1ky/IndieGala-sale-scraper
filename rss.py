import os
import json
import datetime
import requests
from bs4 import BeautifulSoup


def save_data(data, file_name):
    if not os.path.exists("data_rss/"):
        os.mkdir("data_rss")

    with open(f"data_rss/{file_name}", "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def get_page_count():
    response = requests.get(f"https://www.indiegala.com/store_games_rss?sale=true")
    soup = BeautifulSoup(response.content, "xml")

    total_pages = int(soup.find("totalPages").text)

    return total_pages


def get_data():
    # sale = "true" if only_sale_games else "false"

    data = []

    total_pages = get_page_count()

    for i in range(1, total_pages + 1):
        print(f"Scraping {i}/{total_pages}")

        response = requests.get(
            f"https://www.indiegala.com/store_games_rss?page={i}&sale=true"
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
                        product_discount_end
                    ).strftime("%d/%m/Y"),
                    "blacklisted_countries": blacklisted_countries,
                }
            )
    data.sort(key=lambda x: x["product_price_with_discount"])

    return data


def main():
    data = get_data()

    file_name = f"{datetime.datetime.now().strftime("%d_%m_%Y")}.json"

    save_data(data, file_name)


if __name__ == "__main__":
    main()
