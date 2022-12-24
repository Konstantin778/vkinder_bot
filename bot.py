import sqlalchemy as sq
from sqlalchemy.orm import declarative_base, sessionmaker
import psycopg2
from pprint import pprint
import datetime
from datetime import date
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import random
from random import randrange
from vkinder import *
from database import *
keyboard = VkKeyboard()
keyboard.add_button("старт", color=VkKeyboardColor.SECONDARY)
keyboard.add_line()
keyboard.add_button("поиск", color=VkKeyboardColor.PRIMARY)
keyboard.add_line()
keyboard.add_button("показ", color=VkKeyboardColor.POSITIVE)

with open("token_bot.txt", "r") as file:
    bot_token = file.read().strip()

vk_session = vk_api.VkApi(token=bot_token)
longpoll = VkLongPoll(vk_session)
vk = vk_session.get_api()

class Bot:
    def __init__(self, bot_token: str):
        self.bot_token = bot_token

    offset = 0
    got_user = []
    shown_couple = []

    def write_msg(self, user_id, message, attachment=None, keyboard = None):
        vk_session.method("messages.send", {"user_id": user_id, "message": message,
                                            "attachment": attachment, "keyboard": keyboard, "random_id": get_random_id()})

    def get_user(self):
        # функция получает параметры пользователя бота и при каждом новом вызове перезаписывает
        # полученные данные в переменную got_user
        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
                user_id = event.user_id
                try:
                    request = event.text
                    if request.lower() == "старт" or request.lower() == "start":
                        self.write_msg(user_id, 'Для начала поиска введите "поиск" ', keyboard=keyboard.get_keyboard())
                        user = (vk_client.get_params(user_ids=user_id))
                        if user is None:
                            self.write_msg(user_id, 'Невозможно определить пользователя.\
                                                         Проверьте настройки учётной записи ')
                            continue
                        if "bdate" not in user.keys():
                            self.write_msg(user_id, f'Недостаточно данных для поиска пары.'
                                               f' Укажите дату рождения в настройках профиля\
                                                            и разрешите её показ')
                            continue
                        if "city" not in user.keys():
                            self.write_msg(user_id,
                                      f'Недостаточно данных для поиска пары.\
                                         Укажите в профиле город своего проживания')
                            continue
                        try:
                            user
                        except vk_api.exceptions.ApiError:
                            self.write_msg(user_id, f'Ошибка api Вконтакте')
                            continue
                        else:
                            self.shown_couple.clear()
                            self.got_user.clear()
                            self.got_user.append(user)
                    else:
                        self.write_msg(user_id, 'неправильно указана команда ')
                        continue
                except ConnectionError:
                    self.write_msg(user_id, 'Ошибка')
                break

    def get_offered_people(self):
        # функция получает данные пользователя из переменной got_user и на их основании ищет подходящие пары
        # и при каждом вызове возвращает список из 50 новых анкет
        if self.got_user[0] is not None:
            birth_year = int(self.got_user[0]["bdate"][-4:])
            current_year = date.today().year
            age = current_year - birth_year

            sex = 0
            if self.got_user[0]["sex"] == 1:
                sex += 2
            else:
                sex += 1
            user_city = self.got_user[0]["city"]["id"]
            relation = self.got_user[0]["relation"]
            try:
                offered_people = vk_client.search_people(age - 1, age + 1, sex, user_city, relation, self.offset)
            except vk_api.exceptions.ApiError:
                self.write_msg(event.user_id, f'Ошибка api Вконтакте')
            else:
                if offered_people is not None:
                    return offered_people
                else:
                    self.write_msg(event.user_id, f'Не удалось найти подходящу пару.\
                                    Измените параметры профиля или повторите попытку позже')
        else:
            self.write_msg(event.user_id, f'Не удалось обнаружить пользователя и осуществить поиск')

    def get_people_ids(self):
        # функция обрабатывает данные, полученные из функции get_offered_people() и возвращает список
        # кортежей, каждый из которых состоит из id и имени с фамилией найденного человека. Найденные пользователи,
        # с закрытой страницей профиля на попадают в данный список.
        people_ids = []
        for people in self.get_offered_people():
            if people['is_closed'] == False:
                people_info = (people["id"], f'{people["first_name"]} {people["last_name"]}')
                if people_info is not None:
                    people_ids.append(people_info)
        return people_ids

    def get_whole_info(self):
        # функция обрабатывает данные, полученные из функции get_people_ids() и осуществляет поиск трёх
        # самых популярных фотографий профиля у каждого из найденных людей. Возвращает список кортежей,
        # каждый из которых состоит из имени-фамилии найденного человека, ссылке на его/её страницу vk.com
        # и список из трёх самых популярных фотографий профиля, записанных в формате для передачи в метод messages.send
        whole_info = []
        if len(self.get_people_ids()) > 0:
            for couple in self.get_people_ids():
                id_couple = f'https://vk.com/id{vk_client.get_photos(owner_id=str(couple[0]))[1]}'
                all_photos = vk_client.get_photos(owner_id=str(couple[0]))[0]
                if id_couple is None or len(all_photos) < 3:
                    continue
                photos_ids = {}
                for photo in all_photos:
                    photos_ids[(photo["id"])] = photo["comments"]["count"] + photo["likes"][
                        "count"] + photo["likes"]["user_likes"]
                sorted_ids = (sorted(photos_ids.items(), key=lambda x: x[1]))[-3:]
                couple_name = couple[1]
                only_ids = []
                for id in sorted_ids:
                    only_ids.append(f'photo{id_couple[17:]}_{id[0]}')
                info = (couple_name, id_couple, only_ids)
                whole_info.append(info)
            return whole_info

    def run(self):
        # функция запускается после определения пользователя, активирует вышеописанные функции.
        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
                user_id = event.user_id
                request = event.text
                if request.lower() == "поиск" or request.lower() == "search":
                    self.get_offered_people()
                    self.get_people_ids()
                    self.get_whole_info()
                    self.write_msg(user_id, 'Для просмотра результатов введите "показ" ')
                break

    def run_2(self):
        # функция при нажатии "показ" выводит в бота сообщение, состоящее из имени-фамилии пары,
        # ссылки на его/её страницу в вк и три фотографии. При каждом запуске выводятся профили,
        # записанные в список. После завершения списка запускается функция run(), происходит поиск
        # новых профилей и список перезаписывается
        i = 0
        for event in longpoll.listen():
            if i < len(self.get_whole_info()):
                if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
                    request = event.text
                    if request.lower() == "показ" or request.lower() == "show":
                        couple = self.get_whole_info()[i]
                        if couple not in self.shown_couple and couple is not None:
                            self.shown_couple.append(couple)
                            try:
                                self.write_msg(event.user_id, message=f'Ваша пара - {couple[0]}, {couple[1]}',
                                          attachment=f'{couple[2][0]},{couple[2][1]},{couple[2][2]}')
                                user_table_name = f'id{event.user_id}'
                                couple_id = f'{couple[1][15:]}'
                                i += 1
                                if i != len(self.get_whole_info()) - 1:
                                    self.write_msg(event.user_id, 'Для просмотра результатов введите "показ" ')
                                engine = sq.create_engine(DSN)
                                Session = sessionmaker(bind=engine)
                                session = Session()
                                User = create_models(user_table_name)
                                create_table(engine)
                                try:
                                    table_columns = User(id_couple=couple_id, name_couple=couple[0])
                                    session.add(table_columns)
                                    session.commit()
                                except:
                                    pass
                                session.close()

                            except:
                                continue
                        else:
                            pass
            else:
                break
        self.offset += 50
        self.write_msg(event.user_id, 'для продолжения поиска введите "поиск" ')

vk_bot = Bot(bot_token=bot_token)

def run_bot():
    vk_bot.get_user()
    while True:
        vk_bot.run()
        vk_bot.run_2()

run_bot()

