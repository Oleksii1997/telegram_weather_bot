# WeatherHomeBot weather_bot

import telebot
from telebot import types
from geopy.geocoders import Nominatim
import requests
from bs4 import BeautifulSoup

HOST = 'https://sinoptik.ua/'
URL = 'https://sinoptik.ua/погода-'
HEADERS = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/'
              'avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/87.0.4280.88 Mobile Safari/537.367.36'
}

bot = telebot.TeleBot('your token', parse_mode=None)


@bot.message_handler(commands=['start'])
def start_func(message):
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
    geolocation = types.KeyboardButton(text="Надіслати геолокацію", request_location=True)
    markup.row(geolocation)
    bot.send_message(message.chat.id, "Привіт) \nУведіть назву населеного пункту, погода в якому вас цікавить "
                                      "або відправте геолокацію.", reply_markup=markup)


@bot.message_handler(commands=['help'])
def start_func(message):
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
    geolocation = types.KeyboardButton(text="Надіслати геолокацію", request_location=True)
    markup.row(geolocation)
    text = "Привіт)\n Я можу показати вам погоду за певний період часу, якщо " \
           "ви надішлете мені свою геолокацію, або назву міста.\n Щоб запустити або почати заново наш " \
           "діалог відправте команду '/start'"
    bot.send_message(message.chat.id, f"{text}", reply_markup=markup)


@bot.message_handler(commands=['about'])
def start_func(message):
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
    geolocation = types.KeyboardButton(text="Надіслати геолокацію", request_location=True)
    markup.row(geolocation)
    text = "Привіт) Я бот який вміє позувати погоду.\n" \
           "Для того щоб почати діалог зі мною надішліть команду '/start'\n" \
           "Далі я запропоную відправити мені ваше місцезнаходження або назву " \
           "населеного пункут, погоду в якому ви хочете дізнатися.\n" \
           "Я перевірю чи таке місто існує, і якщо ви мене не намагаєтесь надурити,\n" \
           "зберу для вас погоду за обраний період часу.\n" \
           "Необхідну інформацію мені надає сайт sinoptik.ua"
    bot.send_message(message.chat.id, f"{text}", reply_markup=markup)


# клас який працює з об'єктом геолокації та назвою міста, перевіряє чи існує відповідна сторінка на sinoptik.ua
# повертає користувачу повідомлення або клавіатуру вибору дати погоди або помилу
class GetLocation:
    def __init__(self, message):
        self.message = message
        self.error_location = "Сталася помилка, об'єкт геолокації не надав необхідну інформацію. " \
                              "Надішліть текстову назву населеного пункту."
        self.city_name_error = "Перевірте правильність написання, такий населений пункт не знайдено"

    # надсилає користувачу повідомлення про помилку
    def search_error(self, error_message):
        markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
        geolocation = types.KeyboardButton(text="Надіслати геолокацію", request_location=True)
        markup.row(geolocation)
        bot.send_message(self.message.chat.id, f'{error_message}', reply_markup=markup)

    # надсилає клавіатуру вибору днів погоди
    def days_weather(self, city_name):
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton(text=f"Погода, {city_name}, на сьогодні", callback_data=f"{city_name},1"))
        keyboard.add(types.InlineKeyboardButton(text=f"Погода, {city_name}, на 3 дні", callback_data=f"{city_name},3"))
        keyboard.add(types.InlineKeyboardButton(text=f"Погода, {city_name}, на 7 днів", callback_data=f"{city_name},7"))
        keyboard.add(
            types.InlineKeyboardButton(text=f"Погода, {city_name}, на 10 днів", callback_data=f"{city_name},10"))
        bot.send_message(self.message.chat.id, "Погода на який день вас цікавить?", reply_markup=keyboard)

    # перевірка чи об'єкт геолокації повернув назву населеного пункту і
    # чи існує відповідна сторінка на sinoptik.ua
    # повертає або помилку або клавіатуру
    def city_sinoptic_valid(self, geo_list):
        city_name = None
        for item in geo_list:
            if " " in item or item.isdigit() or item == 'Україна':
                pass
            else:
                r = requests.get(f"{URL}{item}", headers=HEADERS)
                if r.status_code is 200:
                    city_name = item
        if city_name is None:
            if len(geo_list) > 1:
                self.search_error(self.error_location)
            else:
                self.search_error(self.city_name_error)
        else:
            self.days_weather(city_name.capitalize())

    # якщо користувач надіслав геолокацію, отримуємо адресу з об'єкта геолокації
    # повертає або помилку або викликає city_sinoptic_valid(self, geo_list)
    def search_location(self):
        geolocator = Nominatim(user_agent='weather.py')
        # якщо ми отримали геолокацію
        try:
            location_list = geolocator.reverse(
                "%s, %s" % (str(self.message.location.latitude), str(self.message.location.longitude)),
                timeout=3, exactly_one=True)
        except:
            location_list = None
        if location_list is not None:
            location_list = location_list.address.split(', ')
            self.city_sinoptic_valid(location_list)
        else:
            self.search_error(self.error_location)

    # якщо користувач надіслав текстову назву міста, перевіряємо валідність
    # повертає або помилку або викликає city_sinoptic_valid(self, geo_list)
    def city_name_valid(self):
        chars = set('0123456789$,@?!^";:-+=#№<>*/|')
        if any((c in chars) for c in self.message.text):
            bot.send_message(self.message.chat.id, "Назва населеного пункту не повинна містити символів або чисел")
        elif ' ' in self.message.text:
            bot.send_message(self.message.chat.id, "В назві не повинно бути пробілів, напишіть через дефіс")
        elif len(self.message.text) >= 45:
            bot.send_message(self.message.chat.id, "Такого населеного пункту не існує")
        else:
            geo_list = [self.message.text.lower()]
            self.city_sinoptic_valid(geo_list)


# клас який збирає погоду за запитом клієнта і надає відповідб
class ParsWeather:

    def __init__(self, message):
        self.message = message

    # повідомлення про помилку якщо сторінка sinoptik.ua не відповідає
    def page_error(self):
        markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
        geolocation = types.KeyboardButton(text="Надіслати геолокацію", request_location=True)
        markup.row(geolocation)
        bot.send_message(self.message.message.chat.id, "Сталася помилка(, спробуйте пізніше. ", reply_markup=markup)

    # відправляємо результат клієнту
    def view_weather(self, data_list, city_name=None, region=None):
        markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
        geolocation = types.KeyboardButton(text="Надіслати геолокацію", request_location=True)
        markup.row(geolocation)
        result_text = f"Я зібрав інформацію за вашим запитом.\n {city_name} \n {region} \n"
        for item in data_list:
            result_text += f'{item["date"]} {item["month"]}: \n   Макс: {item["max_temp"]} - ' \
                           f'Мін: {item["min_temp"]} \n   {item["description"]}\n'
        bot.send_message(self.message.message.chat.id, f"{result_text}", reply_markup=markup)

    # парсимо дані з сторінки, викликаємо view_weather або page_error
    def get_content(self, r):
        item = 1
        days = int(self.message.data.split(',')[1])
        soup = BeautifulSoup(r.content, 'html.parser')
        try:
            city_name = soup.find('div', class_='cityName').find('h1').text
            region = soup.find('div', class_='currentRegion').text
            data_list = []
            while item <= days:
                data_dict = {}
                if item == 1:
                    data_dict["description"] = soup.find('div', class_='wDescription').find('div',
                                                                                            class_='description').text

                else:
                    data_dict["description"] = soup.find('div', id=f'bd{item}').find('div', class_='weatherIco').get(
                        'title')
                data_dict["max_temp"] = soup.find('div', id=f'bd{item}').find('div', class_='max').find('span').text
                data_dict["min_temp"] = soup.find('div', id=f'bd{item}').find('div', class_='min').find('span').text
                data_dict["date"] = soup.find('div', id=f'bd{item}').find('p', class_='date').text
                data_dict["month"] = soup.find('div', id=f'bd{item}').find('p', class_='month').text
                data_list.append(data_dict)
                item += 1
            self.view_weather(data_list, city_name, region)
        except:
            self.page_error()

    # отримуємо сторінку html, передаємо її парсеру, або викликаємо помилку
    def get_html(self):
        city = self.message.data.split(',')[0].lower()
        r = requests.get(f"{URL}{city}/10-дней")
        if r.status_code is 200:
            self.get_content(r)
        else:
            self.page_error()


# отримуємо назву міста
@bot.message_handler(content_types=['text'])
def get_geolocation(message):
    bot_geo = GetLocation(message)
    bot_geo.city_name_valid()


# отримуємо геолокацію користувача
@bot.message_handler(content_types=['location'])
def get_geolocation(message):
    bot_geo = GetLocation(message)
    bot_geo.search_location()


# обробка клавіатури вибору дня на який цікавить погода
@bot.callback_query_handler(func=lambda message: inline_wether_valid(message))
def select_wether(message):
    bot_pars = ParsWeather(message)
    bot_pars.get_html()


# перевірка, що відповідь саме від клавіатури вибору дня погоди
def inline_wether_valid(message):
    data = message.data.split(',')
    if int(data[1]) in [1, 3, 7, 10]:
        return True
    else:
        return False


if __name__ == "__main__":
    bot.polling()
