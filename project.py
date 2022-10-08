from dataclasses import dataclass
from datetime import datetime, timedelta
from threading import Thread
import json
import os
import sys
import time
import requests
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# Словник відповідності українських і англійських назв міст
# (OpenWeatherMap API працює лише з англійськими назвами)
name_mappings = {
    "Київ": "Kiev",
    "Харків": "Kharkiv",
    "Львів": "Lviv",
    "Одеса": "Odesa",
    "Дніпро": "Dnipro",
    "Полтава": "Poltava",
    "Запоріжжя": "Zaporizhzhia",
    "Івано-Франківськ": "Ivano-Frankivsk",
    "Тернопіль": "Ternopil",
    "Вінниця": "Vinnytsia",
    "Рівне": "Rivne",
    "Хмельницький": "Khmelnytskyi",
    "Луцьк": "Lutsk",
    "Житомир": "Zhytomyr",
    "Черкаси": "Cherkasy",
    "Кропивницький": "Kropyvnytskyi",
    "Чернівці": "Chernivtsi",
    "Чернігів": "Chernihiv",
    "Миколаїв": "Mykolaiv",
    "Ужгород": "Uzhhorod",
    "Суми": "Sumy",
    "Херсон": "Kherson",
    "Донецьк": "Donetsk",
    "Луганськ": "Luhansk",
    "Сімферополь": "Simferopol"
}


# Наближений еквівалент struct у С
@dataclass
class CityTemperature:
    name: str
    temperature: int
    last_updated: datetime  # Об'єкт дати/часу для запам'ятовування


# Сортування масиву об'єктів
def sort(data: list[CityTemperature]) -> list[CityTemperature]:
    copy = data.copy()
    # Звичайний bubble sort, це не критично, бо об'єктів завжди всього лише 25
    length = len(data)
    for i in range(length - 1):
        for j in range(length - 1 - i):
            if copy[j].temperature > copy[j+1].temperature:
                copy[j], copy[j+1] = copy[j+1], copy[j]
    return copy


# Лінійний пошук елемента з найменшою температурою
def smallest(data: list[CityTemperature]) -> CityTemperature:
    smallest = data[0]
    for city in data:
        if city.temperature < smallest.temperature:
            smallest = city
    
    return smallest


# Лінійний пошук елемента з найбільшою температурою
def biggest(data: list[CityTemperature]) -> CityTemperature:
    biggest = data[0]
    for city in data:
        if city.temperature > biggest.temperature:
            biggest = city
    
    return biggest


# Збереження поточного стану даних у файл json (на випадок закриття програми)
def save(data: list[CityTemperature]) -> None:
    dict_data = [
        {
            "name": city.name,
            "temperature": city.temperature,
            "last_updated": city.last_updated.strftime("%d-%m-%Y %H:%M:%S")
        }
        for city in data
    ]
    json_data = json.dumps(dict_data, indent=4, ensure_ascii=False)
    with open("last.json", "w", encoding="utf8") as file:
        file.write(json_data)


# Завантаження останнього стану даних з файлу
def load() -> list[CityTemperature]:
    with open("last.json", "r", encoding="utf8") as file:
        data = file.read()
        data = json.loads(data)
        data = [
            CityTemperature(
                name=city["name"],
                temperature=city["temperature"],
                last_updated=datetime.strptime(city["last_updated"], "%d-%m-%Y %H:%M:%S")
            )
            for city in data
        ]
        return data

# Згенерувати масив об'єктів в початковому стані на початку програми
def init() -> list[CityTemperature]:
    return [
        CityTemperature(
            name=name,
            temperature=0, # Початкові дані будуть нулем
            last_updated=datetime.now().replace(microsecond=0)
        )
        for name in name_mappings.keys()
    ]


# Оновити дані
def update_data(data: list[CityTemperature]) -> None:
    # Ключ (токен) OpenWeatherMap API
    with open("token.txt", "r") as file:
        token = file.read()

    # Створення HTTP-сессії для відправки запитів
    with requests.Session() as session:
        for city in data:
            # Отримання інформації про місто за його англійським ім'ям
            eng_name = name_mappings[city.name]
            response = session.get(f"https://api.openweathermap.org/data/2.5/weather?q={eng_name}&appid={token}").json()

            # Перевод температури із Кельвінів у Цельсій
            kelvin_temperature = response["main"]["temp"]
            celcius_temperature = round(kelvin_temperature - 273.15)

            # Оновлення даних об'єкту
            city.temperature = celcius_temperature
            city.last_updated = datetime.now().replace(microsecond=0)


# Функція-таргет, яку виконуватиме Потік, який буде оновлювати дані (refresher_thread)
def data_refresh_cycle(data: list[CityTemperature], frequency: int) -> None:
    while True:
        update_data(data)
        save(data)

        # Розрахувати скільки часу "спати" до наступного оновлення
        current = datetime.now()
        future = current + timedelta(minutes=frequency)
        time.sleep((future - current).total_seconds())
        

# Функція будування і оновлення графіку (запускається на Головному Потоці)
def plot_refresh_cycle(data: list[CityTemperature], frequency: int) -> None:
    # Створення пустої фігури на початку програми
    plt.figure(figsize=(10,6))

    def animate(i):
        # Знайдення найменшої і найбільшої температури
        minimum = smallest(data)
        maximum = biggest(data)

        # Сортування міст за температурою і очищення попереднього слайду
        sorted_copy = sort(data)
        names = [city.name for city in sorted_copy]
        temperatures = [city.temperature for city in sorted_copy]
        plt.clf()
        
        # Встановлення підписів на осях та заголовку із часом
        plt.xticks(range(1, len(data) + 1), names, rotation=45, ha="right")
        plt.xlabel("Міста України", labelpad=20)
        plt.ylabel("Температура повітря, °C")
        plt.title(data[0].last_updated.strftime("%d-%m-%Y %H:%M:%S"))

        # Створення блочної діаграми на графіку
        bar_chart = plt.bar(range(1, len(data) + 1), temperatures, width=0.5)
        for index, rect in enumerate(bar_chart):
            height = rect.get_height()
            plt.text(rect.get_x() + rect.get_width() / 2, height + 0.5, temperatures[index], ha="center")
        
        # Відображення інформації про найменшу і найбільшу температури
        plt.text(27, 20, f"Найнижча:\n{minimum.name}, {minimum.temperature} °C")
        plt.text(27, 17, f"Найвища:\n{maximum.name}, {maximum.temperature} °C")
        # Вирівняння графіку щоб усі написи вмістились
        plt.subplots_adjust(right=0.8, bottom=0.2)

    # Старт анімації графіку із заданим інтервалом
    animation_obj = FuncAnimation(plt.gcf(), animate, interval=frequency*1000*60)
    plt.show()


# Сама програма
def main():
    # Отримання бажаної частоти оновлення (в хвилинах) з аргументів запуску програми
    if len(sys.argv) == 1:
        print("Введіть як аргумент частоту оновлення даних в хвилинах!")
        return
    frequency = sys.argv[1]
    try:
        frequency = int(frequency)
    except ValueError:
        print("Частота оновлення має бути числом!")
        return

    # Ініціалізувати буфер даних попередніми (якщо є) або пустими значеннями.
    # Він буде доступний для читання і змінення для обох Потоків
    data = None
    if os.path.exists("last.json"):
        data = load()
    else:
        data = init()

    # Запуск Потоку оновлення даних
    refresher_thread = Thread(target=data_refresh_cycle, args=(data, frequency))
    refresher_thread.start()

    # Запуск візуалізації (на цьому, Головному Потоці)
    plot_refresh_cycle(data, frequency)

# Виклик main-функції лише при запуску цього файлу,
# щоб можна було звідси без проблем імпортувати інші функції для тестів,
# не запускаючи цей скрипт
if __name__ == "__main__":
    main()
