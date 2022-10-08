import unittest
from datetime import datetime
import requests
import project
from project import CityTemperature

class TestProgram(unittest.TestCase):
    # Рандомні дані для тестів
    data = [
        CityTemperature("Харків", 20, datetime.now().replace(microsecond=0)),
        CityTemperature("Київ", 17, datetime.now().replace(microsecond=0)),
        CityTemperature("Львів", 18, datetime.now().replace(microsecond=0)),
        CityTemperature("Одеса", 15, datetime.now().replace(microsecond=0))
    ]
    
    # Щоб дані правильно зберігалися і завантажувалися
    def test_saving_and_loading_from_file(self):
        project.save(self.data)
        self.assertEqual(self.data, project.load())
    
    # Повинно бути Одеса
    def test_smallest(self):
        self.assertEqual(self.data[3], project.smallest(self.data))
    
    # Повинно бути Харків
    def test_biggest(self):
        self.assertEqual(self.data[0], project.biggest(self.data))
    
    # Порівняння з вбудованим алгоритмом sorted()
    def test_sort(self):
        sorted_data_copy = sorted(self.data.copy(), key=lambda city: city.temperature)
        project.sort(self.data)
        self.assertEqual(sorted_data_copy, self.data)
    
    # Всі статус-коди http-запитів повинні бути 200 (ОК)
    def test_city_names_validity(self):
        with open("token.txt", "r") as file:
            token = file.read()
        statuses = []
        with requests.Session() as session:
            for eng_name in project.name_mappings.values():
                response = session.get(f"https://api.openweathermap.org/data/2.5/weather?q={eng_name}&appid={token}")
                statuses.append(response.status_code)
        self.assertEqual(statuses, [200 for _ in range(25)])
    