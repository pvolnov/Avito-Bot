import asyncio
import configparser
import os.path
import pickle
import sys

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options

from models import Tasks, Items
from parser import Parser

config = configparser.RawConfigParser()
config.read('config.conf')

start_mes = """
─────────────╔╗─────     ╔╗───────╔╗─
────────────╔╝╚╗────     ║║──────╔╝╚╗
╔══╗╔╗╔╗╔══╗╚╗╔╝╔══╗     ║╚═╗╔══╗╚╗╔╝
║╔╗║║╚╝║║╔╗║─║║─║╔╗║     ║╔╗║║╔╗║─║║─
║╔╗║╚╗╔╝║╚╝║─║╚╗║╚╝║     ║╚╝║║╚╝║─║╚╗
╚╝╚╝─╚╝─╚══╝─╚═╝╚══╝     ╚══╝╚══╝─╚═╝
"""

if __name__ == "__main__":
    Tasks.delete().execute()
    if "-c" in sys.argv:
        Items.delete().execute()
        print("Данные очищенны")
        exit(0)

    for conf in config.sections():
        if conf != "SETTING":
            inf = dict(config.items(conf))
            inf["name"] = conf
            Tasks.create(**inf)

    print(start_mes)
    print(f"Парситься разделов: {Tasks.select().count()}")

    parser = Parser(None, alamer_key=config.get("SETTING", "alamer_key"))
    loop = asyncio.get_event_loop()

    if "-m" in sys.argv:
        print("Запущен в режиме мониторинга")
        for _ in range(100000):
            print("=====================")
            future = asyncio.ensure_future(parser.update_tasks(message=False))
            loop.run_until_complete(future)
        exit(0)

    if "-s" in sys.argv:
        future = asyncio.ensure_future(parser.update_tasks(save=True))
        loop.run_until_complete(future)
        print("Данные сохранены")
        exit(0)

    options = Options()
    if os.path.exists("cookies.pickle"):
        options.headless = True
    driver = webdriver.Firefox(options=options, executable_path='/usr/local/bin/geckodriver')
    driver.get("https://www.avito.ru")

    if os.path.exists("cookies.pickle"):
        with open("cookies.pickle", "rb") as f:
            cookies = pickle.load(f)
            driver.delete_all_cookies()
            for c in cookies:
                driver.add_cookie(c)
            driver.refresh()
    else:
        driver.get("https://www.avito.ru/rossiya#login")
        driver.find_element_by_name("login").send_keys(config.get("SETTING", "avito_login"))
        driver.find_element_by_name("password").send_keys(config.get("SETTING", "avito_password"), Keys.ENTER)
        input("Please, enter recaptcha and place ENTER")

        cookies = driver.get_cookies()
        with open("cookies.pickle", "wb") as f:
            pickle.dump(cookies, f)

    if "Вход и регистрация" in driver.page_source:
        os.remove("cookies.pickle")
        input("Файл cookies просрочен, перезапустите скрипт для запуска браузера и прохождения авторизации")
        exit(0)
    else:
        print("Аккаунт авторизирован")

    parser = Parser(driver, alamer_key=config.get("SETTING", "alamer_key"))
    loop = asyncio.get_event_loop()

    for _ in range(100000):
        print("=====================")
        future = asyncio.ensure_future(parser.update_tasks())
        loop.run_until_complete(future)
        parser.check_new_messanges()
    driver.quit()
