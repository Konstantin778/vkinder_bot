import sqlalchemy as sq
from sqlalchemy.orm import declarative_base, sessionmaker
import psycopg2
from pprint import pprint
import datetime
from datetime import date
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
import random
from random import randrange
from vkinder import *

with open("token_bot.txt", "r") as file:
    bot_token = file.read().strip()

DSN = "postgresql://student:1@localhost:5432/homeworks"
Base = declarative_base()

while True:
        vk_session = vk_api.VkApi(token=bot_token)
        longpoll = VkLongPoll(vk_session)
        vk = vk_session.get_api()
        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
                request = event.text
                if request.lower() == "поиск" or request.lower() == "search":
                    user_id = event.user_id
                    # Получение списка параметров пользователя в переменную user
                    user = (vk_client.get_params(user_ids=user_id, fields="bdate, city, sex, relation")["response"][0])
                    # Если в анкете не указана дата рождения, то бот попросит её добавить
                    if "bdate" not in user.keys():
                        vk.messages.send(user_id=event.user_id, random_id=get_random_id(),
                                         message=f'Недостаточно данных для поиска пары.'
                                                 f' Укажите дату рождения в настройках профиля и разрешите её показ')
                        continue
                    # Если в анкете не указан город проживания, то бот попросит его добавить
                    if "city" not in user.keys():
                        vk.messages.send(user_id=event.user_id, random_id=get_random_id(),
                                         message=f'Недостаточно данных для поиска пары. Укажите в профиле город своего проживания')
                        continue
                    # получение отдельных параметров из переменной user и использование их для поиска людей search_people с закреплением списка подходящих людей в переменной offered_people
                    def get_age():
                        birth_year = int(user["bdate"][-4:])
                        current_year = date.today().year
                        return current_year - birth_year

                    def put_sex():
                        sex = 0
                        if user["sex"] == 1:
                            sex += 2
                        else:
                            sex += 1
                        return sex

                    user_city = user["city"]["id"]
                    relation = user["relation"]

                    offered_people = vk_client.search_people(get_age()-1, get_age()+1, put_sex(), user_city, relation)

                    people_ids = [] # Получение списка id с именами и фамилиями найденных людей.
                    for people in offered_people:
                        if people['is_closed'] == False:
                            people_info = (people["id"], f'{people["first_name"]} {people["last_name"]}')
                            people_ids.append(people_info)

                    random_couple = (random.choice(people_ids)) # выбор случайного человека из списка найденных людей
                    all_photos = vk_client.get_photos(owner_id = str(random_couple[0]))[0] #получение списка фотографий профиля предложенного человека

                    def get_id_your_couple(): # получение id предложенного человека
                        return f'https://vk.com/id{vk_client.get_photos(owner_id = str(random_couple[0]))[1]}'

                    def get_links(): # получение списка из id трёх самых популярных фотографий профиля предложенного человека и запись их в формате attachments для метода messages.send в vk.api
                        photos_ids = {}
                        if len(all_photos) >= 3:
                            for photo in all_photos:
                                photos_ids[(photo["id"])] = photo["comments"]["count"] + photo["likes"]["count"] + \
                                                                     photo["likes"]["user_likes"]
                            sorted_ids = (sorted(photos_ids.items(), key=lambda x: x[1]))[-3:]
                            only_ids = []
                            for id in sorted_ids:
                                only_ids.append(f'photo{get_id_your_couple()[17:]}_{id[0]}')
                            return only_ids

                    best_photos_ids = get_links()
                    try:
                        vk.messages.send(
                            user_id=event.user_id,
                            random_id=get_random_id(),
                            message=f'Ваша пара - {random_couple[1]}, {get_id_your_couple()}',
                            attachment=f'{best_photos_ids[0]},{best_photos_ids[1]},{best_photos_ids[2]}')
                    except:
                        vk.messages.send(
                            user_id=event.user_id,
                            random_id=get_random_id(),
                            message=f'повторите поиск')
                        continue

                    # обозначение переменных для занесение в таблицу в базе данных
                    user_table_name = f'id{user_id}' # наименование таблицы для каждого пользователя бота
                    couple_id = f'id{vk_client.get_photos(owner_id=str(random_couple[0]))[1]}' #id предложенной пары для использования в качестве primary key

                    class User(Base):
                        __tablename__ = user_table_name
                        __table_args__ = {"schema": "vkinder_database", 'extend_existing': True}

                        id_couple = sq.Column(sq.String(length=15), primary_key=True, unique=True)
                        name_couple = sq.Column(sq.String(length=40))

                    def create_table(engine):
                        Base.metadata.create_all(engine)

                    engine = sq.create_engine(DSN)
                    Session = sessionmaker(bind=engine)
                    session = Session()
                    create_table(engine)
                    try:
                        table_columns = User(id_couple=couple_id, name_couple=random_couple[1])
                        session.add(table_columns)
                        session.commit()
                    except:
                        pass

                    session.close()




