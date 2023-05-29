import requests
from bs4 import BeautifulSoup

#парсинг сайту з проксі, отримання списку проксі
def get_proxy_list():
    url = 'https://free-proxy-list.net/'
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    soup = BeautifulSoup(response.text, 'html.parser')
    proxy_list = soup.find('textarea').get_text()
    proxy_list = proxy_list.split('\n')
    proxy_list = [proxy_list[i] for i in range(2, len(proxy_list)) if proxy_list[i] != '']

    return proxy_list
