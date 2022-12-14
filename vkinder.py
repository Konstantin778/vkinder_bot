from pprint import pprint
import requests
import vk_api


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

    def get_params(self, user_ids, fields: str = "bdate, city, sex, relation"):
        #Функция для получения параметров пользователя бота для подбора подходящей пары
        params = {
            "user_ids": user_ids,
            "fields": fields
        }
        try:
            response = requests.get(f"{self.base_url}/method/users.get",
                            params={**params, **self.general_params()}).json()
        except vk_api.exceptions.ApiError:
            pass
        except KeyError:
            pass
        except:
            print("Error")
        else:
            if response is not None:
                return response["response"][0]
            else:
                print("get_params() function has returned None object")
                pass


    def search_people(self, age_from, age_to, sex, city, status, offset, sorting: int = 0, count: int = 50):
        #Функция для получения списка людей по подходящим параметрам
        params = {
            "age_from": age_from,
            "age_to": age_to,
            "sex": sex,
            "city": city,
            "status": status,
            "offset": offset,
            "sort": sorting,
            "count": count
        }
        try:
            response = requests.get(f"{self.base_url}/method/users.search",
                            params={**self.general_params(), **params}).json()["response"]["items"]
        except vk_api.exceptions.ApiError:
            pass
        except KeyError:
            pass
        except:
            print("Error")
        else:
            if response is not None:
                return response
            else:
                print("search_people() function has returned None object")
                pass

    def get_photos(self, owner_id, album_id = "profile", photo_sizes = 1, extended = 1):
        #Функция для получения списка фотографий профиля и id выбранного пользователя
        params = {
            "owner_id": owner_id,
            "album_id": album_id,
            "photo_sizes": photo_sizes,
            "extended": extended
        }
        try:
            response = requests.get(f"{self.base_url}/method/photos.get",
                            params={**self.general_params(), **params}).json()["response"]["items"]
        except vk_api.exceptions.ApiError:
            pass
        except KeyError:
            pass
        except:
            print("Error")
        else:
            if response is not None:
                return response
            else:
                print("get_photos() function has returned None object")
                return []
        return []


vk_client = Vkinder(token=token, api_version="5.131")




