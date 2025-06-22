import os
import re
import discord
import enum
import asyncio
from discord.ext import commands
from llama_cpp import Llama
from typing import List

class HistoriqueChoice(enum.Enum):
    oui = "oui"
    non = "non"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

token = os.getenv("DISCORD_TOKEN")
if not token:
    raise ValueError("DISCORD_TOKEN environment variable is not set.")

MODEL_PATH = "C:/Users/swanl/Documents/AI/text-generation-webui/user_data/models/"
MODEL_NAME = "L3-8B-Stheno-v3.2-Q4_K_M.gguf"

llm = Llama(model_path=MODEL_PATH + MODEL_NAME, n_ctx=2048, n_gpu_layers=99, n_batch=512)

CHARACTER_PROMPTS = {
    "assistant": open("assistant.txt", "r", encoding="utf-8").read(),
    "oldman": open("oldman.txt", "r", encoding="utf-8").read(),
    "racist": open("racist.txt", "r", encoding="utf-8").read(),
    "uwu": open("uwu.txt", "r", encoding="utf-8").read(),
    "sexyman": open("sexyman.txt", "r", encoding="utf-8").read(),
    "sexywoman": open("sexywoman.txt", "r", encoding="utf-8").read(),
}

@bot.event
async def on_ready():
    print(f"Connecté en tant que {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Slash commands synchronisées ({len(synced)})")
    except Exception as e:
        print(f"Erreur lors de la synchronisation des slash commands: {e}")

async def personnage_autocomplete(
    interaction: discord.Interaction,
    current: str
) -> List[discord.app_commands.Choice[str]]:
    return [
        discord.app_commands.Choice(name=key, value=key)
        for key in CHARACTER_PROMPTS.keys()
        if current.lower() in key.lower()
    ]

@bot.tree.command(name="ask", description="Pose une question à un personnage IA")
@discord.app_commands.describe(
    personnage="Choisis le personnage IA",
    question="Ta question",
    historique="Inclure l'historique des 10 derniers messages (oui/non)"
)
@discord.app_commands.autocomplete(personnage=personnage_autocomplete)
async def ask(interaction: discord.Interaction, personnage: str, question: str, historique: HistoriqueChoice = HistoriqueChoice.oui  # Utilise l'enum ici
):
    if personnage not in CHARACTER_PROMPTS:
        await interaction.response.send_message(
            f"Personnage inconnu. Choisis parmi : {', '.join(CHARACTER_PROMPTS.keys())}", ephemeral=True
        )
        return

    await interaction.response.defer()  # Affiche "en train d'écrire..."

    # Récupère les 10 derniers messages du salon

    history = ""
    if historique:
        messages = [
            m async for m in interaction.channel.history(limit=10)
            if (
                m.content
                and not m.attachments
                and not m.embeds
                and "http://" not in m.content
                and "https://" not in m.content
            )
        ]
        for m in reversed(messages):
            history += f"{m.author.name}: {m.content}\n"

    prompt = (
        CHARACTER_PROMPTS[personnage]
        + "\nHistorique de la conversation:\n"
        + history
        + f"{interaction.user.name}: {question}\n"
        + f"{bot.user.name}:"
    )

    print(f"Prompt envoyé à LLM: {prompt}")

    response = await asyncio.to_thread(
        llm,
        prompt,
        max_tokens=128,
        temperature=0.8,
        top_p=0.95,
        repeat_penalty=1.1,
        stop=["\n"]
    )
    answer = response["choices"][0]["text"].strip()
    match = re.search(r'^(.*[.!?])', answer, re.DOTALL)
    if match:
        answer = match.group(1).strip()
    if not answer:
        answer = "Je suis à court d'idées... réessaye 😅"

    await interaction.followup.send(
        f"**{interaction.user.display_name} :** {question}\n"
        f"**{bot.user.display_name} :** {answer}"
    )

bot.run(token)