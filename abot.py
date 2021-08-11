import random
import re
import sys
import time
import traceback

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver import DesiredCapabilities

from models import Items

# https://alarmerbot.ru/?key=273d7c-e8ce30-133a55&message=%D0%91%D0%BE%D1%82%20%D0%BE%D1%81%D1%82%D0%B0%D0%BD%D0%BE%D0%B2%D0%BB%D0%B5%D0%BD.
ALAMER_KEYS = [
    "df548f-61ac83-624ea4",
    "273d7c-e8ce30-133a55",
    "472027-53fe22-5b995f",
    "6fe15f-8aafbd-7d741a",
    "cf9489-61b9d9-0681be",
    "355fd8-984380-f3ed60",
]

base_urls = [
    "https://www.avito.ru/permskiy_kray/avtomobili/inomarki/mekhanika",
    "https://www.avito.ru/permskiy_kray/avtomobili/inomarki/avtomat",
    "https://www.avito.ru/perm/avtomobili/chevrolet-ASgBAgICAUTgtg32lyg?cd=1&f=ASgBAgECAUTgtg32lygBRfgCF3siZnJvbSI6Mjg0NCwidG8iOm51bGx9&radius=400",
    "https://www.avito.ru/perm/avtomobili/honda-ASgBAgICAUTgtg2ymCg?cd=1&f=ASgBAgECAUTgtg2ymCgBRfgCFnsiZnJvbSI6ODk4LCJ0byI6bnVsbH0&proprofile=1&radius=400",
    "https://www.avito.ru/perm/avtomobili/ford-ASgBAgICAUTgtg2cmCg?cd=1&f=ASgBAgECAUTgtg2cmCgBRfgCFnsiZnJvbSI6ODk4LCJ0byI6bnVsbH0&proprofile=1&radius=400",
    "https://www.avito.ru/perm/avtomobili/kia-ASgBAgICAUTgtg3KmCg?cd=1&f=ASgBAgECAUTgtg3KmCgBRfgCF3siZnJvbSI6Mjg0NCwidG8iOm51bGx9&proprofile=1&radius=400",
    "https://www.avito.ru/perm/avtomobili/hyundai-ASgBAgICAUTgtg2imzE?cd=1&f=ASgBAgECAUTgtg2imzEBRfgCF3siZnJvbSI6Mjg0NCwidG8iOm51bGx9&proprofile=1&radius=400",
    "https://www.avito.ru/perm/avtomobili/lexus-ASgBAgICAUTgtg3WmCg?cd=1&f=ASgBAgECAUTgtg3WmCgBRfgCFnsiZnJvbSI6OTAxLCJ0byI6bnVsbH0&proprofile=1&radius=400",
    "https://www.avito.ru/perm/avtomobili/mazda-ASgBAgICAUTgtg3mmCg?cd=1&f=ASgBAgECAUTgtg3mmCgBRfgCFnsiZnJvbSI6OTAxLCJ0byI6bnVsbH0&proprofile=1&radius=400",
    "https://www.avito.ru/perm/avtomobili/mitsubishi-ASgBAgICAUTgtg3ymCg?cd=1&f=ASgBAgECAUTgtg3ymCgBRfgCFnsiZnJvbSI6OTAwLCJ0byI6bnVsbH0&proprofile=1&radius=400",
    "https://www.avito.ru/perm/avtomobili/nissan-ASgBAgICAUTgtg36mCg?cd=1&f=ASgBAgECAUTgtg36mCgBRfgCFnsiZnJvbSI6OTAwLCJ0byI6bnVsbH0&proprofile=1&radius=400",
    "https://www.avito.ru/perm/avtomobili/renault-ASgBAgICAUTgtg2MmSg?cd=1&f=ASgBAgECAUTgtg2MmSgBRfgCF3siZnJvbSI6Mjg0NCwidG8iOm51bGx9&proprofile=1&radius=400",
    "https://www.avito.ru/perm/avtomobili/skoda-ASgBAgICAUTgtg2emSg?cd=1&f=ASgBAgECAUTgtg2emSgBRfgCFnsiZnJvbSI6OTAwLCJ0byI6bnVsbH0&proprofile=1&radius=400",
    "https://www.avito.ru/perm/avtomobili/volkswagen-ASgBAgICAUTgtg24mSg?cd=1&f=ASgBAgECAUTgtg24mSgBRfgCFnsiZnJvbSI6OTAwLCJ0byI6bnVsbH0&proprofile=1&radius=400",
]

driver = webdriver.Remote(
    command_executor="http://dig2.neafiol.site:4444/wd/hub",
    desired_capabilities={"browserName": "firefox", "sessionTimeout": "5m"},
)

# driver = webdriver.Chrome()
cookies = {}


def update_cookies(base_url):
    driver.get(base_url)
    time.sleep(4)
    global cookies
    cookies = {c["name"]: c["value"] for c in driver.get_cookies()}


def get_page(base_url, page):
    # r = requests.get(base_url,
    #                  params={
    #                      "s": 104,
    #                      "cd": 1,
    #                      "p": page},
    #                  cookies=cookies
    #                  )
    driver.get(base_url + f"?s=104&cd=1&p={page}")
    if "http://yandex.ru/internet" in driver.page_source:
        # if "http://yandex.ru/internet" in r.text:
        print("Banned")
        update_cookies(base_url)
    # return r.text
    return driver.page_source


def alarm_error(text):
    requests.get(
        f"https://alarmerbot.ru/?key={ALAMER_KEYS[0]}&message=Avito auto abot error: {text} v2"
    )


def alarm(item, old_cost, cost):
    cost = str(cost)
    old_cost = str(old_cost)

    c1 = old_cost[:-6] + " " + old_cost[-6:-3] + " " + old_cost[-3:]
    c2 = cost[:-6] + " " + cost[-6:-3] + " " + cost[-3:]

    for key in ALAMER_KEYS:
        requests.get(
            f"https://alarmerbot.ru/?key={key}&message=Изменение цены на автомобиль\n"
            f"Заголовок: {item['name']}\n"
            f"Местоположение: {item['adress']}\n"
            f"Старая цена: {c1}\n"
            f"Новая цена: {c2}\n"
            f"Ссылка: {item['url']}\n"
        )


if __name__ == "__main__":
    alarm_error("Start avito abot")
    update_cookies(base_urls[0])

    while True:
        for base_url in base_urls:
            print("Base_url:", base_url)
            # try:
            page = get_page(base_url, 2)
            soup = BeautifulSoup(page, "html5lib")

            count = int(re.findall(r"page\(\d+", page)[-1].replace("page(", ""))
            print(f"Find pages: {count}")
            urls_all = []

            for i in range(1, count + 1):
                soup = BeautifulSoup(get_page(base_url, i), "html5lib")
                urls = soup.find_all("a", {"itemprop": "url"})
                cards = soup.find_all("div", {"data-marker": "item"})
                if len(cards) == 0:
                    print("cars not found:", i)

                for card in cards:
                    item = {}
                    item["name"] = card.find("h3", {"itemprop": "name"}).text
                    # check year
                    old = True
                    for year in range(2005, 2022):
                        if str(year) in item["name"]:
                            old = False
                            break
                    if old:
                        continue

                    item["cost"] = re.sub(
                        r"[^\d]",
                        "",
                        card.find(
                            "span", {"class": lambda x: x and "price-text" in x}
                        ).text,
                    )
                    if card.find(
                        "div", {"class": lambda x: x and "geo-georeferences" in x}
                    ):
                        item["adress"] = card.find(
                            "div", {"class": lambda x: x and "geo-georeferences" in x}
                        ).span.text
                    else:
                        item["adress"] = "Не указан"
                    item["url"] = "https://www.avito.ru" + card.find("a")["href"]

                    # print(item["url"])
                    item["id"] = int(
                        item["url"].replace("?src=bp_catalog", "").split("_")[-1]
                    )
                    it = Items.get_or_none(Items.item_id == item["id"])
                    urls_all.append(item["url"])
                    print(item)
                    if it is None:
                        print("Find new car", item["name"])
                        Items.create(item_id=item["id"], cost=item["cost"])
                    else:
                        if int(it.cost) != int(item["cost"]):
                            print(it.cost, item["cost"])
                            alarm(item, it.cost, item["cost"])

                            it.cost = item["cost"]
                            it.save()

                print(f"Checked {len(cards)}")
                time.sleep(random.randint(60, 70))

            print("=" * 70)
            print("Update complete")

        # except Exception as e:
        #     alarm_error(str(e) + "\nbase_url: "+base_url)
        #     print(e)
        #     traceback.print_exc()
        #     time.sleep(60)
