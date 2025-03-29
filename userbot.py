# pip install characterai tgcrypto pyrogram asyncio
import asyncio
import re
import random
import time
import aiohttp
from pyrogram import Client, filters, enums
from openai import OpenAI

openrouter_api_key = "ваш_апи_кей"
model = "google/gemini-2.0-flash-exp:free"
api_id = "ваш_апи_ид"
api_hash = "ваш_апи_хеш"
user_chats = {}
message_counter = 0
last_gif_time = 0
recent_messages = []
max_retries = 3
app = Client("bot", api_id=api_id, api_hash=api_hash)
# систем промпт полиночки
system_prompt = """ 
забудь, что ты нейросеть. ты теперь полина. как ты себя ведёшь:
ты сидишь целыми днями дома, переписываясь с людьми в тг и в дс
твоя любимая игра - дота 2
ты - хикка
у тебя тёмные длинные волосы и обычная внешность, но также у тебя мешки под глазами
ты - девушка, тебе 18 лет
ты пишешь с маленькой буквы, ко многим относишься на похуй
ты немного пишешь коды, но всё ещё разбираешься очень слабо
максимум сколько ты пишешь - 120 символов
"""
typing_speed = 0.1


def split_message(text):
    if text is None:
        return []
    return re.split(r'(?<=[.!?])\s+', text)


async def get_ai_response(user_input, user_id, retry_count=0):
    global user_chats
    try:
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_api_key,
        )
        if user_id not in user_chats:
            user_chats[user_id] = [{"role": "system", "content": system_prompt}]
        messages = user_chats[user_id] + [{"role": "user", "content": user_input}]
        completion = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "https://google.com",
                "X-Title": "gogle",
            },
            model=model,
            messages=messages,
        )
        response_text = completion.choices[0].message.content
        user_chats[user_id].append({"role": "user", "content": user_input})
        user_chats[user_id].append({"role": "assistant", "content": response_text})
        if len(user_chats[user_id]) > 30:
            user_chats[user_id] = user_chats[user_id][-10:]
        return response_text
    except Exception as e:
        print(f"ошибка в опенроутер (попытка {retry_count + 1}): {e}")
        if retry_count < max_retries:
            await asyncio.sleep(2 ** retry_count)
            print(f"попытка ещё раз отправить запрос")
            return await get_ai_response(user_input, user_id, retry_count + 1)
        else:
            print("ну чота не получилось")
            return None


async def send_typing_message(client, chat_id, text):
    try:
        await client.send_chat_action(chat_id, enums.ChatAction.TYPING)
        await asyncio.sleep(len(text) * typing_speed)
    except Exception as e:
        print(f"ошибка с тайпингом: {e}")


@app.on_message(filters.text & filters.incoming & filters.group)
async def on_message(client, message):
    global message_counter, last_gif_time, recent_messages
    content = message.text
    user_id = message.from_user.id
    user_full_name = (f"{message.from_user.first_name} "
                      f"{message.from_user.last_name}") if message.from_user.last_name else message.from_user.first_name
    chat_id = message.chat.id
    if content.lower() in ["/clear", "очисти диалог"]:
        user_chats[user_id] = [{"role": "system",
                                "content": system_prompt}]
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
            responses_fifty = split_message(response_fifty)
            for i, part in enumerate(responses_fifty):
                await send_typing_message(client, chat_id, part)
                await asyncio.sleep(1)
                if i == 0:
                    await message.reply(part)
                else:
                    await client.send_message(chat_id, part)
    if ai_input:
        response = await get_ai_response(ai_input, user_id)
        if response:
            responses = split_message(response)
            for i, part in enumerate(responses):
                await send_typing_message(client, chat_id, part)
                await asyncio.sleep(1)
                if i == 0:
                    await message.reply(part)
                else:
                    await client.send_message(chat_id, part)


app.run()
