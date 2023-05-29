from selenium import webdriver
from selenium.webdriver.chrome.options import Options

#створення драйверів

# тип віддаленого вебдрайвера
webdriver_type = 'saucelabs' #'saucelabs' 'lambdatest'


# створення драйвера локального, за потреби з проксі
def create_driver(proxy=None):
    options = Options()
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-infobars")
    options.add_argument("--mute-audio")
    options.add_argument('--user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                         'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"')

    # отключаем автоматическое подтверждение использования кук
    options.add_argument("--disable-web-security")
    options.add_argument("--allow-running-insecure-content")
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    options.add_argument("--headless")

    if proxy:
        options.add_argument(f"--proxy-server={proxy}")

    driver = webdriver.Chrome(options=options)
    return driver


# створення драйвера віддаленого
def create_webdriver(proxy=None, type = webdriver_type):
    if type == 'lambdatest':
        limitsec = 40

        capabilities = {
            'LT:Options': {
                "build": "Weather bot",
                "name": "Python_project",
                "platformName": "Windows 10"
            },
            "browserName": "Chrome",
            "browserVersion": "latest",
            "timeout": limitsec,
        }

        options = Options()
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-infobars")
        options.add_argument("--mute-audio")

        # отключаем автоматическое подтверждение использования кук
        options.add_argument("--disable-web-security")
        options.add_argument('--disable-cookies')
        options.add_argument("--allow-running-insecure-content")

        if proxy:
            options.add_argument(f"--proxy-server={proxy}")

        with open('private/webdriver_access', 'r') as f:
            webdriver_access = f.read()

        username = webdriver_access.split(':')[0]
        accessToken = webdriver_access.split(':')[1]
        gridUrl = "hub.lambdatest.com/wd/hub"

        url = "https://" + username + ":" + accessToken + "@" + gridUrl

        driver = webdriver.Remote(
            command_executor=url,
            options=options,
            desired_capabilities=capabilities
        )
        return driver

    elif type == 'saucelabs':
        from selenium.webdriver.chrome.options import Options as ChromeOptions

        options = ChromeOptions()
        options.browser_version = "latest"
        options.platform_name = "Windows 11"
        sauce_options = {}
        sauce_options['build'] = 'selenium-build-3TRC3'
        sauce_options['name'] = 'Weatherbot'
        options.set_capability('sauce:options', sauce_options)

        with open('private/sauce_acces', 'r') as f:
            url = f.read()

        driver = webdriver.Remote(command_executor=url, options=options)

        return driver

    else:
        return None
