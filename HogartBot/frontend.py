import telebot
from telebot import types
import texts as t
from example_data import articles as arts
from config import TOKEN
import requests
from yandex_speech import speech_to_text
from yandex_speech import SpeechException

bot = telebot.TeleBot(TOKEN)
m_art = []
special_things = []


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, t.start)


@bot.message_handler(commands=['help'])
def show_help(message):
    bot.send_message(message.chat.id, t.help)


@bot.message_handler(commands=['hogart'])
def hogart(message):
    keyboard = types.InlineKeyboardMarkup()
    url_button = types.InlineKeyboardButton(text='Перейти на сайт компании "Хогарт"', url="http://hogart.ru/")
    keyboard.add(url_button)
    bot.send_message(message.chat.id, t.contact, reply_markup=keyboard)


@bot.message_handler(commands=['store'])
def store(message):
    keyboard = types.InlineKeyboardMarkup()
    button_butovo = types.InlineKeyboardButton(text="Бутово (Москва)", callback_data="butovo")
    button_neva = types.InlineKeyboardButton(text="Нева склад (Санкт-Петербург)", callback_data="neva")
    keyboard.add(button_butovo)
    keyboard.add(button_neva)
    bot.send_message(message.chat.id, "Выберите склад:", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.message:
        if call.data == "butovo":
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=t.store_butovo)
        elif call.data == "neva":
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=t.store_neva)
        elif call.data == "butovo_art":
            for art in m_art:
                if art['id'] == call.message.chat.id:
                    text = "Товара с артикулом: {art} ({name}) на складе 'Бутово' {kolvo} шт.".format(art=art['art'],
                                                                                                      name=art['name'],
                                                                                                      kolvo=art['butovo'])
                    break
            bot.edit_message_text(chat_id=call.message.chat.id,  message_id=call.message.message_id, text=text)
        elif call.data == "neva_art":
            for art in m_art:
                if art['id'] == call.message.chat.id:
                    text = "Товара с артикулом: {art} ({name}) на складе 'Нева' {kolvo} шт.".format(art=art['art'],
                                                                                                      name=art['name'],
                                                                                                      kolvo=art['neva'])
                    break
            bot.edit_message_text(chat_id=call.message.chat.id,  message_id=call.message.message_id, text=text)


@bot.message_handler(commands=['art'])
def show_art(message):
    sent = bot.send_message(message.chat.id, "Введите артикул интересующего товара:")
    bot.register_next_step_handler(sent, articles)
    for id in special_things:
        if id == message.chat.id:
            return
    special_things.append(message.chat.id)


def articles(message):
    m_art.clear()
    for art in arts:
        if art['art'] == message.text:
            m_art.append({'art': art['art'], 'name': art['name'], 'butovo': art['butovo'], 'neva': art['neva'],
                          'id': message.chat.id})

    if m_art:
        if len(m_art) > 1:
            pass

        keyboard = types.InlineKeyboardMarkup()
        button_butovo = types.InlineKeyboardButton(text="Бутово (Москва)", callback_data="butovo_art")
        button_neva = types.InlineKeyboardButton(text="Нева склад (Санкт-Петербург)", callback_data="neva_art")
        keyboard.add(button_butovo)
        keyboard.add(button_neva)
        bot.send_message(message.chat.id, "Выберите склад:", reply_markup=keyboard)

    else:
        bot.send_message(message.chat.id, "Товар с таким артикулом не найден")

    special_things.remove(message.chat.id)


@bot.inline_handler(lambda query: len(query.query) > 0)
def query_text(query):
    if query.query == "contact":
        t_contact = types.InlineQueryResultArticle(
            id='1', title="Информация о компании Хогарт",
            # Описание отображается в подсказке,
            # message_text - то, что будет отправлено в виде сообщения
            description="Информация о компании Хогарт",
            input_message_content=types.InputTextMessageContent(
                message_text=t.contact)
        )
        bot.answer_inline_query(query.id, [t_contact])


@bot.message_handler(content_types=["text"])
def hello(message):
    for id in special_things:
        if id == message.chat.id:
            return
    gogo = answer_text(message.text, message.chat.id)
    if not(gogo):
        bot.send_message(message.chat.id,
                     'Таки я не понял, чего Вы хотите')


def answer_text(text,chat_id):
    text_low = text.lower()
    gogo = False
    if text_low.find('компан') > -1:
        if text_low.find('где ') > -1:
            keyboard = types.InlineKeyboardMarkup()
            url_button = types.InlineKeyboardButton(text='Перейти на сайт компании "Хогарт"',
                                                    url="http://hogart.ru/")
            keyboard.add(url_button)
            bot.send_message(chat_id, t.where_hogart, reply_markup=keyboard)
            gogo = True
        elif text_low.find('о ') > -1 or text_low.find('что ') > -1:
            keyboard = types.InlineKeyboardMarkup()
            url_button = types.InlineKeyboardButton(text='Перейти на сайт компании "Хогарт"',
                                                    url="http://hogart.ru/")
            keyboard.add(url_button)
            bot.send_message(chat_id, t.contact, reply_markup=keyboard)
            gogo = True
    elif text_low.find('склад') > -1:
        if text_low.find('бутов') > -1:
            bot.send_message(chat_id, t.store_butovo)
            gogo = True
        elif text_low.find('нева') > -1 or text_low.find('петербур') > -1:
            bot.send_message(chat_id, t.store_neva)
            gogo = True
        else:
            keyboard = types.InlineKeyboardMarkup()
            button_butovo = types.InlineKeyboardButton(text="Бутово (Москва)", callback_data="butovo")
            button_neva = types.InlineKeyboardButton(text="Нева склад (Санкт-Петербург)", callback_data="neva")
            keyboard.add(button_butovo)
            keyboard.add(button_neva)
            bot.send_message(chat_id, "Выберите склад:", reply_markup=keyboard)
            gogo = True
    elif text_low.find('адрес') > -1:
        keyboard = types.InlineKeyboardMarkup()
        url_button = types.InlineKeyboardButton(text='Перейти на сайт компании "Хогарт"',
                                                url="http://hogart.ru/")
        keyboard.add(url_button)
        bot.send_message(chat_id, t.where_hogart, reply_markup=keyboard)
        gogo = True
    elif text_low.find('привет') > -1 or text_low.find('здрав') > -1 or text_low.find('даров') > -1:
        bot.send_message(chat_id, t.greeting)
        gogo = True
    elif text_low.find('добр') > -1:
        if text_low.find('день') > -1 or text_low.find('дня') > -1 \
                or text_low.find('ноч') > -1 or text_low.find('утр') > -1:
            bot.send_message(chat_id, t.greeting)
            gogo = True
    return gogo


@bot.message_handler(content_types=['voice'])
def voice_processing(message):
    file_info = bot.get_file(message.voice.file_id)
    file = requests.get('https://api.telegram.org/file/bot{0}/{1}'.format(TOKEN, file_info.file_path))

    try:
        # обращение к нашему новому модулю
        text = speech_to_text(bytes=file.content)
        gogo = answer_text(text, message.chat.id)
    except SpeechException:
        # Обработка случая, когда распознавание не удалось
        bot.send_message(message.chat.id,
                         'Не удалось распознать Ваш акцент')
    else:
        if not(gogo):
            # Бизнес-логика
            bot.send_message(message.chat.id, 'Вы сказали: "{}"\nЯ не знаю, как на это реагировать :-('.format(text))


if __name__ == '__main__':
    bot.polling()