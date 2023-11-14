from telethon.sync import TelegramClient
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty
from telethon.tl.functions.messages import GetHistoryRequest

import re

global_title_value = None
phone = ""
api_id = ''
api_hash = ''

channel_link = input("Укажите ссылку на канал в формате: https://t.me/alishev_g")

client = TelegramClient(phone, api_id, api_hash)

async def join_channel():
    global global_title_value

    await client.start(phone=phone)
    try:
        entity = await client.get_entity(channel_link)

        match = re.search(r"title='([^']+)'", str(entity))

        if match:
            global_title_value = match.group(1)
        else:
            print("Значение title не найдено в строке.")

        await client(JoinChannelRequest(entity))
        print(f"Успешно вступил в канал {channel_link}")

    except Exception as e:
        print(f"Ошибка: {e}")

client.loop.run_until_complete(join_channel())


chats = []
last_date = None
chunk_size = 200
groups = ""
result = client(GetDialogsRequest(
    offset_date=last_date,
    offset_id=0,
    offset_peer=InputPeerEmpty(),
    limit=chunk_size,
    hash=0
))
chats.extend(result.chats)

for chat in chats:
    match = re.search(r"title='([^']+)'", str(chat))

    if match:
        title_value = match.group(1)

        if global_title_value == title_value:
            groups = chat
            break

offset_id = 0
limit = 1
all_messages = []
total_messages = 0
total_count_limit = 10

while True:
    history = client(GetHistoryRequest(
        peer=groups,
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

async def disconnect():
    await client.disconnect()

client.loop.run_until_complete(disconnect())