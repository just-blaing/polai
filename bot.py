import asyncio
import re
import disnake
from disnake.ext import commands
from characterai import aiocai
import random

discord_token = "тыкните сюда токен бота дс"
cai_token = "тыкните сюда токен чарактер аи (его можно взять здесь: https://docs.kram.cat/auth.html)"
id = "3b9jNbV9sxbILv6uGzqw-YyUIPHX06mSAR61Dk5bzPo"
user_chats = {}
message_counter = 0
intents = disnake.Intents.all()
bot = commands.Bot(command_prefix="/", intents=intents)


async def get_ai_response(user_input, user_id):
    client = aiocai.Client(cai_token)
    me = await client.get_me()
    if user_id not in user_chats or user_chats[user_id] is None:
        async with await client.connect() as chat:
            new, _ = await chat.new_chat(id, me.id)
            user_chats[user_id] = new.chat_id
    chat_id = user_chats[user_id]
    async with await client.connect() as chat:
        message = await chat.send_message(id, chat_id, user_input)
        return message


def split_message(text):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    parts = []
    current_part = ""
    for sentence in sentences:
        if len(current_part) + len(sentence) + 1 > 200:
            parts.append(current_part.strip())
            current_part = sentence
        else:
            current_part += " " + sentence
    if current_part:
        parts.append(current_part.strip())
    return parts


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


@bot.slash_command(description="Очистить диалог")
async def clear(interaction: disnake.AppCmdInter):
    user_id = interaction.author.id
    user_chats[user_id] = None
    await interaction.send("Диалог очищен.")


@bot.event
async def on_message(message):
    global message_counter
    if message.author == bot.user:
        return
    bot_mention = f"<@{bot.user.id}>"
    user_id = message.author.id
    is_mention = bot_mention in message.content
    is_reply = message.reference and message.reference.resolved.author == bot.user
    contains_keywords = re.search(r"\bполина\b|\bполиночка\b", message.content, re.IGNORECASE)
    if is_mention or is_reply or contains_keywords:
        user_input = message.content.replace(bot_mention, "").strip()
        if is_reply:
            original_message = message.reference.resolved
            user_input = f'{message.author.name} ответил на ваше сообщение "{original_message.content}": {user_input}'
        message_counter += 1
        async with message.channel.typing():
            await asyncio.sleep(random.uniform(1, 3))
        response = await get_ai_response(user_input, user_id)
        response_text = response.text
        emojis = find_emojis(response_text)
        for emoji in emojis:
            response_text = response_text.replace(emoji, '')
        responses = split_message(response_text)
        num_messages = random.randint(1, 30)
        responses = responses[:num_messages]
        first_message = True
        emoji_used = False
        for part in responses:
            typing_duration = min(max(1, len(part) // 10), 5)
            async with message.channel.typing():
                await asyncio.sleep(typing_duration)
            if first_message:
                await message.reply(part)
                first_message = False
            else:
                await message.channel.send(part)
        if emojis and not emoji_used:
            await message.channel.send(emojis[0])
            emoji_used = True
        for emoji in emojis:
            try:
                await message.add_reaction(emoji)
            except disnake.HTTPException:
                print(f"не удалось добавить реакцию с эмодзи {emoji}")


bot.run(discord_token)
