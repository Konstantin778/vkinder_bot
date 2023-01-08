from vk_api.longpoll import VkLongPoll
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

from bot import Bot
from vkinder import *



with open("token_bot.txt", "r") as file:
    bot_token = file.read().strip()


vk_bot = Bot(bot_token=bot_token)


def run_bot():
    vk_bot.get_user()
    while True:
        vk_bot.run()
        vk_bot.run_2()


run_bot()
