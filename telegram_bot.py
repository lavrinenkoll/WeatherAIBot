import requests
import telebot
from PIL import Image
from telebot import types

from outputs_bot.dalle import create_image
from tools.parsing import parse_all
from outputs_bot.diagram import build_diagram, get_time_now, get_temperature_and_rain_probability
from tools.get_urls import create_urls_requests, create_urls_selenium
from io import BytesIO
from tools.firebase_actions import *  #tools.database_actions  tools.firebase_actions

with open('private/bot_token', 'r') as f:
    token = f.read()

bot = telebot.TeleBot(token)
user_id = 0

#------------------GLOBAL---------------------#
#----------------------------------------------
driver_type_weather = 'requests'    #selenium: 'local', 'remote' | 'requests' быстрее | type of parsing weather
driver_type_img = 'remote'          #'local'(на repl.it банят за прокси) 'remote' | type of img generation

if driver_type_img == 'local':
    proxy_needed = 1
else:
    proxy_needed = 0
#----------------------------------------------
markup_menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
row1 = ["Налаштування"]
row2 = ["Яка зараз погода?", "Картинки як вдягнутись зараз"]
markup_menu.row(*row2)
markup_menu.row(*row1)
#----------------------------------------------

@bot.message_handler(commands=['start'])
def start_message(message):
    global user_id
    user_id = message.from_user.id
    data_user = get_data(user_id)
    markup_remove = types.ReplyKeyboardRemove(selective=False)
    # проверка на наличие пользователя в базе
    if data_user == []:
        markup = types.InlineKeyboardMarkup()
        row1 = [types.InlineKeyboardButton("Надіслати геопозицію", callback_data='location'),
                types.InlineKeyboardButton("Ввести назву міста", callback_data='city')]
        row2 = [types.InlineKeyboardButton("Вказати стать", callback_data='sex')]
        markup.row(*row1)
        markup.row(*row2)

        bot.send_message(message.chat.id, f'*Привіт, {message.from_user.first_name}, я бот-погода*, який допоможе '
                                          f'тобі обрати одяг на сьогоднішній день.',
                         parse_mode="Markdown", reply_markup=markup_remove)
        bot.send_message(message.chat.id, 'Для початку надішли мені свою геолокацію, '
                                          'або введи назву свого помешкання; та вкажи свою стать.',
                         parse_mode="Markdown", reply_markup=markup)
        db_table_val(user_id, '', -1, '')
    elif (data_user != [] and data_user[0][2] == '' or data_user[0][3] == -1):
        markup = types.InlineKeyboardMarkup()
        row1 = [types.InlineKeyboardButton("Надіслати геопозицію", callback_data='location'),
                types.InlineKeyboardButton("Ввести назву міста", callback_data='city')]
        row2 = [types.InlineKeyboardButton("Вказати стать", callback_data='sex')]
        markup.row(*row1)
        markup.row(*row2)

        dont_have = 'У базі: '
        if data_user[0][2] == '':
            dont_have += 'немає геолокації'
            if data_user[0][3] == -1:
                dont_have += ', немає статі.'
            else:
                dont_have += '.'
        elif data_user[0][3] == -1:
            dont_have += 'немає статі.'


        bot.send_message(message.chat.id, f'З поверненням, {message.from_user.first_name}!', reply_markup=markup_remove)
        bot.send_message(message.chat.id, 'Схоже, ти ввів не все данні. '+dont_have+'\n'
                                          'Надішли мені свою геолокацію, або введи назву свого помешкання; та вкажи свою стать.',
                         parse_mode="Markdown", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, f'З поверненням, {message.from_user.first_name}!', reply_markup=markup_menu)
        # ????


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    try:
        if call.message:
            if call.data == 'location':
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                item1 = types.KeyboardButton("Надіслати геопозицію", request_location=True)
                item2 = types.KeyboardButton("Скасувати")
                markup.add(item1, item2)

                bot.send_message(call.message.chat.id, 'Надішли свою геолокацію:', reply_markup=markup)
                bot.register_next_step_handler(call.message, get_location)
            elif call.data == 'city':
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                item2 = types.KeyboardButton("Скасувати")
                markup.add(item2)

                bot.send_message(call.message.chat.id, 'Введи назву міста:', reply_markup=markup)
                bot.register_next_step_handler(call.message, get_city)
            elif call.data == 'sex':
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                row1 = [types.InlineKeyboardButton("Чоловік"),
                        types.InlineKeyboardButton("Жінка")]
                row2 = [types.KeyboardButton("Скасувати")]
                markup.row(*row1)
                markup.row(*row2)

                bot.send_message(call.message.chat.id, 'Обери стать:', reply_markup=markup)
                bot.register_next_step_handler(call.message, get_sex)
            elif call.data == 'menu':
                bot.send_message(call.message.chat.id, 'Ви у головному меню.',
                                 reply_markup=markup_menu)

    except Exception as e:
        print(repr(e))


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.text == "Налаштування":
        user_data = get_data(message.from_user.id)
        markup = types.InlineKeyboardMarkup()
        row1 = [types.InlineKeyboardButton("Надіслати геопозицію", callback_data='location'),
                types.InlineKeyboardButton("Ввести назву міста", callback_data='city')]
        row2 = [types.InlineKeyboardButton("Вказати стать", callback_data='sex')]
        row3 = [types.InlineKeyboardButton("Назад", callback_data='menu')]
        markup.row(*row1)
        markup.row(*row2)
        markup.row(*row3)
        bot.send_message(message.chat.id, f'Поточні дані:\n'
                                          f'Обрана локація: {user_data[0][2] if len(user_data[0][2]) != 0 else "не обрано"}\n'
                                          f'Обрана стать: {"Чоловік" if user_data[0][3] == 0 else ("Жінка" if user_data[0][3] == 1 else "не обрано")}\n\n'
                                          f'Обери пункт налаштувань, який тебе цікавить:', reply_markup=markup)
    elif message.text == "У головне меню":
        bot.send_message(message.chat.id, 'Ви у головному меню.',
                         reply_markup=markup_menu)
    elif message.text == "Яка зараз погода?":
        get_weather(message, markup_menu)
    elif message.text == "Картинки як вдягнутись зараз":
        get_image(message, markup_menu)


def get_city_by_loc(latitude, longitude):
    url = 'https://nominatim.openstreetmap.org/reverse?format=json&lat={}&lon={}&zoom=18&addressdetails=1'.format(
        latitude, longitude)
    response = requests.get(url)
    data = response.json()
    city = data['address']['city']
    state = data['address']['state']
    country = data['address']['country']
    return f"{city}, {state}, {country}"


def get_city_by_name(city):
    # найти город в базе по названию
    url = 'https://nominatim.openstreetmap.org/search?q={}&format=json&addressdetails=1&limit=1'.format(city)
    response = requests.get(url)
    data = response.json()
    if data == []:
        return None

    try:
        city = data[0]['address']['city']
    except:
        city = None
    if city == None:
        city = data[0]['address']['town']

    try:
        state = data[0]['address']['state']
    except:
        state = None
    country = data[0]['address']['country']
    if state == None:
        return f"{city}, {country}"
    return f"{city}, {state}, {country}"


def get_location(message):
    global user_id
    user_id = message.from_user.id
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    row1 = ["У головне меню"]
    markup.row(*row1)
    if message.text == 'Скасувати':
        bot.send_message(message.chat.id, 'Дія скасована.', reply_markup=markup)
        return
    try:
        latitude = message.location.latitude
        longitude = message.location.longitude
        city = get_city_by_loc(latitude, longitude)
        bot.send_message(message.chat.id, 'Дякую за інформацію!\nВведене місто: ' + city, reply_markup=markup)
        update_data(user_id, city, None, None)
    except Exception as e:
        bot.send_message(message.chat.id, 'Виникла помилка, натисни та спробуй ще раз.', reply_markup=markup)
        print(repr(e))


def get_city(message):
    global user_id
    user_id = message.from_user.id
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    row1 = ["У головне меню"]
    markup.row(*row1)
    try:
        city = message.text
        if city == 'Скасувати':
            bot.send_message(message.chat.id, 'Дія скасована.', reply_markup=markup)
            return
        city = get_city_by_name(city)
        if city == None:
            bot.send_message(message.chat.id, 'Виникла помилка, спробуй ще раз.\n'
                                              'Перевір правильність введення назви, натисни та спробуй знову.',
                             reply_markup=markup)
        else:
            bot.send_message(message.chat.id, f'Дякую за інформацію!\nВведене місто: {city}\n'
                                              f'Якщо воно не вірне, натисни та спробуй ще раз, уточнивши, '
                                              f'наприклад, область.',
                             reply_markup=markup)
            update_data(user_id, city, None, None)
    except Exception as e:
        bot.send_message(message.chat.id, 'Виникла помилка, натисни та спробуй ще раз.', reply_markup=markup)
        print(repr(e))


def get_sex(message):
    global user_id
    user_id = message.from_user.id
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    row1 = ["У головне меню"]
    markup.row(*row1)
    if message.text == 'Скасувати':
        bot.send_message(message.chat.id, 'Дія скасована.', reply_markup=markup)
        return
    elif message.text == "Чоловік":
        bot.send_message(message.chat.id, 'Дякую за інформацію!', reply_markup=markup)
        bot.delete_message(message.chat.id, message_id=message.message_id - 1)
        update_data(user_id, None, 0, None)
    elif message.text == "Жінка":
        bot.send_message(message.chat.id, 'Дякую за інформацію!', reply_markup=markup)
        bot.delete_message(message.chat.id, message_id=message.message_id - 1)
        update_data(user_id, None, 1, None)
    else:
        bot.send_message(message.chat.id, 'Виникла помилка, натисни та спробуй ще раз.', reply_markup=markup)


lock = 0


def get_weather(message, markup):
    global user_id
    global lock
    if lock == 1:
        return
    lock = 1
    user_id = message.from_user.id
    user_data = get_data(user_id)

    if user_data[0][2] == '':
        bot.send_message(message.chat.id, 'Спочатку введи місто, в якому ти знаходишся у налаштуваннях.',
                         reply_markup=markup)
        lock = 0
        return

    if user_data[0][2].split(', ')[-1] == "Россия":
        bot.send_message(message.chat.id, 'Нема інформації, наразі бот працює тільки з розвиненими країнами',
                         reply_markup=markup)
        lock = 0
        return

    bot.send_message(message.chat.id, 'Зачекай, я шукаю погоду...', reply_markup=types.ReplyKeyboardRemove())
    try:
        if driver_type_weather == 'requests':
            url_gismeteo, url_sinoptik, url_meta = create_urls_requests(user_data[0][2])
        else:
            url_gismeteo, url_sinoptik, url_meta = create_urls_selenium(user_data[0][2], driver_type_weather)
    except Exception as e:
        bot.send_message(message.chat.id, 'Виникла помилка, спробуй ще раз.\nАбо перевір правильність налаштувань.',
                         reply_markup=markup)
        lock = 0
        print(repr(e))
        return
    try:
        weather = parse_all(url_gismeteo, url_sinoptik, url_meta)
        time_now, time_str = get_time_now(user_data[0][2])
        hours = list(weather.keys())
        temperature = [hour_data[0] for hour_data in weather.values()]
        rain = [hour_data[1] for hour_data in weather.values()]
    except Exception as e:
        bot.send_message(message.chat.id, 'Виникла помилка, спробуй ще раз.\nАбо перевір правильність налаштувань.',
                         reply_markup=markup)
        lock = 0
        print(repr(e))
        return

    bot.send_message(message.chat.id, 'Будую гарненький графік...')
    try:
        img, text = build_diagram(hours, temperature, rain, time_now, time_str, user_data[0][2])
        bio = BytesIO()
        img.save(bio, format='PNG')
        bio.seek(0)
    except Exception as e:
        bot.send_message(message.chat.id, 'Виникла помилка, спробуй ще раз.\nАбо перевір правильність налаштувань.',
                         reply_markup=markup)
        lock = 0
        print(repr(e))
        return
    bot.send_photo(message.chat.id, photo=bio, caption=text, reply_markup=markup)
    bot.delete_message(message.chat.id, message_id=message.message_id + 1)
    bot.delete_message(message.chat.id, message_id=message.message_id + 2)
    img.close()
    lock = 0


lock2 = 0


def get_image(message, markup):
    global user_id
    user_id = message.from_user.id

    global lock2
    if lock2 == 1:
        return
    lock2 = 1

    user_data = get_data(user_id)
    if user_data[0][2] == '' or user_data[0][3] == -1:
        bot.send_message(message.chat.id, 'Спочатку введи усі дані у налаштуваннях.',
                         reply_markup=markup)
        lock2 = 0
        return

    bot.send_message(message.chat.id, 'Зачекай, створюю зображення...', reply_markup=types.ReplyKeyboardRemove())
    try:
        if driver_type_weather == 'requests':
            url_gismeteo, url_sinoptik, url_meta = create_urls_requests(user_data[0][2])
        else:
            url_gismeteo, url_sinoptik, url_meta = create_urls_selenium(user_data[0][2], driver_type_weather)
    except Exception as e:
        bot.send_message(message.chat.id, 'Виникла помилка, спробуй ще раз.\nАбо перевір правильність налаштувань.',
                         reply_markup=markup)
        lock2 = 0
        print(repr(e))
        return
    try:
        weather = parse_all(url_gismeteo, url_sinoptik, url_meta)
        time_now, time_str = get_time_now(user_data[0][2])
        hours = list(weather.keys())
        temperature = [hour_data[0] for hour_data in weather.values()]
        rain = [hour_data[1] for hour_data in weather.values()]
    except Exception as e:
        bot.send_message(message.chat.id, 'Виникла помилка, спробуй ще раз.\nАбо перевір правильність налаштувань.',
                         reply_markup=markup)
        lock2 = 0
        print(repr(e))
        return

    temperature_now, rain_now = get_temperature_and_rain_probability(temperature, rain, time_now)

    try:
        img = create_image(temperature_now, rain_now, user_data[0][3], driver_type_img, proxy_needed)
    except Exception as e:
        bot.send_message(message.chat.id, 'Виникла помилка, спробуй ще раз.', reply_markup=markup)
        lock2 = 0
        print(repr(e))
        return

    try:
        img = Image.open(BytesIO(img))
        bio = BytesIO()
        img.save(bio, format='PNG')
        bio.seek(0)
        text = f'Ось що згенерувала нейронна мережа на поточні покази.\n' \
               f'Температура: {temperature_now}°C\nЙмовірність дощу: {rain_now}%\n\n' \
               f'*Увага! Це лише приблизна візуалізація як можна вдягнутися.*' \
               f'Все залежить від того, як себе відчуваєш.\n' \
               f'Згенеровано за допомогою DeepAI'
        bot.send_photo(message.chat.id, photo=bio, reply_markup=markup, caption=text, parse_mode='Markdown')
        bot.delete_message(message.chat.id, message_id=message.message_id + 1)
        img.close()
    except Exception as e:
        bot.send_message(message.chat.id, 'Виникла помилка, спробуй ще раз.', reply_markup=markup)
        lock2 = 0
        print(repr(e))
        return
    lock2 = 0


bot.polling(none_stop=True, interval=0)
