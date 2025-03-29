# pip install characterai tgcrypto pyrogram asyncio
import asyncio
import re
import random
import time
from characterai import aiocai
from pyrogram import Client, filters, enums
import tgcrypto
import aiohttp

# https://docs.kram.cat/auth.html
cai_token = "ваш_чарактер_аи_токен"
chat_id_characterai = "3b9jNbV9sxbILv6uGzqw-YyUIPHX06mSAR61Dk5bzPo"
# кстати всё ещё не понимаю зачем для ботов задавать апи ид и апи хеш
api_id = "ваш_апи_ид"
api_hash = "ваш_апи_хеш"
user_chats = {}
message_counter = 0
last_gif_time = 0
# вы можете задать сами кд для гифок если очень хотите
gif_cooldown = 60
recent_messages = []
url_gif = "https://raw.githubusercontent.com/Telery-Userbot/BD_Telery/refs/heads/main/komarugifbd"


async def get_random_gif():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url_gif, timeout=10) as response:
                if response.status == 200:
                    gif_list = await response.text()
                    gifs = gif_list.strip().split('\n')
                    valid_gifs = [gif for i, gif in enumerate(gifs) if i % 2 == 0]
                    if valid_gifs:
                        return random.choice(valid_gifs)
                    else:
                        print("Список GIF пуст или не соответствует ожидаемому формату.")
                        return None
                else:
                    print(f"Ошибка при получении GIF: {response.status}")
                    return None
    except aiohttp.ClientError as e:
        print(f"Ошибка соединения при получении GIF: {e}")
        return None
    except asyncio.TimeoutError:
        print("Превышено время ожидания при получении GIF")
        return None


async def get_ai_response(user_input, user_id):
    try:
        client = aiocai.Client(cai_token)
        me = await client.get_me()
        if user_id not in user_chats or user_chats[user_id] is None:
            async with await client.connect() as chat:
                new, _ = await chat.new_chat(chat_id_characterai, me.id)
                user_chats[user_id] = new.chat_id
        chat_id = user_chats[user_id]
        async with await client.connect() as chat:
            message = await chat.send_message(chat_id_characterai, chat_id, user_input)
            return message
    except Exception as e:
        print({e})
        return None


def split_message(text):
    return re.split(r'(?<=[.!?])\s+', text)


app = Client("bot", api_id=api_id, api_hash=api_hash)


@app.on_message(filters.text & filters.incoming & filters.group)
async def on_message(client, message):
    global message_counter, last_gif_time, recent_messages
    content = message.text
    user_id = message.from_user.id
    user_full_name = (f"{message.from_user.first_name} "
                      f"{message.from_user.last_name}") if message.from_user.last_name else message.from_user.first_name
    chat_id = message.chat.id
    if content.lower() in ["/clear", "очисти диалог"]:
        user_chats[user_id] = None
        await message.reply("Диалог очищен.")
        return
    recent_messages.append((user_full_name, content))
    if len(recent_messages) > 50:
        recent_messages.pop(0)
    if message.reply_to_message and message.reply_to_message.from_user.id == client.me.id:
        ai_input = f"{user_full_name} ответил на ваше сообщение \"{message.reply_to_message.text}\" так:\n\"{content}\""
    elif "полина" in content.lower() or "полиночка" in content.lower() or "polina" in content.lower():
        ai_input = f"{user_full_name} написал вам:\n\"{content}\""
    else:
        ai_input = None
    message_counter += 1
    if message_counter % 50 == 0 and recent_messages:
        random_user, random_message = random.choice(recent_messages)
        fifty_message_input = f"{random_user} написал вам:\n\"{random_message}\""
        response_fifty = await get_ai_response(fifty_message_input, user_id)
        if response_fifty:
            responses_fifty = split_message(response_fifty.text)
            for i, part in enumerate(responses_fifty):
                typing_duration = min(max(1, len(part) // 10), 5)
                await asyncio.sleep(typing_duration)
                if i == 0:
                    await message.reply(part)
                else:
                    await client.send_message(chat_id, part)
    if ai_input:
        response = await get_ai_response(ai_input, user_id)
        if response:
            responses = split_message(response.text)
            for i, part in enumerate(responses):
                typing_duration = min(max(1, len(part) // 10), 5)
                await asyncio.sleep(typing_duration)
                if i == 0:
                    await message.reply(part)
                else:
                    await client.send_message(chat_id, part)
    current_time = time.time()
    if current_time - last_gif_time > gif_cooldown:
        gif_url = await get_random_gif()
        if gif_url:
            try:
                await client.send_animation(chat_id, gif_url)
                last_gif_time = current_time
            except Exception as e:
                print({e})


app.run()
