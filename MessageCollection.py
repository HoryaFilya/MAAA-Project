from fake_useragent import UserAgent
from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty
from telethon.tl.functions.messages import GetHistoryRequest

import requests
import re


phone = input("Введите телефон в формате +79089001234:")

headers = {
    'user-agent': UserAgent().random
}

payload = {
    'phone': phone
}

            # Отправляем номер телефона (берем у пользователя) -> получаем random_hash
responce = requests.post('https://my.telegram.org/auth/send_password', headers=headers, params=payload)
random_hash = responce.json()['random_hash']


            # Отправляем random_hash (из прошлого запроса) и password (берем у пользователя) -> получаем cookies
password = input("Введите пришедший в TG код:")

payload = {
    'phone': phone,
    'random_hash': random_hash,
    'password': password
}

responce = requests.post('https://my.telegram.org/auth/login', headers=headers, params=payload)
cookie = responce.headers['Set-Cookie'].split(";")[0]


            # Отправляем cookies (из прошлого запроса) -> понимаем, зареган или нет
headers2 = {
    'user-agent': UserAgent().random,
    'Cookie': cookie
}

responce = requests.get('https://my.telegram.org/apps', headers=headers2)
content = str(responce.content)


            # ЕСЛИ ЗАРЕГАН:
if content.find('onclick="this.select();">') != -1:
    indexStartForId = content.find('onclick="this.select();">') + 33
    indexStopForId = content.find('</span>') - 9
    id = content[indexStartForId:indexStopForId:]

    content = content[indexStopForId::]

    indexStartForHash = content.find('onclick="this.select();">') + 25
    indexStopForHash = indexStartForHash + 80
    hash = re.search(r"([a-z0-9]+)", content[indexStartForHash:indexStopForHash:]).group(1)

            # ЕСЛИ НЕ ЗАРЕГАН:
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

    responce = requests.post('https://my.telegram.org/apps/create', headers=headers, params=payload)


    headers = {
        'user-agent': UserAgent().random,
        'Cookie': cookie
    }

    responce = requests.get('https://my.telegram.org/apps', headers=headers)
    content = str(responce.content)

    indexStartForId = content.find('onclick="this.select();">') + 33
    indexStopForId = content.find('</span>') - 9
    id = content[indexStartForId:indexStopForId:]

    content = content[indexStopForId::]

    indexStartForHash = content.find('onclick="this.select();">') + 25
    indexStopForHash = indexStartForHash + 80
    hash = re.search(r"([a-z0-9]+)", content[indexStartForHash:indexStopForHash:]).group(1)


api_id = id
api_hash = hash

client = TelegramClient(phone, api_id, api_hash)

client.start(phone=phone)

chats = []
last_date = None
chunk_size = 200
groups=[]
result = client(GetDialogsRequest(
            offset_date=last_date,
            offset_id=0,
            offset_peer=InputPeerEmpty(),
            limit=chunk_size,
            hash = 0
        ))
chats.extend(result.chats)

for chat in chats:
    groups.append(chat)

povtor = ["Unsupported Chat"]

for i in range(len(groups)):
    if i == len(groups) - 1:
        break
    if groups[i].title == groups[i + 1].title:
        povtor.append(groups[i].title)

for i in groups:
    if i.title in povtor:
        groups.remove(i)

print("Выберите группу для парсинга сообщений:")

i = 0

for g in groups:
   print(str(i) + "- " + g.title)
   i += 1

g_index = input("Введите нужную цифру: ")
target_group=groups[int(g_index)]

offset_id = 0
limit = 1
all_messages = []
total_messages = 0
total_count_limit = 10

while True:
   history = client(GetHistoryRequest(
       peer=target_group,
       offset_id=offset_id,
       offset_date=None,
       add_offset=0,
       limit=limit,
       max_id=0,
       min_id=0,
       hash=0
   ))

   if not history.messages:
       break

   messages = history.messages

   for message in messages:
       all_messages.append(message.message)

   total_messages += 1
   offset_id = messages[len(messages) - 1].id

   if total_count_limit != 0 and total_messages >= total_count_limit:
       break

for message in all_messages[::-1]:
    print(message)