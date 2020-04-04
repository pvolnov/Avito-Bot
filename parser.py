import asyncio
import re
import time
from datetime import datetime

import requests
from aiohttp import ClientSession
from bs4 import BeautifulSoup
from selenium.webdriver.common.keys import Keys

from models import Tasks, Items


async def fetch(task: Tasks, session):
    async with session.get(task.url) as response:
        return (await response.read()).decode("utf-8"), task


class Parser:

    def __init__(self, driver, alamer_keys=[], cookies={}):
        self.driver = driver
        self.alamer_keys = alamer_keys
        self.cookies = cookies

    def send_mail(self, url, text):
        print("Send mailing")
        self.driver.get(url)
        time.sleep(3)
        if len(self.driver.find_elements_by_xpath("//button[@data-marker='messenger-button/button']")) == 0:
            return ""

        class_ = self.driver.find_elements_by_xpath("//button[@data-marker='messenger-button/button']")[
            -1].get_attribute('class')
        self.driver.execute_script(f"document.getElementsByClassName('{class_}')[0].click()")
        print("Code executed")
        retr = 15
        while len(self.driver.find_elements_by_tag_name("textarea")) == 0 and retr > 0:
            time.sleep(1)
            retr -= 1
            print("Retriing..")

        if retr > 0:
            url = self.driver.current_url
            self.driver.find_element_by_tag_name("textarea").send_keys(text, Keys.ENTER)  # Keys.ENTER
            return url
        else:
            return ""

    def check_new_mails(self, url):
        self.driver.get(url)
        time.sleep(1)
        page = self.driver.page_source
        soup = BeautifulSoup(page, 'html5lib')
        return len(soup.find_all("div", {"data-marker": "message"})) > 1

    def alarm(self, text):
        print(f"{datetime.now().time()}: {text}")
        for key in self.alamer_keys:
            requests.get(f"https://alarmerbot.ru/?key={key}&message={text}")

    def get_items_from_page(self, page):
        soup = BeautifulSoup(page, 'html5lib')

        items = []
        for item in soup.find_all("div", {"class": "item__line"}):
            url = "https://www.avito.ru" + item.a["href"]
            cost = item.find("div", {"class": "snippet-price-row"}).span.text.replace("\n", "").replace(" ", "")
            cost = re.findall(r'\d+', cost)
            if item.img:
                img = item.img["src"]
            else:
                img = ""
            if len(cost) > 0:
                cost = cost[0]
            else:
                cost = 0
            cost = int(cost)
            name = item.h3.text
            shop = item.find("div", {"class": "data"}).find("a", {"class": "snippet-link"})
            shop_inf = item.find("div", {"class": "item_table-wrapper"}).find("a")

            if shop is None and shop_inf is None:
                items.append({
                    "photo": img,
                    "name": name,
                    "cost": cost,
                    "url": url
                })

        return items

    def get_item_discr(self, url):
        page = requests.get(url).text
        soup = BeautifulSoup(page, 'html5lib')
        return soup.find("div", {"itemprop": "description"}).text

    def update_tasks(self, save=False, message=True):
        tasks = Tasks.select()
        parts_urls = []
        pages = []

        for t in tasks:
            if t.url not in parts_urls:
                page = requests.get(t.url).text
                parts_urls.append(t.url)
                pages.append(page)

        print("Uploading pages:", len(pages), "from", len(tasks), "tasks")
        old_items = Items.select().execute()
        old_items_urls = [i.url for i in old_items]
        new_items = []
        for page in pages:
            items = self.get_items_from_page(page)
            assert len(items) > 0, "page blocked!\n\n" + page

            print(f"Find {len(items)} items")
            for i in items:
                if i["url"] not in old_items_urls:
                    print("New item:", i["url"])
                    if save:
                        Items.create(**i)
                    else:
                        i["discr"] = self.get_item_discr(i["url"])
                        new_items.append(i)
                        old_items_urls.append(i["url"])

        created_items = []
        for task in tasks:
            for i in new_items:
                if task.min_cost <= i["cost"] <= task.max_cost and not save \
                        and i["url"] not in created_items:

                    sname = (i["discr"] + i["name"]).lower().replace(" ", "")

                    if not task.model in sname or task.params not in sname:
                        cont = False
                        for v in [16, 32, 64, 128, 256]:
                            if str(v) in sname:
                                cont = True
                        if cont or task.model not in sname:
                            continue

                    if message and i["cost"] > task.mes_cost:
                        i["message_url"] = self.send_mail(i["url"], task.message_text)
                    else:
                        i["message_url"] = ""

                    print("Find new OK item")

                    if i["message_url"] == "":
                        self.alarm(
                            f"Добавлен новый товар {i['name']} по цене {i['cost']}\n{i['url']}")
                    else:
                        i["surveillance"] = True
                        self.alarm(f"Новое сообщение отправлено {i['name']} ({i['cost']})\n{i['message_url']}")
                    Items.create(**i)
                    created_items.append(i["url"])

        for i in new_items:
            if i["url"] not in created_items:
                Items.create(**i)

    def check_new_messanges(self):
        for item in Items.select().where((Items.response == False) & (Items.surveillance == True)).order_by(
                Items.update_order.desc()).limit(2).execute():
            print(f"Проверка ответа по товару {item.name}")
            if self.check_new_mails(item.message_url):
                item.response = True
                item.update_order = 0
                item.save()
                self.alarm(f"Получен ответ по  товару {item.name}\n{item.message_url}")
            else:
                print("Ответ еще не получен")
        Items.update({Items.update_order: Items.update_order + 1})
