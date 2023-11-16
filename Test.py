from aiogram import Bot, Dispatcher, types
from telethon import TelegramClient
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.types import InputPeerEmpty

import re
import os
import tempfile
import config


phone = config.PHONE
api_id = config.API_ID
api_hash = config.API_HASH
token = config.TOKEN


bot = Bot(token=token)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.reply("Привет! Укажите ссылку на канал в формате: https://t.me/alishev_g")

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
            await bot.send_message(message.chat.id, "Something went wrong.")


if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)