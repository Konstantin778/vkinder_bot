from pprint import pprint
import requests

with open("token_app.txt", "r") as file:
    token = file.read().strip()

class Vkinder:
    def __init__(self, token: str, api_version: str, base_url: str = "https://api.vk.com/"):
        self.token = token
        self.api_version = api_version
        self.base_url = base_url

    def general_params(self):
        return {
            "access_token": self.token,
            "v": self.api_version,
        }

    def get_params(self, user_ids, fields: str):  #Функция для получения параметров пользователя бота для подбора подходящей пары
        params = {
            "user_ids": user_ids,
            "fields": fields
        }
        return requests.get(f"{self.base_url}/method/users.get",
                            params={**params, **self.general_params()}).json()

    def search_people(self, age_from, age_to, sex, city, status, sorting: int = 0, count: int = 1000): #Функция для получения списка людей по подходящим параметрам
        params = {
            "age_from": age_from,
            "age_to": age_to,
            "sex": sex,
            "city": city,
            "status": status,
            "sort": sorting,
            "count": count,
        }
        return requests.get(f"{self.base_url}/method/users.search",
                            params={**self.general_params(), **params}).json()["response"]["items"]

    def get_photos(self, owner_id, album_id = "profile", photo_sizes = 1, extended = 1): #Функция для получения списка фотографий профиля и id выбранного пользователя
        params = {
            "owner_id": owner_id,
            "album_id": album_id,
            "photo_sizes": photo_sizes,
            "extended": extended
        }
        return requests.get(f"{self.base_url}/method/photos.get",
                            params={**self.general_params(), **params}).json()["response"]["items"], owner_id


vk_client = Vkinder(token=token, api_version="5.131")
