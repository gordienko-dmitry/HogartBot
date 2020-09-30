from telebot import types, TeleBot
from telebot.types import Message, CallbackQuery, InlineQuery, InlineKeyboardMarkup
import requests
import telebot
import logging

from mock_data import texts, data
from .speech import speech_to_text, SpeechException
from .botan import track as botan_track


current_articles_chats: list = []
chats_with_searching_articles: list = []


def _get_butovo_warehouse_info():
    """Getting info for butovo warehouse."""
    return texts.store_butovo


def _get_neva_warehouse_info():
    """Getting info for neva warehouse."""
    return texts.store_neva


def _get_article_text_butovo(chat_id: int) -> str:
    """Getting text for butovo warehouse."""
    return _get_article_text(chat_id, "butovo")


def _get_article_text_neva(chat_id: int) -> str:
    """Getting text for neva warehouse."""
    return _get_article_text(chat_id, "neva")


def _get_article_text(chat_id: int, quantity_text: str) -> str:
    """Getting text for current article."""
    text: str = ''
    for art in current_articles_chats:
        if art['id'] == chat_id:
            text = f"Товара с артикулом: {art['art']} ({art['name']}) на складе 'Бутово' {art[quantity_text]} шт."
            break
    return text


def _get_keyboard_company() -> InlineKeyboardMarkup:
    """Getting keyboard with button for company site."""
    keyboard = types.InlineKeyboardMarkup()
    url_button = types.InlineKeyboardButton(text='Перейти на сайт компании "Хогарт"',
                                            url="http://hogart.ru/")
    keyboard.add(url_button)
    return keyboard


def _get_keyboard_warehouses() -> InlineKeyboardMarkup:
    """Get warehouses buttons in keyboard."""
    keyboard = types.InlineKeyboardMarkup()
    button_butovo = types.InlineKeyboardButton(text="Бутово (Москва)",
                                               callback_data="butovo")
    button_neva = types.InlineKeyboardButton(text="Нева склад (Санкт-Петербург)",
                                             callback_data="neva")
    keyboard.add(button_butovo)
    keyboard.add(button_neva)
    return keyboard


def _start_message(bot: TeleBot, message: Message, botan_key: str) -> None:
    """Message for start command."""
    bot.send_message(message.chat.id, texts.start)
    if not botan_track(botan_key, message.chat.id, message, 'Обработка команды'):
        logging.error('botan problem')


def _show_help(bot: TeleBot, message: Message, botan_key: str) -> None:
    """Help message.
    Showing all available commands.
    """
    bot.send_message(message.chat.id, texts.help)
    if not botan_track(botan_key, message.chat.id, message, 'Обработка команды'):
        logging.error('botan problem')


def _show_company_info(bot: TeleBot, message: Message, botan_key: str) -> None:
    """Show company information."""
    keyboard: InlineKeyboardMarkup = _get_keyboard_company()
    bot.send_message(message.chat.id, texts.contact, reply_markup=keyboard)
    if not botan_track(botan_key, message.chat.id, message, 'Обработка команды'):
        logging.error('botan problem')


def _store(bot: TeleBot, message: Message, botan_key: str) -> None:
    """Inline buttons for warehouses info."""
    keyboard = _get_keyboard_warehouses()
    bot.send_message(message.chat.id, "Выберите склад:", reply_markup=keyboard)
    if not botan_track(botan_key, message.chat.id, message, 'Обработка команды'):
        logging.error('botan problem')


def _callback(bot: TeleBot, call: CallbackQuery) -> None:
    """Callbacks from inline buttons."""
    if call.message:
        callbacks_actions: dict = {
            "butovo": _get_butovo_warehouse_info,
            "neva": _get_neva_warehouse_info,
            "butovo_art": _get_article_text_butovo,
            "neva_art": _get_article_text_neva
        }

        if call.data not in callbacks_actions:
            return

        message_text: str = callbacks_actions[call.data]()
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text=message_text)


def _show_article(bot: TeleBot, message: Message, botan_key: str) -> None:
    """Entry point for article stores."""
    sent = bot.send_message(message.chat.id, "Введите артикул интересующего товара:")
    bot.register_next_step_handler(sent, _find_articles)
    for id in chats_with_searching_articles:
        if id == message.chat.id:
            return

    chats_with_searching_articles.append(message.chat.id)
    if not botan_track(botan_key, message.chat.id, message, 'Обработка команды'):
        logging.error('botan problem')


def _find_articles(bot: TeleBot, message: Message):
    """Searching for article and asking about warehouse."""
    current_articles_chats.clear()
    for acticle in data.articles:
        if acticle['art'] == message.text:
            current_articles_chats.append(
                {
                    'art': acticle['art'],
                    'name': acticle['name'],
                    'butovo': acticle['butovo'],
                    'neva': acticle['neva'],
                    'id': message.chat.id
                })

    if current_articles_chats:
        if len(current_articles_chats) > 1:
            pass

        keyboard: InlineKeyboardMarkup = _get_keyboard_warehouses()
        bot.send_message(message.chat.id, "Выберите склад:", reply_markup=keyboard)

    else:
        bot.send_message(message.chat.id, "Товар с таким артикулом не найден")

    chats_with_searching_articles.remove(message.chat.id)


def _show_inline_list(bot: TeleBot, query: InlineQuery, botan_key: str):
    """Sending inline list to user."""
    inline_query: list = [
        types.InlineQueryResultArticle(
            id='1',
            title="Информация о компании Хогарт",
            description="Информация о компании Хогарт",
            input_message_content=types.InputTextMessageContent(message_text=texts.contact)
        ),
        types.InlineQueryResultArticle(
            id='2',
            title="Адрес компании",
            description="Адрес центрального офиса в Москве",
            input_message_content=types.InputTextMessageContent(message_text=texts.where_hogart)
        ),
        types.InlineQueryResultArticle(
            id='3',
            title="Склад Бутово",
            description="Адрес склада в Бутово",
            input_message_content=types.InputTextMessageContent(message_text=texts.store_butovo)
        ),
        types.InlineQueryResultArticle(
            id='4',
            title="Склад Нева",
            description="Адрес склада в Санкт-Петербурге",
            input_message_content=types.InputTextMessageContent(message_text=texts.store_neva)
        )]

    bot.answer_inline_query(query.id, inline_query)
    if not botan_track(botan_key, query.id, None, 'Inline режим'):
        logging.error('botan problem')


def _send_answer_for_text_input(bot: TeleBot, message: Message, botan_key: str) -> None:
    """Getting answer fot text input."""
    for id in chats_with_searching_articles:
        if id == message.chat.id:
            return
    is_answer: bool = _send_text_answer(bot, message.text, message.chat.id)
    if not is_answer:
        bot.send_message(message.chat.id, 'Таки я не понял, чего Вы хотите')

    if not botan_track(botan_key, message.chat.id, message, 'Обработка текста', '' if is_answer else 'Нет ответа'):
        logging.error('botan problem')
    

def _send_text_answer(bot: TeleBot, text: str, chat_id: int) -> bool:
    """Sending answer for user message."""
    text_low: str = text.lower()
    is_answer = False
    if text_low.find('компан') > -1:
        if text_low.find('где ') > -1:
            keyboard = _get_keyboard_company()
            bot.send_message(chat_id, texts.where_hogart, reply_markup=keyboard)
            is_answer = True

        elif text_low.find('о ') > -1 or text_low.find('что ') > -1:
            keyboard = _get_keyboard_company()
            bot.send_message(chat_id, texts.contact, reply_markup=keyboard)
            is_answer = True

    elif text_low.find('склад') > -1:
        if text_low.find('бутов') > -1:
            bot.send_message(chat_id, texts.store_butovo)
            is_answer = True

        elif text_low.find('нева') > -1 or text_low.find('петербур') > -1:
            bot.send_message(chat_id, texts.store_neva)
            is_answer = True

        else:
            keyboard = _get_keyboard_warehouses()
            bot.send_message(chat_id, "Выберите склад:", reply_markup=keyboard)
            is_answer = True

    elif text_low.find('адрес') > -1:
        keyboard = _get_keyboard_company()
        bot.send_message(chat_id, texts.where_hogart, reply_markup=keyboard)
        is_answer = True

    elif text_low.find('привет') > -1 or text_low.find('здрав') > -1 or text_low.find('даров') > -1:
        bot.send_message(chat_id, texts.greeting)
        is_answer = True

    elif text_low.find('добр') > -1:
        if text_low.find('день') > -1 or text_low.find('дня') > -1 \
                or text_low.find('ноч') > -1 or text_low.find('утр') > -1:

            bot.send_message(chat_id, texts.greeting)
            is_answer = True

    return is_answer


def _send_answer_for_voice_input(bot: TeleBot, message: Message, telegram_token: str,
                                 yandex_key: str, botan_key: str) -> None:
    """Finding out answer for voice input.
    First of all - convert voice to text via yandex service,
    then searching correct answer.
    """
    file_info = bot.get_file(message.voice.file_id)
    file = requests.get('https://api.telegram.org/file/bot{0}/{1}'.format(telegram_token, file_info.file_path))

    try:
        # обращение к нашему новому модулю
        text: str = speech_to_text(file_in_bytes=file.content, key=yandex_key)
        is_answer = _send_text_answer(bot, text, message.chat.id)
        if not botan_track(botan_key, message.chat.id, message, 'Обработка голоса', text=text):
            logging.error('botan problem')
    except SpeechException:
        # Обработка случая, когда распознавание не удалось
        bot.send_message(message.chat.id,
                         'Не удалось распознать Ваш акцент')
        if not botan_track(botan_key, message.chat.id, message, 'Обработка голоса', 'Не распознано', text=""):
            logging.error('botan problem')
    else:
        if not is_answer:
            # Бизнес-логика
            bot.send_message(message.chat.id, 'Вы сказали: "{}"\nЯ не знаю, как на это реагировать :-('.format(text))
            
            if not botan_track(botan_key, message.chat.id, message, 'Обработка голоса', 'Нет ответа',  text=text):
                logging.error('botan problem')


def add_handlers_to_bot(bot: telebot.TeleBot, telegram_token: str, botan_key: str, yandex_key: str) -> None:

    @bot.message_handler(commands=['start'])
    def _start_handler(message: Message):
        _start_message(bot, message, botan_key)

    @bot.message_handler(commands=['help'])
    def _help_handler(message):
        _show_help(bot, message, botan_key)

    @bot.message_handler(commands=['hogart'])
    def _company_handler(message):
        _show_company_info(bot, message, botan_key)

    @bot.message_handler(commands=['store'])
    def _store_handler(message):
        _store(bot, message, botan_key)

    @bot.callback_query_handler(func=lambda call: True)
    def _callback_handler(call: CallbackQuery):
        _callback(bot, call)

    @bot.message_handler(commands=['art'])
    def _article_handler(message: Message):
        _show_article(bot, message, botan_key)

    @bot.inline_handler(lambda query: len(query.query) == 0)
    def _query_handler(query):
        _show_inline_list(bot, query, botan_key)

    @bot.message_handler(content_types=["text"])
    def _text_handler(message):
        _send_answer_for_text_input(bot, message, botan_key)

    @bot.message_handler(content_types=['voice'])
    def _voice_handler(message):
        _send_answer_for_voice_input(bot, message, telegram_token, yandex_key, botan_key)
