import time
from urllib.parse import urljoin, urlsplit, urlunsplit
import requests
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from tools.create_drivers import create_driver, create_webdriver

# getting weather links using selenium
def create_urls_selenium(adress, type_driver):
    adress = adress.replace(' ', '+')
    adress = adress.replace(',', '')
    url = "https://www.google.com/search?q=погода+гісметео+сьогодні+"+adress

    if type_driver == 'local':
        driver = create_driver()
    elif type_driver == 'remote':
        driver = create_webdriver()

    try:
        driver.get(url)
        assert "погода гісметео сьогодні" in driver.title

        link = driver.find_element(By.XPATH, "//a[contains(@href, 'gismeteo.ua')]")
        url = link.get_attribute('href')
        driver.get(url)

        url_gismeteo = driver.current_url
        url_gismeteo = url_gismeteo.replace('gismeteo.ua', 'gismeteo.ua/ua')

        #sinoptik
        url = "https://www.google.com/search?q=погода+sinoptik+сьогодні+"+adress
        driver.get(url)
        assert "погода sinoptik сьогодні" in driver.title
        link = driver.find_element(By.XPATH, "//a[contains(@href, 'sinoptik.ua')]")
        url = link.get_attribute('href')
        driver.get(url)
        url_sinoptik = driver.current_url

        #pogoda meta
        url = "https://www.google.com/search?q=погода+meta+сьогодні+"+adress
        driver.get(url)
        assert "погода meta сьогодні" in driver.title
        link = driver.find_element(By.XPATH, "//a[contains(@href, 'pogoda.meta.ua')]")
        url = link.get_attribute('href')
        driver.get(url)
        url_meta = driver.current_url
        driver.close()

        return url_gismeteo, url_sinoptik, url_meta

    except Exception as e:
        print(repr(e))
        driver.close()
        return None, None, None


# getting weather links using requests
def create_urls_requests(adress):
    adress = adress.replace(' ', '+')
    adress = adress.replace(',', '')
    url = f"https://www.google.com/search?q=погода+гісметео+сьогодні+{adress}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    gismeteo_link = soup.find('a', href=lambda href: href and 'gismeteo.ua' in href)['href']
    gismeteo_parts = urlsplit(gismeteo_link)
    if '/ua/' not in gismeteo_parts.path:
        gismeteo_parts = gismeteo_parts._replace(path='/ua' + gismeteo_parts.path)
    gismeteo_link = urlunsplit(gismeteo_parts)

    url = f"https://www.google.com/search?q=погода+sinoptik+сьогодні+{adress}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    sinoptik_link = soup.find('a', href=lambda href: href and 'sinoptik.ua' in href)['href']
    sinoptik_link = urljoin(response.url, sinoptik_link)

    url = f"https://www.google.com/search?q=погода+meta+сьогодні+{adress}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    meta_link = soup.find('a', href=lambda href: href and 'pogoda.meta.ua' in href)['href']
    meta_link = urljoin(response.url, meta_link)

    gismeteo_link = gismeteo_link.split('q=')[1]
    sinoptik_link = sinoptik_link.split('q=')[1]
    sinoptik_link = sinoptik_link.replace('%25', '%')
    meta_link = meta_link.split('q=')[1]

    gismeteo_link = gismeteo_link.split('&sa')[0]
    sinoptik_link = sinoptik_link.split('&sa')[0]
    meta_link = meta_link.split('&sa')[0]

    return gismeteo_link, sinoptik_link, meta_link


# execution time comparison
def count_efficiency():
    adress = 'Кривий Ріг, Дніпропетровська область, Україна'
    time_selenium_local = 0
    time_selenium_remote = 0
    time_requests = 0

    for i in range(5):
        start = time.time()
        create_urls_selenium(adress, 'local')
        time_selenium_local += time.time() - start

        start = time.time()
        create_urls_selenium(adress, 'remote')
        time_selenium_remote += time.time() - start

        start = time.time()
        create_urls_requests(adress)
        time_requests += time.time() - start

    print(f'Algorithm execution time with Selenium locally: {time_selenium_local/5}')
    print(f'Algorithm execution time with Selenium remotely: {time_selenium_remote/5}')
    print(f'Algorithm execution time with requests: {time_requests/5}')

    '''
    Algorithm execution time with selenium locally: 22.83811511993408
    Algorithm execution time with selenium remotely: 12.849758338928222
    Algorithm execution time with requests: 3.3600680351257326
    '''
