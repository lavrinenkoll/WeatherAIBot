import requests
import telebot
from PIL import Image
from telebot import types
from io import BytesIO

from outputs_bot.dalle import create_image
from tools.parsing import parse_all
from outputs_bot.diagram import build_diagram, get_time_now, get_temperature_and_rain_probability
from tools.get_urls import create_urls_requests, create_urls_selenium
from tools.firebase_actions import *  #tools.database_actions (для локального) tools.firebase_actions (для облачного)

# отримання токену бота з файлу
with open('private/bot_token', 'r') as f:
    token = f.read()

# створення бота
bot = telebot.TeleBot(token)
user_id = 0 # id користувача

#глобальні змінні для вибору роботи бота
#------------------GLOBAL---------------------#
#----------------------------------------------
driver_type_weather = 'requests'    #selenium: 'local', 'remote' | 'requests' быстрее | type of parsing weather
driver_type_img = 'remote'          #'local'(на repl.it банят за прокси) 'remote' | type of img generation

if driver_type_img == 'local':
    proxy_needed = 1
else:
    proxy_needed = 0

#головне меню
#----------------------------------------------
markup_menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
row1 = ["Налаштування"]
row2 = ["Яка зараз погода?", "Картинки як вдягнутись зараз"]
markup_menu.row(*row2)
markup_menu.row(*row1)
#----------------------------------------------


#обробка команди /start
@bot.message_handler(commands=['start'])
def start_message(message):
    global user_id
    user_id = message.from_user.id #отримання id користувача
    data_user = get_data(user_id) #отримання даних користувача з бази
    markup_remove = types.ReplyKeyboardRemove(selective=False) #розмітка без кнопок

    # перевірка чи є користувач в базі
    if data_user == []: #якщо немає
        markup = types.InlineKeyboardMarkup()
        row1 = [types.InlineKeyboardButton("Надіслати геопозицію", callback_data='location'),
                types.InlineKeyboardButton("Ввести назву міста", callback_data='city')]
        row2 = [types.InlineKeyboardButton("Вказати стать", callback_data='sex')]
        markup.row(*row1)
        markup.row(*row2)
        #відправка повідомлення з розміткою
        bot.send_message(message.chat.id, f'*Привіт, {message.from_user.first_name}, я бот-погода*, який допоможе '
                                          f'тобі обрати одяг на сьогоднішній день.',
                         parse_mode="Markdown", reply_markup=markup_remove)
        bot.send_message(message.chat.id, 'Для початку надішли мені свою геолокацію, '
                                          'або введи назву свого помешкання; та вкажи свою стать.',
                         parse_mode="Markdown", reply_markup=markup)
        #додавання користувача в базу
        db_table_val(user_id, '', -1, '')

    elif data_user != [] and data_user[0][2] == '' or data_user[0][3] == -1: #якщо є, але не вказано місто або стать
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

        #відправка повідомлення з розміткою + інформація про те, що не вказано
        bot.send_message(message.chat.id, f'З поверненням, {message.from_user.first_name}!', reply_markup=markup_remove)
        bot.send_message(message.chat.id, 'Схоже, ти ввів не все данні. '+dont_have+'\n'
                                          'Надішли мені свою геолокацію, або введи назву свого помешкання; та вкажи свою стать.',
                         parse_mode="Markdown", reply_markup=markup)
    else:
        #відправка повідомлення з розміткою
        bot.send_message(message.chat.id, f'З поверненням, {message.from_user.first_name}!', reply_markup=markup_menu)


#функція, яка відповідає за обробку запитів з кнопок
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    try:
        if call.message:
            #якщо натиснуто кнопку "Надіслати геопозицію"
            if call.data == 'location':
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                item1 = types.KeyboardButton("Надіслати геопозицію", request_location=True)
                item2 = types.KeyboardButton("Скасувати")
                markup.add(item1, item2)

                bot.send_message(call.message.chat.id, 'Надішли свою геолокацію:', reply_markup=markup)
                bot.register_next_step_handler(call.message, get_location)

            #якщо натиснуто кнопку "Ввести назву міста"
            elif call.data == 'city':
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                item2 = types.KeyboardButton("Скасувати")
                markup.add(item2)

                bot.send_message(call.message.chat.id, 'Введи назву міста:', reply_markup=markup)
                bot.register_next_step_handler(call.message, get_city)

            #якщо натиснуто кнопку "Вказати стать"
            elif call.data == 'sex':
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                row1 = [types.InlineKeyboardButton("Чоловік"),
                        types.InlineKeyboardButton("Жінка")]
                row2 = [types.KeyboardButton("Скасувати")]
                markup.row(*row1)
                markup.row(*row2)

                bot.send_message(call.message.chat.id, 'Обери стать:', reply_markup=markup)
                bot.register_next_step_handler(call.message, get_sex)

            #якщо натиснуто кнопку "Скасувати"
            elif call.data == 'menu':
                bot.send_message(call.message.chat.id, 'Ви у головному меню.',
                                 reply_markup=markup_menu)

    except Exception as e:
        print(repr(e))


#обробка текстових повідомлень
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    #якщо натиснуто кнопку "Налаштування"
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

    #якщо натиснуто кнопку "У головне меню"
    elif message.text == "У головне меню":
        bot.send_message(message.chat.id, 'Ви у головному меню.',
                         reply_markup=markup_menu)

    #якщо натиснуто кнопку "Яка зараз погода?"
    elif message.text == "Яка зараз погода?":
        get_weather(message, markup_menu)

    #якщо натиснуто кнопку "Картинки як вдягнутись зараз"
    elif message.text == "Картинки як вдягнутись зараз":
        get_image(message, markup_menu)


#функція для отримання назви міста за геолокацією
def get_city_by_loc(latitude, longitude):
    url = 'https://nominatim.openstreetmap.org/reverse?format=json&lat={}&lon={}&zoom=18&addressdetails=1'.format(
        latitude, longitude)
    response = requests.get(url)
    data = response.json()
    city = data['address']['city']
    state = data['address']['state']
    country = data['address']['country']
    return f"{city}, {state}, {country}"


#функція для отримання точної назви міста за вказаною назвою
def get_city_by_name(city):
    # шукати місто в базі даних
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


#обробка виклику функції для отримання міста за геолокацією
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
        update_data(user_id, city, None, None) # оновлення даних користувача в базі даних
    except Exception as e:
        bot.send_message(message.chat.id, 'Виникла помилка, натисни та спробуй ще раз.', reply_markup=markup)
        print(repr(e))


#обробка виклику функції для отримання міста за назвою
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
            update_data(user_id, city, None, None) # оновлення даних користувача
    except Exception as e:
        bot.send_message(message.chat.id, 'Виникла помилка, натисни та спробуй ще раз.', reply_markup=markup)
        print(repr(e))


#обробка виклику функції для отримання статі
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
        update_data(user_id, None, 0, None) # поновити дані в БД
    elif message.text == "Жінка":
        bot.send_message(message.chat.id, 'Дякую за інформацію!', reply_markup=markup)
        bot.delete_message(message.chat.id, message_id=message.message_id - 1)
        update_data(user_id, None, 1, None) # поновити дані в БД
    else:
        bot.send_message(message.chat.id, 'Виникла помилка, натисни та спробуй ще раз.', reply_markup=markup)


#змінна для блокування виклику функції щоб не викликати її декілька разів
lock = 0


#обробка виклику функції для отримання погоди
def get_weather(message, markup):
    global user_id
    global lock
    # блокування виклику функції
    if lock == 1:
        return
    lock = 1
    user_id = message.from_user.id
    user_data = get_data(user_id) # отримання даних користувача

    # перевірка на наявність даних користувача
    if user_data[0][2] == '':
        bot.send_message(message.chat.id, 'Спочатку введи місто, в якому ти знаходишся у налаштуваннях.',
                         reply_markup=markup)
        lock = 0
        return

    # перевірка на наявність даних користувача
    if user_data[0][2].split(', ')[-1] == "Россия":
        bot.send_message(message.chat.id, 'Нема інформації, наразі бот працює тільки з розвиненими країнами',
                         reply_markup=markup)
        lock = 0
        return

    bot.send_message(message.chat.id, 'Зачекай, я шукаю погоду...', reply_markup=types.ReplyKeyboardRemove())
    try:
        # отримання посилань на погоду в залежності від обраного типу
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
        # парсинг отриманих посилань
        weather = parse_all(url_gismeteo, url_sinoptik, url_meta)
        # отримання часу зараз для вказаного міста
        time_now, time_str = get_time_now(user_data[0][2])
        # розбиття даних на окремі частини
        hours = list(weather.keys())
        temperature = [hour_data[0] for hour_data in weather.values()]
        rain = [hour_data[1] for hour_data in weather.values()]
    except Exception as e:
        bot.send_message(message.chat.id, 'Виникла помилка, спробуй ще раз.\nАбо перевір правильність налаштувань.',
                         reply_markup=markup)
        lock = 0
        print(repr(e))
        return

    # створення графіку
    bot.send_message(message.chat.id, 'Будую гарненький графік...')
    try:
        # створення графіку
        img, text = build_diagram(hours, temperature, rain, time_now, time_str, user_data[0][2])
        bio = BytesIO()
        # збереження графіку в буфер
        img.save(bio, format='PNG')
        bio.seek(0)
    except Exception as e:
        bot.send_message(message.chat.id, 'Виникла помилка, спробуй ще раз.\nАбо перевір правильність налаштувань.',
                         reply_markup=markup)
        lock = 0
        print(repr(e))
        return
    # відправлення графіку, тексту та видалення минулих повідомлень про стан
    bot.send_photo(message.chat.id, photo=bio, caption=text, reply_markup=markup)
    bot.delete_message(message.chat.id, message_id=message.message_id + 1)
    bot.delete_message(message.chat.id, message_id=message.message_id + 2)
    img.close()
    # звільнення блокування
    lock = 0


# змінна для блокування виконання функції
lock2 = 0


# функція для відправлення картинки як вдягнутись
def get_image(message, markup):
    global user_id
    user_id = message.from_user.id

    # блокування виконання функції
    global lock2
    if lock2 == 1:
        return
    lock2 = 1

    user_data = get_data(user_id) # отримання даних користувача
    # перевірка чи користувач ввів місто та стать
    if user_data[0][2] == '' or user_data[0][3] == -1:
        bot.send_message(message.chat.id, 'Спочатку введи усі дані у налаштуваннях.',
                         reply_markup=markup)
        lock2 = 0
        return

    bot.send_message(message.chat.id, 'Зачекай, створюю зображення...', reply_markup=types.ReplyKeyboardRemove())
    try:
        # створення посилань для парсингу відповідно до налаштувань
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
        # отримання даних з сайтів
        weather = parse_all(url_gismeteo, url_sinoptik, url_meta)
        # отримання даних про час зараз
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

    # отримання температури та опадів на зараз
    temperature_now, rain_now = get_temperature_and_rain_probability(temperature, rain, time_now)

    try:
        # отримання зображення
        img = create_image(temperature_now, rain_now, user_data[0][3], driver_type_img, proxy_needed)
    except Exception as e:
        bot.send_message(message.chat.id, 'Виникла помилка, спробуй ще раз.', reply_markup=markup)
        lock2 = 0
        print(repr(e))
        return

    try:
        # відправлення зображення
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


#запуск бота на постійну роботу
bot.polling(none_stop=True, interval=0)
