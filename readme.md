# Avito Bot

A python script which checks every few seconds the specified sections of the site for new items. If found, it sends a message to the seller. If the message can not be sent, it sends a message to telegram through the alarmer bot. After each update, the bot checks for replies to all the messages sent earlier and if found, sends notifications via the alarmer bot.

### Setting up

1. Download firefix
2. Download Linux
Setup config.conf file
    1. Each block has 7 parameters, all names must be unique
    2. `url` - link to search section
    3. The `max_cost` - the maximum price of the product at which the notification will be sent
    4. Min_cost` - the minimum product price at which the notice will be sent
    5. Measures_cost` - the amount to which to write to the seller with a request to lower the price
    6. Model` - the model of the phone
    7. `params` - phone settings
    8. Message_text` - The text of the message that the bot writes
     The seller if the price is more than `max_cost` and less than `mes_cost`. 
4. Configure the bot in the file config.conf under SETTING:
    1. Avito_password` - the password from the account at avito
    2. `avito_login` - login from the account in avito
    3. `alamer_key2 ` - key to send a notification to the telegram bot, you can get here t.me/alarmer_bot: 
5. Run `./bot -c` to clear the cache
6. Run `./bot -s` to save the pulling items not to spam notifications at startup and not to catch the fraud
7. Run `./bot -m ` to run in monitoring mode (eg on the server), without authorization and sending messages (does not require a browser).
8. Run `./bot` to run in normal mode, requires a browser and **geckodriver** in the path to `/usr/local/bin/geckodriver`.

### Features

+ Support of authorization at the site via cookie swapping
+ Asynchronous parsing of product sections
+ Captcha display in case of need to bypass it
+ Local BD which saves the parser state at restart
+ Easy configuration through config.conf file
+ Using Alamer Bot in telegram to send notifications
+ Using selenium drivers to control your browser to bypass avito ford and messaging
+ Project built with Docker

### Technology

* Selenium
* BeautifulSoup
* Aiohttp and asyncio
* SQL Lite 
* Docker 
* Peewee ORM

#### halal architecture

dist/bot - bot built
bot/bot - bot code
bot/parser - a class for encapsulating all the functions of the bot
bot/model - classes of models for working with DB
