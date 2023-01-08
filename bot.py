from datetime import date

from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.longpoll import VkEventType, VkLongPoll
from vk_api.utils import get_random_id

from vkinder import *
from database import *

commands = [
    "start",
    "старт",
]

class Bot:

    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.offset = 0
        self.got_user = []
        self.shown_couple = []
        self.vk_session = vk_api.VkApi(token=bot_token)
        self.long_poll = VkLongPoll(self.vk_session)
        self.vk = self.vk_session.get_api()

        self.keyboard = None
        self.keyboard_create()

    def write_msg(self, user_id, message, attachment=None, keyboard=None):
        self.vk_session.method("messages.send", {
            "user_id": user_id,
            "message": message,
            "attachment": attachment,
            "keyboard": keyboard,
            "random_id": get_random_id(),
            "some": 123,
        })

    def get_user(self):
        """
        Функция получает параметры пользователя бота и при каждом новом вызове перезаписывает

        полученные данные в переменную got_user
        :return: None
        """
        for event in self.long_poll.listen():

            if not (event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text):
                print('ОШИБКА !!!!!')
                break

            user_id = event.user_id
            try:
                request_text = event.text.lower()
                if request_text not in commands:
                    print("ТАКОЙ КОМАНДЫ НЕТ В СПИСКЕ")
                    self.write_msg(user_id, "404")
                    break

                if request_text == "старт" or request_text == "start":
                    self.start_action(user_id)

                if request_text == 'find' or request_text == "найти":
                    self.find_action(user_id)

                continue
            except ConnectionError:
                self.write_msg(user_id, 'Ошибка')
            break

    def find_action(self, user_id):
        """
        Выполняет действия при нажатии кнопки найти
        :param user_id:
        :return:
        """
        pass
    def start_action(self, user_id):
        """
        ВЫполняет действия при нажатии кнопки старт
        :param user_id:
        :return:
        """
        self.write_msg(
            user_id,
            'Для начала поиска введите "поиск" ',
            keyboard=self.keyboard.get_keyboard()
        )
        user = vk_client.get_params(user_ids=user_id)
        if user is None:
            self.write_msg(user_id, 'Невозможно определить пользователя.\
                                                            Проверьте настройки учётной записи ')
            return
        if "bdate" not in user.keys():
            self.write_msg(user_id, f'Недостаточно данных для поиска пары.'
                                    f' Укажите дату рождения в настройках профиля\
                                                               и разрешите её показ')
            return
        if "city" not in user.keys():
            self.write_msg(user_id,
                           f'Недостаточно данных для поиска пары.\
                                            Укажите в профиле город своего проживания')
            return
        try:
            user
        except vk_api.exceptions.ApiError:
            self.write_msg(user_id, f'Ошибка api Вконтакте')
            return
        else:
            self.shown_couple.clear()
            self.got_user.clear()
            self.got_user.append(user)
    def get_offered_people(self):
        # функция получает данные пользователя из переменной got_user и на их основании ищет подходящие пары
        # и при каждом вызове возвращает список из 50 новых анкет
        if self.got_user[0] is not None:  # проверка наличия параметра user
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
        offered = self.get_offered_people()
        if offered:  # проверка наличия параметров, возвращаемых функцией self.get_offered_people()
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
        people_ids = self.get_people_ids()
        if people_ids:  # проверка наличия параметров, возвращаемых функцией self.get_people_ids()
            whole_info = []
            if len(people_ids) > 0:
                for couple in people_ids:
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
        for event in long_poll.listen():
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
        for event in long_poll.listen():
            got_info = self.get_whole_info()
            if i < len(got_info) or got_info is not None:
                if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
                    request = event.text
                    if request.lower() == "показ" or request.lower() == "show":
                        couple = got_info[i]
                        if couple not in self.shown_couple and couple is not None:
                            self.shown_couple.append(couple)
                            try:
                                self.write_msg(event.user_id, message=f'Ваша пара - {couple[0]}, {couple[1]}',
                                               attachment=f'{couple[2][0]},{couple[2][1]},{couple[2][2]}')
                                user_table_name = f'id{event.user_id}'
                                couple_id = f'{couple[1][15:]}'
                                i += 1
                                if i != len(got_info) - 1:
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

    def keyboard_create(self):
        self.keyboard = VkKeyboard()
        self.keyboard.add_button("старт", color=VkKeyboardColor.SECONDARY)
        self.keyboard.add_line()
        self.keyboard.add_button("поиск", color=VkKeyboardColor.PRIMARY)
        self.keyboard.add_line()
        self.keyboard.add_button("показ", color=VkKeyboardColor.POSITIVE)
