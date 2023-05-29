import matplotlib.pyplot as plt
import matplotlib as mpl
import seaborn as sns
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

# створення графіку погооди на сьогодні + додаткові функції для отримання даних

# створення графіку
def build_diagram(time, temperature, rain_probability, time_now, time_str, adress):
    mpl.use('Agg')
    sns.set_style("whitegrid")
    time.append(24)
    temperature.append(temperature[-1])
    rain_probability.append(rain_probability[-1])

    time_part = time_now // 3
    time_part = time_part * 3
    temperature_now = temperature[time_part // 3]
    rain_probability_now = rain_probability[time_part // 3]

    fig, axs = plt.subplots(nrows=3, ncols=1, gridspec_kw={'height_ratios': [0.2, 0.4, 0.4]}, figsize=(8, 8))

    icon = Image.open('res/icon.png')
    text_image = Image.new('RGBA', (2500, 500), (255, 255, 255, 0))
    draw = ImageDraw.Draw(text_image)
    font = ImageFont.truetype('res/font.ttf', 90, encoding='unic')
    text = f"{adress}\nЧас зараз: {time_str}\nТемпература: {temperature_now}°C\n" \
           f"Можливість дощу: {rain_probability_now}%"
    lines = text.split('\n')
    line_height = font.getsize('hg')[1]
    top_margin = 10
    left_margin = 10
    for i, line in enumerate(lines):
        draw.text((left_margin, top_margin + i * line_height), line, font=font, fill=(0, 0, 0, 255), encoding='utf-8')

    result_image = Image.new('RGBA', (icon.width + text_image.width, icon.height), (255, 255, 255, 0))
    result_image.paste(icon, (-20, 0))
    result_image.paste(text_image, (icon.width+100, 40))

    result_array = np.array(result_image)

    axs[0].imshow(result_array)
    axs[0].axis('off')

    axs[1].plot(time, temperature, color='black', linewidth=1, drawstyle='steps-post')
    axs[1].set_ylabel('Температура, °C')
    axs[1].set_xticks(time)
    axs[1].set_xlim(0-0.05, 24+0.05)
    axs[1].set_ylim(round(min(temperature))-1, round(max(temperature))+1)
    axs[1].set_yticks(range(round(min(temperature))-1, round(max(temperature))+1, 1))
    axs[1].set_xticklabels([str(t) + ':00' for t in time])
    axs[1].axvline(x=time_now, color='red', linestyle='--', linewidth=2)
    axs[1].fill_between(time, temperature, color='red', alpha=0.1)

    axs[2].plot(time, rain_probability, color='black', linewidth=1, drawstyle='steps-post')
    axs[2].set_xlabel('Час, год')
    axs[2].set_xticks(time)
    axs[2].set_xlim(0-0.05, 24+0.05)
    axs[2].set_ylim(-1, 101)
    axs[2].set_yticks(range(0, 101, 10))
    axs[2].set_xticklabels([str(t) + ':00' for t in time])
    axs[2].set_ylabel('Вірогідність дощу, %')
    axs[2].axvline(x=time_now, color='red', linestyle='--', linewidth=2)
    axs[2].axhline(y=50, color='black', linestyle='--', linewidth=1)
    axs[2].fill_between(time, rain_probability, color='blue', alpha=0.1)

    canvas = FigureCanvas(fig)
    canvas.draw()

    img = Image.frombytes('RGB', canvas.get_width_height(), canvas.tostring_rgb())
    img = img.crop((0, 60, img.width, img.height))

    return img, text


# отримання даних про поточну температуру та вірогідність дощу
def get_temperature_and_rain_probability(temperature, rain_probability, time_now):
    time_part = time_now // 3
    time_part = time_part * 3
    temperature_now = temperature[time_part // 3]
    rain_probability_now = rain_probability[time_part // 3]
    return temperature_now, rain_probability_now


# отримання даних про поточний час для вказаної адреси
def get_time_now(adress):
    import requests
    from bs4 import BeautifulSoup
    adress = adress.replace(' ', '+')
    url = 'https://www.google.com/search?q={}+time'.format(adress)

    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    time_str = soup.find('div', {'class': 'BNeawe iBp4i AP7Wnd'}).get_text()

    if time_str[-2:] == "AM" and time_str[:2] == "12":
        return 0, "00" + time_str[2:-2]

    elif time_str[-2:] == "AM":
        return int(time_str[:2]), time_str[:-2]

    elif time_str[-2:] == "PM" and time_str[:2] == "12":
        return int(time_str[:2]), time_str[:-2]

    elif time_str[-2:] == "PM":
        hours, minutes = time_str[:-3].split(':')
        hours = int(hours)
        minutes = int(minutes)

        return hours + 12, "{:02d}:{:02d}".format(hours + 12, minutes)

    else:
        return int(time_str[:2]), time_str