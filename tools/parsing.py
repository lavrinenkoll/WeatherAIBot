import requests
from bs4 import BeautifulSoup


def parse_all(url_gismeteo, url_sinoptik, url_meta):

    try:
        dict_gismeteo = parse_gismeteo(url_gismeteo)
    except:
        dict_gismeteo = {}
    try:
        dict_sinoptik = parse_sinoptik(url_sinoptik)
    except:
        dict_sinoptik = {}
    try:
        dict_meta = parse_meta(url_meta)
    except:
        dict_meta = {}

    data = [dict_gismeteo, dict_sinoptik, dict_meta]
    dict_average = get_average(data)
    return dict_average

def get_average(data):
    dict_average = {}
    number_of_sources = 0

    hours = [x for x in range(0, 24, 3)]
    temperature = [0]*len(hours)
    rain = [0]*len(hours)
    for source in data:
        if source == {}:
            continue

        number_of_sources += 1
        for i in range(len(hours)):
            temperature[i] += source[hours[i]][0]
            rain[i] += source[hours[i]][2]

    if number_of_sources == 0:
        print('Error. No data available.')
        return
    for i in range(len(hours)):
        dict_average[hours[i]] = [temperature[i]//number_of_sources, 100*round(rain[i]/number_of_sources, 2)]

    return dict_average

def parse_gismeteo(url):
    dict_gismeteo = {}
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    soup = BeautifulSoup(response.text, 'html.parser')

    info_div = soup.find('div', class_='widget-body widget-columns-8')

    hours = range(0, 24, 3)

    temperature_div = info_div.find('div', class_='chart')
    temperature = temperature_div.find_all('span', class_='unit unit_temperature_c')
    temperature = [int(temp.text) for temp in temperature]

    type_div = info_div.find('div', class_='widget-row widget-row-icon')
    types = type_div.find_all('div', class_='weather-icon tooltip')
    types = [type['data-text'] for type in types]

    rain = [1 if 'дощ' in type else 0 for type in types]

    for i in range(len(hours)):
        dict_gismeteo[hours[i]] = [temperature[i], types[i], rain[i]]

    return dict_gismeteo

def parse_sinoptik(url):
    dict_sinoptik = {}
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    soup = BeautifulSoup(response.text, 'html.parser')

    info_div = soup.find('table', class_='weatherDetails')

    hours = range(0, 24, 3)

    temperature_div = info_div.find('tr', class_='temperatureSens')
    temperature = temperature_div.find_all('td')
    temperature = [int(temp.text[:-1]) for temp in temperature]

    type_div = info_div.find('tr', class_='img weatherIcoS')
    types = type_div.find_all('div')
    types = [type['title'] for type in types]

    rain = [1 if 'дощ' in type else 0 for type in types]

    for i in range(len(hours)):
        dict_sinoptik[hours[i]] = [temperature[i], types[i], rain[i]]

    return dict_sinoptik

def parse_meta(url):
    dict_meta = {}
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    soup = BeautifulSoup(response.text, 'html.parser')

    info_div = soup.find('div', class_='city__forecast-content')

    columns = info_div.find_all('div', class_='city__forecast-col')
    hours = range(0, 24, 3)
    temperature = []
    types = []
    rain = []

    for column in columns:
        temp = column.find('div', class_='city__forecast-feels').text
        temperature.append(int(temp[:-1]))

        type = column.find('div', class_='city__forecast-icon icon')['data-tippy-content']
        types.append(type)

        rain.append(1 if 'дощ' in type else 0)

    for i in range(len(hours)):
        dict_meta[hours[i]] = [temperature[i], types[i], rain[i]]

    return dict_meta