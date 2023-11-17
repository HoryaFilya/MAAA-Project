import config
import re
import requests
import tempfile
import os
from fake_useragent import UserAgent
from aiogram import Bot, types, Dispatcher, executor
from aiogram.types import (KeyboardButton, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telethon import TelegramClient
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.functions.messages import GetHistoryRequest
from aiogram.dispatcher.filters import Command, CommandStart, CommandHelp, CommandSettings, Regexp
from fake_useragent import UserAgent
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from telethon.tl.types import InputPeerEmpty

bot = Bot(token=config.bot_token)
dp = Dispatcher(bot, storage=MemoryStorage())

phone = config.phone
api_id = config.api_id
api_hash = config.api_hash

# Ожидание ввода данных(номер, код)
#
class Registration(StatesGroup):
    awaiting_phone = State()
    awaiting_code = State()

#
# Создание начальной клавиатуры
#

async def main_menu():
    markup = types.reply_keyboard.ReplyKeyboardMarkup(row_width=2,resize_keyboard=True)
    btn1 = types.KeyboardButton('Спарсить данные из открытого канала')
    btn2 = types.KeyboardButton('Спарсить данные из закрытого канала')
    btn3 = types.KeyboardButton('Фото котиков')
    markup.add(btn1, btn2, btn3)
    return markup

@dp.message_handler(Command("start"), state="*") # Начало
async def start_message(message):
    text = (f'Привет {message.from_user.first_name}, я бот парсер информации.'
            'Выберите, что вы хотите из кнопок ниже:')
    markup = await main_menu()
    await message.answer(text, reply_markup=markup)

#
# Открытый канал
#


@dp.message_handler(regexp='Спарсить данные из открытого канала')
async def parsing_open_chanel(message):
    text = 'Укажите ссылку на канал в формате: https://t.me/alishev_g'
    await message.answer(text, reply_markup=ReplyKeyboardRemove())

#
# Закрытый канал
#

@dp.message_handler(regexp='Спарсить данные из закрытого канала')
async def parser_closed_chanel(message):
    markup = types.reply_keyboard.ReplyKeyboardMarkup(row_width=2,resize_keyboard=True)
    btn1 = types.KeyboardButton('Меню')
    markup.add(btn1)
    
    await Registration.awaiting_phone.set()
    await message.reply("Для парсинга нужно пройти регистрацию. \n\nВведите ваш номер телефона в формате +79089001234")

@dp.message_handler(Regexp(r'^\+\d{11}$'), state=Registration.awaiting_phone)
async def get_user_phone(message: types.Message, state: FSMContext):
    phone = message.text
    headers = {
        'user-agent': UserAgent().random
    }

    payload = {
        'phone': phone
    }

    response = requests.post('https://my.telegram.org/auth/send_password', headers=headers, params=payload)
    random_hash = response.json()['random_hash']

    await message.reply("Пожалуйста, введите код, полученный в Telegram.")
    await state.update_data(phone=phone, random_hash=random_hash, headers=headers)
    await Registration.awaiting_code.set()

@dp.message_handler(Regexp(r'^[A-Za-z0-9_]{11}$'), state=Registration.awaiting_code)
async def get_user_code(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        phone = data['phone']
        random_hash = data['random_hash']
        headers = data['headers']

    password = message.text

    payload = {
        'phone': phone, 
        'random_hash': random_hash, 
        'password': password
    }

    response = requests.post('https://my.telegram.org/auth/login', headers=headers, params=payload)
    cookie = response.headers['Set-Cookie'].split(";")[0]

        # Отправляем cookies (из прошлого запроса) -> понимаем, зареган или нет
    headers2 = {
        'user-agent': UserAgent().random, 
        'Cookie': cookie
    }

    response = requests.get('https://my.telegram.org/apps', headers=headers2)
    content = str(response.content)

    #
    # Логика, если пользователь зарегистрирован
    #
    if content.find('onclick="this.select();">') != -1:
        indexStartForId = content.find('onclick="this.select();">') + 33
        indexStopForId = content.find('</span>') - 9
        id = content[indexStartForId:indexStopForId:]

        content = content[indexStopForId::]

        indexStartForHash = content.find('onclick="this.select();">') + 25
        indexStopForHash = indexStartForHash + 80
        hash = re.search(r"([a-z0-9]+)", content[indexStartForHash:indexStopForHash:]).group(1)
    #
    # Логика, если пользователь НЕ зарегистрирован
    #
    else:
        indexStart = content.find('name="hash" value="') + 19
        indexStop = indexStart + 20
        hash = re.search(r"([a-z0-9]+)", content[indexStart:indexStop:]).group(1)

        headers = {
            'user-agent': UserAgent().random,
            'Cookie': cookie
        }

        payload = {
            "hash": hash,
            "app_title": "TestSearchMessage",
            "app_shortname": "TestSearch",
            "app_url": "",
            "app_platform": "android",
            "app_desc": ""
        }

        response = requests.post('https://my.telegram.org/apps/create', headers=headers, params=payload)

        headers = {
            'user-agent': UserAgent().random, 
            'Cookie': cookie
        }

        response = requests.get('https://my.telegram.org/apps', headers=headers)
        content = str(response.content)

        indexStartForId = content.find('onclick="this.select();">') + 33
        indexStopForId = content.find('</span>') - 9
        id = content[indexStartForId:indexStopForId:]

        content = content[indexStopForId::]

        indexStartForHash = content.find('onclick="this.select();">') + 25
        indexStopForHash = indexStartForHash + 80
        hash = re.search(r"([a-z0-9]+)", content[indexStartForHash:indexStopForHash:]).group(1)

    api_id = id
    api_hash = hash
    text = f'API ID: {api_id}\nAPI Hash: {api_hash}'
    await message.answer(text)
   


# #
# # Вход из под аккаунта пользователя
# #

# client = TelegramClient(phone, api_id, api_hash)

# client.start(phone=phone)

# chats = []
# last_date = None
# chunk_size = 200
# groups=[]
# result = client(GetDialogsRequest(
#             offset_date=last_date,
#             offset_id=0,
#             offset_peer=InputPeerEmpty(),
#             limit=chunk_size,
#             hash = 0
#         ))
# chats.extend(result.chats)

# for chat in chats:
#     groups.append(chat)

# povtor = ["Unsupported Chat"]

# for i in range(len(groups)):
#     if i == len(groups) - 1:
#         break
#     if groups[i].title == groups[i + 1].title:
#         povtor.append(groups[i].title)

# for i in groups:
#     if i.title in povtor:
#         groups.remove(i)

# print("Выберите группу для парсинга сообщений:")

# i = 0

# for g in groups:
#    print(str(i) + "- " + g.title)
#    i += 1

# g_index = input("Введите нужную цифру: ")
# target_group=groups[int(g_index)]

# offset_id = 0
# limit = 1
# all_messages = []
# total_messages = 0
# total_count_limit = 10

# while True:
#    history = client(GetHistoryRequest(
#        peer=target_group,
#        offset_id=offset_id,
#        offset_date=None,
#        add_offset=0,
#        limit=limit,
#        max_id=0,
#        min_id=0,
#        hash=0
#    ))

#    if not history.messages:
#        break

#    messages = history.messages

#    for message in messages:
#        all_messages.append(message.message)

#    total_messages += 1
#    offset_id = messages[len(messages) - 1].id

#    if total_count_limit != 0 and total_messages >= total_count_limit:
#        break

# for message in all_messages[::-1]:
#     print(message)


@dp.message_handler(regexp='Меню')
async def start_message(message: types.Message):
    markup = await main_menu()
    text = (f'{message.from_user.first_name}, я бот парсер информации.'
            'Выберите, что вы хотите из кнопок ниже:')
    await message.answer(text, reply_markup=markup)

#@dp.message_handler() #Создаём новое событие, которое запускается в ответ на любой текст, введённый пользователем.
#async def echo(message: types.Message): #Создаём функцию с простой задачей — отправить обратно тот же текст, что ввёл пользователь.
#   await message.answer(message.text)

@dp.message_handler(commands=['stop'])
async def stop(message: types.Message):
    await message.reply("Бот отключен.")

@dp.message_handler()
async def process_channel_link(message: types.Message):
    channel_link = message.text

    async with TelegramClient(phone, api_id, api_hash) as client:
        try:
            entity = await client.get_entity(channel_link)
            match = re.search(r"title='([^']+)'", str(entity))
            await client(JoinChannelRequest(entity))
            print(f"Успешно вступил в канал {channel_link}")
        except Exception as e:
            print(f"Ошибка: {e}")

    if match:
        channel_name = match.group(1)
        await get_channel_messages(channel_name, message)

async def get_channel_messages(channel_name, message: types.Message):
    async with TelegramClient(phone, api_id, api_hash) as client:
        try:
            dialogs = await client(GetDialogsRequest(
                offset_date=None,
                offset_id=0,
                offset_peer=InputPeerEmpty(),
                limit=200,
                hash=0
            ))

            chats = dialogs.chats

            groups = None
            for chat in chats:
                match = re.search(r"title='([^']+)'", str(chat))

                if match:
                    title_value = match.group(1)

                    if channel_name == title_value:
                        groups = chat
                        break

            if groups is None:
                raise ValueError(f"Channel {channel_name} not found.")

            limit = 100
            all_messages = []

            history = await client(GetHistoryRequest(
                peer=groups,
                offset_id=0,
                offset_date=None,
                add_offset=0,
                limit=limit,
                max_id=0,
                min_id=0,
                hash=0
            ))

            messages = history.messages

            for messageUser in messages:
                if messageUser.message is not None:
                    all_messages.append(messageUser.message)

            all_messages.reverse()

            if message.chat is not None:
                response = "\n".join(all_messages)

                with tempfile.NamedTemporaryFile(mode='w+', delete=False, encoding='utf-8', prefix='response_file_') as temp_file:
                    temp_file.write(response)
                    temp_file_path = temp_file.name

                with open(temp_file_path, 'rb') as file:
                    await bot.send_document(message.chat.id, file)

                os.remove(temp_file_path)

        except Exception as e:
            markup = types.reply_keyboard.ReplyKeyboardMarkup(row_width=2,resize_keyboard=True)
            btn1 = types.KeyboardButton('Меню')
            markup.add(btn1)
            await bot.send_message(message.chat.id, "Something went wrong.", reply_markup=markup )

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)