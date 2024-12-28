import discord
from discord.ext import commands
import asyncio
import re
from characterai import aiocai
import time
import requests
import random

ds_token = "добавьте сюда токен ПОЛЬЗОВАТЕЛЯ дс"
cai_token = "введите сюда токен (его можно взять здесь: https://docs.kram.cat/auth.html)"
caichat_id = "3b9jNbV9sxbILv6uGzqw-YyUIPHX06mSAR61Dk5bzPo"
user_chats = {}
message_counter = 0
last_gif_time = 0
gif_cd = 60


def get_gif_links():
    url = "https://raw.githubusercontent.com/Telery-Userbot/BD_Telery/refs/heads/main/komarugifbd"
    try:
        response = requests.get(url)
        response.raise_for_status()
        gif_links = response.text.splitlines() 
        return gif_links
    except requests.RequestException as e:
        print(f"Ошибка при получении гифок: {e}")
        return []
gif_links = get_gif_links()


async def get_ai_response(user_input, user_id):
    client = aiocai.Client(cai_token)
    me = await client.get_me()
    if user_id not in user_chats or user_chats[user_id] is None:
        async with await client.connect() as chat:
            new, _ = await chat.new_chat(caichat_id, me.id)
            user_chats[user_id] = new.chat_id
    chat_id = user_chats[user_id]
    async with await client.connect() as chat:
        message = await chat.send_message(caichat_id, chat_id, user_input)
        return message


def split_message(text):
    return re.split(r'(?<=[.!?])\s+', text)

def find_emojis(text):
    emoji_pattern = re.compile(
        r'['
        r'\U0001F600-\U0001F64F'  
        r'\U0001F300-\U0001F5FF'  
        r'\U0001F680-\U0001F6FF'  
        r'\U0001F1E0-\U0001F1FF'  
        r'\U00002700-\U000027BF'  
        r'\U0001F900-\U0001F9FF'  
        r'\U00002600-\U000026FF'  
        r'\U00002B50-\U00002BFF'  
        r'\U0001F780-\U0001F7FF' 
        r']+', flags=re.UNICODE)
    return emoji_pattern.findall(text)

bot = commands.Bot(command_prefix="!", self_bot=True)


@bot.event
async def on_message(message):
    global message_counter, last_gif_time
    if message.author.id == bot.user.id:
        return
    bot_mention = f"<@{bot.user.id}>"
    is_mention = bot_mention in message.content
    is_reply = message.reference and message.reference.resolved.author.id == bot.user.id
    if is_mention or is_reply:
        user_input = message.content.replace(bot_mention, "").strip()
        if user_input.lower() in ["/clear", "очисти диалог"]:
            user_chats[message.author.id] = None
            await message.reply("Диалог очищен.")
            return
        if user_input.lower() in ["/regen", "перегенерируй"]:
            response = await get_ai_response(user_input, message.author.id)
            await message.reply(response.text)
            return
        message_counter += 1
        response = await get_ai_response(user_input, message.author.id)
        responses = split_message(response.text)
        for part in responses:
            typing_duration = min(max(1, len(part) // 10), 5)
            async with message.channel.typing():
                await asyncio.sleep(typing_duration)
            await message.reply(part)
        emojis = find_emojis(response.text)
        for emoji in emojis:
            try:
                await message.add_reaction(emoji)
            except discord.HTTPException:
                pass
        if hasattr(response, 'attachments'):
            if response.attachments:
                for attachment in response.attachments:
                    await message.channel.send(f"Image: {attachment['url']}")
        current_time = time.time()
        if current_time - last_gif_time >= gif_cd:
            last_gif_time = current_time
            if gif_links:
                gif_url = random.choice(gif_links)
                time.sleep(1)
                await message.channel.send(gif_url)

bot.run(ds_token)
