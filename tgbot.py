import telebot
from telebot import types

from config import telegram_key
from models import Items, Authors, Users

bot = telebot.TeleBot(telegram_key)

parsels_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
parsels_keyboard.row(types.KeyboardButton(text="Купленные📦"),
                     types.KeyboardButton(text="Жду ответа😴"))


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Пришлите пароль для активации бота")


@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.from_user:
        cal = str(call.data)
        type = cal.split("_")[0]
        data = cal.split("_")[1]
        if type == "show-full":
            item = Items.get(Items.item_id == data)
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(types.InlineKeyboardButton(text="Описание on/off",
                                                  callback_data=f"show-full_{data}"),
                       types.InlineKeyboardButton(text="Avito",
                                                  url=item.url),
                       types.InlineKeyboardButton(text="Отписал 🖌", callback_data=f"writen_{data}"),
                       types.InlineKeyboardButton(text="Купил 📦", callback_data=f"buy_{data}"),
                       types.InlineKeyboardButton(text="🚫 продовца",
                                                  callback_data=f"ban_{data}"),
                       types.InlineKeyboardButton(text="🗑 сообщение", callback_data=f"drop_{data}"),
                       )

            if "Описание:" in call.message.caption:
                bot.edit_message_caption(chat_id=call.message.chat.id,
                                         message_id=call.message.message_id,
                                         caption=call.message.caption[:call.message.caption.find("Описание:")],
                                         reply_markup=markup)
            else:
                bot.edit_message_caption(chat_id=call.message.chat.id,
                                         message_id=call.message.message_id,
                                         caption=call.message.caption + "\nОписание:" + item.discr,
                                         reply_markup=markup)
        elif type == "drop":
            bot.delete_message(chat_id=call.message.chat.id,
                               message_id=call.message.message_id)
            Items.update({Items.status: -1}).where(Items.item_id == data).execute()

        elif type == "buy":
            Items.update({Items.status: 2}).where(Items.item_id == data).execute()
            bot.answer_callback_query(call.id, text="Товар добвлен в Купленные📦")
            return

        elif type == "writen":
            Items.update({Items.status: 1}).where(Items.item_id == data).execute()
            bot.answer_callback_query(call.id, text="Товар добвлен в список ожидания")
            return

        elif type == "skam":
            Items.update({Items.status: -2}).where(Items.item_id == data).execute()
            bot.answer_callback_query(call.id, text="Товар подтвержден как мошеннический")
            bot.delete_message(chat_id=call.message.chat.id,
                               message_id=call.message.message_id)
            return

        elif type == "ban":
            author_id = Items.get(Items.item_id == data).author_id
            Authors.update({Authors.status: 0}).where(Authors.author_id == author_id).execute()
            bot.answer_callback_query(call.id, text="Продавец заблокирован")
            return

        bot.answer_callback_query(call.id, text="")


@bot.message_handler(content_types=["text"])
def repeat_all_messages(message):
    if message.text == "avbot2020":
        if Users.get_or_none(Users.tel_id == message.chat.id) is None:
            Users.create(tel_id=message.chat.id,
                         name=str(message.from_user.first_name) + " " + str(message.from_user.last_name))
            bot.send_message(message.chat.id, "Бот активирован", reply_markup=parsels_keyboard)

    elif message.text in ["Жду ответа😴", "Купленные📦"]:
        if message.text == "Жду ответа😴":
            items = Items.select().where(Items.status == 1).execute()
        else:
            items = Items.select().where(Items.status == 2).execute()

        markup = types.InlineKeyboardMarkup(row_width=1)
        for i in items:
            markup.add(types.InlineKeyboardButton(text=i.name,
                                                  url=i.url))
        if len(items) == 0:
            bot.send_message(message.chat.id, "Список товаров пуст")
        else:
            bot.send_message(message.chat.id, "Список товаров:",
                             reply_markup=markup)


# bot.polling(none_stop=True, timeout=60)
users = Users.select().where(Users.status > 0).execute()
for u in users:
    bot.send_message(u.tel_id, "Вышло обновление. Баг фикс + коррекция алгоритма детекта спама",
                     reply_markup=parsels_keyboard)
exit(0)


while True:
    try:
        bot.polling(none_stop=True, timeout=60)
    except Exception as e:
        print(e)
