import os
import re
import discord
import asyncio
from discord.ext import commands
from llama_cpp import Llama

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

token = os.getenv("DISCORD_TOKEN")
if not token:
    raise ValueError("DISCORD_TOKEN environment variable is not set.")

MODEL_PATH = "C:/Users/swanl/Documents/AI/text-generation-webui/user_data/models/"
MODEL_NAME = "L3-8B-Stheno-v3.2-Q4_K_M.gguf"

llm = Llama(model_path=MODEL_PATH + MODEL_NAME, n_ctx=2048, n_gpu_layers=32, n_batch=512)

CHARACTER_PROMPT = open("character_prompt.txt", "r", encoding="utf-8").read()

@bot.event
async def on_message(message):
    if bot.user in message.mentions and not message.author.bot:
        async with message.channel.typing():
            # Récupère les 10 derniers messages (hors bots)
            messages = [
                m async for m in message.channel.history(limit=10)
                if m.content and not m.attachments and not m.embeds
            ]

            # Formate l'historique pour le prompt
            history = ""
            for m in reversed(messages):
                history += f"{m.author.name}: {m.content}\n"
            prompt = (
                CHARACTER_PROMPT +
                "Historique de la conversation:\n" +
                history +
                f"{message.author.name}: @{bot.user.name} Peux-tu répondre ?\n" +
                f"{bot.user.name}:"
            )

            print("Prompt généré pour LLaMA :", prompt)

            # Génération de la réponse par l'IA
            response = await asyncio.to_thread(
                llm,
                prompt,
                max_tokens=128,
                temperature=0.8,
                top_p=0.95,
                repeat_penalty=1.1,
                stop=["\n"]
            )
            print("Réponse LLaMA brute :", response)
            answer = response["choices"][0]["text"].strip()

            match = re.search(r'^(.*[.!?])', answer, re.DOTALL)
            if match:
                answer = match.group(1).strip()

            if not answer:
                answer = "Je suis à court d'idées... réessaye 😅"

            await message.channel.send(answer)
    await bot.process_commands(message)

bot.run(token)