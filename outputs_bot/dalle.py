import random

import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tools.create_drivers import create_driver, create_webdriver
from tools.get_proxy import get_proxy_list

#creation of a picture by a neural network

#створення картинки
def create_image(temperature, rain, sex, type_driver, proxy_needed):
    text = f"full length {'man' if sex == 0 else 'woman'} dressed for {temperature} degree weather" \
           f"{' with rain' if rain >=60 else ''}"

    # if the local option is selected
    if type_driver == 'local':
        if proxy_needed==1:
            try:
                attempts = 0
                proxy_list = get_proxy_list() # list of proxies from the site
                random.shuffle(proxy_list) # shuffle the proxy list

                for proxy in proxy_list: # we go through the list of proxies and try to make a request
                    try:
                        driver = create_driver(proxy)
                        url = "https://deepai.org/machine-learning-model/text2img"
                        driver.get(url)

                        text_area = driver.find_element(By.XPATH, "//textarea[contains(@class, 'model-input-text-input')]")
                        text_area.send_keys(text)

                        driver.execute_script("textModelSubmit()")

                        wait = WebDriverWait(driver, 30)
                        wait.until(EC.presence_of_element_located(
                            (By.CSS_SELECTOR, "div.try-it-result-area > img[src*='job-view-file']")))

                        WebDriverWait(driver, 3)
                        img = driver.find_element(By.XPATH, "//img[starts-with(@src, 'https://api.deepai.org/job-view-file/')]")
                        src = img.get_attribute('src')

                        response = requests.get(src)
                        return response.content
                    except Exception as e:
                        print(f"Error: {e}")
                        attempts += 1
                        if attempts == 5: # if it was not possible to make a request 5 times, then we exit the cycle
                            break
            except Exception as e:
                print(e)
                return None

        # if no proxy is needed
        else:
            driver = create_driver()
            url = "https://deepai.org/machine-learning-model/text2img"
            driver.get(url)

            text_area = driver.find_element(By.XPATH, "//textarea[contains(@class, 'model-input-text-input')]")
            text_area.send_keys(text)

            driver.execute_script("textModelSubmit()")

            wait = WebDriverWait(driver, 30)
            wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div.try-it-result-area > img[src*='job-view-file']")))

            WebDriverWait(driver, 3)
            img = driver.find_element(By.XPATH, "//img[starts-with(@src, 'https://api.deepai.org/job-view-file/')]")
            src = img.get_attribute('src')

            response = requests.get(src)
            return response.content

    # if the remote web driver option is selected
    elif type_driver == 'remote':
        try:
            driver = create_webdriver()
            url = "https://deepai.org/machine-learning-model/text2img"
            driver.get(url)

            if type_driver == 'remote':
                try:
                    button = driver.find_element(By.XPATH, "//button[contains(@class, 'css-47sehv')]")
                    button.click()
                except:
                    pass

                text_area = driver.find_element(By.XPATH, "//textarea[contains(@class, 'model-input-text-input')]")
                text_area.send_keys(text)

                driver.execute_script("textModelSubmit()")

                wait = WebDriverWait(driver, 30)
                wait.until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "div.try-it-result-area > img[src*='job-view-file']")))

                WebDriverWait(driver, 3)
                img = driver.find_element(By.XPATH, "//img[starts-with(@src, 'https://api.deepai.org/job-view-file/')]")
                src = img.get_attribute('src')

                response = requests.get(src)

                driver.quit()
                return response.content
        except Exception as e:
            print(e)
            driver.quit()
            return None

