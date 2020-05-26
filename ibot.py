import random
import re
import time
import traceback
import requests
import telebot
from bs4 import BeautifulSoup
from telebot import types

from config import *
from models import Items, Authors, Users

bot = telebot.TeleBot(telegram_key)


def check_text(text, short=True):
    s = text.lower().replace("(", "").replace(")", "").replace("plus", " + ").replace(
        "плюс", " + ").replace("айфон", "iphone").replace("х", "x")
    numbers = re.findall(r"\d+", s)
    for n in numbers:
        s = s.replace(n, f" {n} ")
    words = set(filter(lambda x: x != '', s.split(" ")))
    for conf in search_configs:
        names = conf["name"].split(" ")
        if len(set(names) & words) == len(names):
            for f in conf["filtrs"]:
                if f in item["name"]:
                    if conf["filtrs"][f] + 600 >= item["cost"] >= conf["filtrs"][f] - 2000:
                        return short or f != ''
                    break
            break
    return False


def get_page():
    r = requests.get("https://www.avito.ru/sankt-peterburg/telefony/iphone-ASgBAgICAUSeAt4J",
                     params={
                         "q": "iphone",
                         "s": "104"
                     },
                     headers={
                         'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
                                       'Chrome/80.0.3987.149 Safari/537.36',
                     }
                     )
    return r.text


def get_item_info(url):
    time.sleep(random.randint(10, 20))
    r = requests.get(url,
                     headers={
                         'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
                                       'Chrome/80.0.3987.149 Safari/537.36',
                     }
                     )
    data = {}
    soup = BeautifulSoup(r.text, 'html5lib')
    data["scam"] = "phoneMask" not in r.text
    data["author"] = soup.find("div", {"class": "seller-info-name js-seller-info-name"}).a.text.replace("\n", "")
    data["author_id"] = int(
        soup.find("div", {"class": "seller-info-name js-seller-info-name"}).a["href"].split("=")[-1])
    data["address"] = soup.find("span", {"class": "item-address__string"}).text.replace("\n", "")
    data["discr"] = soup.find("div", {"class": "item-description-text"}).text.replace("\n", " ")
    data["image"] = soup.find("img")["src"]
    if "http" not in data["image"]:
        data["image"] = data["image"].replace("//", "https://")
    if soup.find("span", {"class": "item-address-georeferences-item__content"}):
        data["address"] += ", м." + soup.find("span", {"class": "item-address-georeferences-item__content"}).text

    # assert "captcha" in r.text, "Ip baned"
    return data


def alarm_error(text):
    requests.get(f"https://alarmerbot.ru/?key={ALAMER_KEYS[0]}&message=Avito Iphone: {text}")


def success(item):
    item.update(get_item_info(item["url"]))
    Items.update({Items.author_id: item["author_id"],
                  Items.image: item["image"],
                  Items.address: item["address"],
                  Items.discr: item["discr"],
                  Items.scam: item["scam"],
                  }).where(Items.item_id == item["id"]).execute()

    author = Authors.get_or_none(author_id=item["author_id"])
    if author is None:
        author = Authors.create(name=item["author"], author_id=item["author_id"])
    if author.status <= 0:
        print("Author blocked")
        return
    if not check_text(item["name"] + " " + item["discr"], short=False):
        print("Bad description")
        return

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton(text="Описание on/off",
                                          callback_data=f"show-full_{item['id']}"),
               types.InlineKeyboardButton(text="Avito",
                                          url=item['url']),
               types.InlineKeyboardButton(text="Отписал 🖌", callback_data=f"writen_{item['id']}"),
               types.InlineKeyboardButton(text="Купил 📦", callback_data=f"buy_{item['id']}"),
               types.InlineKeyboardButton(text="🚫 продовца",
                                          callback_data=f"ban_{item['id']}"),
               types.InlineKeyboardButton(text="🗑 сообщение", callback_data=f"drop_{item['id']}"),
               )
    head = ""
    if item["scam"] and item["cost"] > 7000:
        markup.add(types.InlineKeyboardButton(text="Это скам📵", callback_data=f"skam_{item['id']}"))
        head = "❗️ВЕРОЯТНО СКАМ❗️\n"
    elif "срочно" in item["discr"].lower():
        head = "🕔️СРОЧНАЯ ПРОДАЖА🕔\n"
    users = Users.select().where(Users.status > 0).execute()
    for u in users:
        try:
            m = bot.send_photo(u.tel_id, item["image"],
                               caption=f"{head}Добален новый Iphone\n"
                                       f"Заголовок: {item['name']}\n"
                                       f"Цена: {item['cost']}\n"
                                       f"Местоположение: {item['address']}\n",
                               reply_markup=markup)

        except Exception as e:
            print(e)
            print(item)
            print(f"User {u.name} has disabled bot")


if __name__ == "__main__":
    print("Bot started")

    while True:
        try:
            soup = BeautifulSoup(get_page(), 'html5lib')
            cards = soup.find_all("div", {"class": "item_table-wrapper"})
            if len(cards) == 0:
                print("cars not found:")

            for card in cards:
                try:
                    adv = bool(card.find("a",
                                         {
                                             "class": "item_table-extended-description item_table-extended-description_blurred"}))
                    item = {}
                    item["name"] = card.h3.text
                    item["name"] = item["name"]
                    adv = (adv or "выбор" in item["name"])
                    adv = (adv or "Компания" in str(card))

                    item["url"] = "https://www.avito.ru" + card.find("a")["href"]
                    try:
                        item["cost"] = int(re.sub(r"[^\d]+", "", card.find("div", {"class": "snippet-price-row"}).text))
                    except:
                        item["cost"] = 0

                    if card.find("span", {"class": "item-address-georeferences-item__content"}):
                        item["address"] = card.find("span", {"class": "item-address-georeferences-item__content"}).text
                    else:
                        item["address"] = "Не указан"
                    item["id"] = int(item["url"].split("_")[-1].split("?")[0])
                    it = Items.get_or_none(Items.item_id == item["id"])

                    if it is None and item["cost"] < 10 ** 6:
                        Items.create(item_id=item["id"], cost=item["cost"],
                                     url=item["url"], name=item["name"])
                        if not adv:
                            print("Find new phone", item["name"], item["cost"])
                            if check_text(item["name"]):
                                success(item)

                except Exception as e:
                    print(e, card.find("a")["href"])
                    traceback.print_exc()

            print("=" * 70)
            print(f"Checked {len(cards)}")
            time.sleep(random.randint(20, 40))

        except Exception as e:
            alarm_error(str(e))
            print(e)
            traceback.print_exc()
            time.sleep(60)
