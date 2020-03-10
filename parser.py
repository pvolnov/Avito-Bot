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

    def __init__(self, driver, alamer_key):
        self.driver = driver
        self.alamer_key = alamer_key

    def send_mail(self, url, text):
        self.driver.get(url)
        try:
            time.sleep(2)
            page = self.driver.page_source
            soup = BeautifulSoup(page, 'html5lib')

            clas = soup.find("button", {"data-marker": "messenger-button/button"})
            if clas is None:
                clas = soup.find("a", {"data-marker": "messenger-button/link"})["class"]
            else:
                clas = clas["class"]
            clas = " ".join(clas)

            script = f'document.getElementsByClassName("{clas}")[0].click()'
            self.driver.execute_script(script)

            url = self.driver.current_url
            time.sleep(3)
            try:
                self.driver.find_element_by_tag_name("textarea").send_keys(text, Keys.ENTER)  # Keys.ENTER
            except Exception as e:
                print("textarea error", e)
                time.sleep(6)
                self.driver.find_element_by_tag_name("textarea").send_keys(text, Keys.ENTER)  # Keys.ENTER
            time.sleep(1)
            return url
        except Exception as e:
            return None

    def check_new_mails(self, url):
        self.driver.get(url)
        time.sleep(1)
        page = self.driver.page_source
        soup = BeautifulSoup(page, 'html5lib')
        return len(soup.find_all("div", {"data-marker": "message"})) > 1

    def alarm(self, text):
        print(f"{datetime.now().time()}: {text}")
        requests.get(f"https://alarmerbot.ru/?key={self.alamer_key}&message={text}")

    def get_items_from_page(self, page):
        soup = BeautifulSoup(page, 'html5lib')

        items = []
        for item in soup.find_all("div", {"class": "item__line"}):
            url = "https://www.avito.ru" + item.a["href"]
            cost = item.find("div", {"class": "snippet-price-row"}).span.text.replace("\n", "").replace(" ", "")
            cost = re.findall(r'\d+', cost)
            img = item.img["src"]
            if len(cost) > 0:
                cost = cost[0]
            else:
                cost = 0
            cost = int(cost)
            name = item.h3.text

            items.append({
                "photo": img,
                "name": name,
                "cost": cost,
                "url": url
            })

        return items

    async def update_tasks(self, save=False, message=True):
        tasks = Tasks.select()
        workers = []
        async with ClientSession() as session:
            for t in tasks:
                work = asyncio.ensure_future(fetch(t, session))
                workers.append(work)

            pages = await asyncio.gather(*workers)

        for page, task in pages:
            items = self.get_items_from_page(page)
            print(f"Обновлен раздел {task.name}, получено {len(items)} товаров time: {datetime.now()}")
            old_items = Items.select().execute()
            old_items_urls = [i.url for i in old_items]
            for i in items:
                if i["url"] not in old_items_urls:
                    print("New item:", i["url"])
                    if int(i["cost"]) <= task.max_cost and not save:
                        if message:
                            i["message_url"] = self.send_mail(i["url"], task.message_text)
                        else:
                            i["message_url"] = None

                        if i["message_url"] is None:
                            self.alarm(
                                f"Добавлен новый товар {i['name']} по цене {i['cost']}, но сообщение отправлять нельзя\n{i['url']}")
                        else:
                            i["surveillance"] = True
                            self.alarm(f"Новое сообщение отправлено {i['name']} ({i['cost']})\n{i['message_url']}")
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
