import asyncio
import logging
import os
import sys
import traceback
import json
import smtplib
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import discord
from discord.ext import commands, tasks

# ----------------------------------------------------------------------
# 0) Bot Initialisation
# ----------------------------------------------------------------------
load_dotenv()

def get_env_config():
    """
    Récupère les variables d'environnement nécessaires pour le bot
    et les retourne sous forme de dictionnaire.
    """
    return {
        "DISCORD_TOKEN": os.getenv("DISCORD_TOKEN"),
        "EMAIL_ADDRESS": os.getenv("EMAIL_ADDRESS"),
        "EMAIL_PASSWORD": os.getenv("EMAIL_PASSWORD"),
        "RECIPIENT_EMAIL": os.getenv("RECIPIENT_EMAIL"),
        "TEST_RECIPIENT_EMAIL": os.getenv("TEST_RECIPIENT_EMAIL"),
        "BOT_STORAGE_CHANNEL_ID": os.getenv("BOT_STORAGE_CHANNEL_ID"),
        "IMPORTANT_MSG_ID": os.getenv("IMPORTANT_MSG_ID"),
        "EXCLUDED_MSG_ID": os.getenv("EXCLUDED_MSG_ID")
    }

def setup_logging():
    """
    Configure le logging et la gestion globale des exceptions.
    """
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    sys.excepthook = lambda etype, value, tb: traceback.print_exception(etype, value, tb)

def get_intents():
    """
    Configure et retourne les intents Discord nécessaires.
    """
    intents = discord.Intents.default()
    intents.messages = True
    intents.message_content = True
    intents.guilds = True
    return intents

setup_logging()
intents = get_intents()
bot = commands.Bot(command_prefix="!", intents=intents)

# Fonction générique pour envoyer un e-mail
def send_email(body, recipient):
    """
    Envoie l'e-mail via SMTP OVH, en mode starttls().
    Le destinataire est passé en paramètre.
    """
    env_config = get_env_config()
    from_addr = env_config.get("EMAIL_ADDRESS")
    password = env_config.get("EMAIL_PASSWORD")

    msg = MIMEMultipart()
    msg["From"] = from_addr
    msg["To"] = recipient
    msg["Subject"] = "Rapport quotidien Discord" if recipient == env_config.get("RECIPIENT_EMAIL") else "Rapport quotidien Discord - TEST"
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP("ssl0.ovh.net", 587) as server:
        server.starttls()
        server.login(from_addr, password)
        server.sendmail(from_addr, recipient, msg.as_string())

# Commande de test qui utilise l'adresse TEST_RECIPIENT_EMAIL
@bot.command(name="testmail")
async def test_email_command(ctx):
    env_config = get_env_config()
    test_recipient = env_config.get("TEST_RECIPIENT_EMAIL")
    if not test_recipient:
        await ctx.send("TEST_RECIPIENT_EMAIL n'est pas configuré dans le .env.")
        return
    body = f"Test email envoyé par le bot à {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    try:
        send_email(body, test_recipient)
        await ctx.send("Email de test envoyé avec succès.")
    except Exception as e:
        await ctx.send(f"Échec de l'envoi de l'email de test: {e}")

# ----------------------------------------------------------------------
# 1) Fonctions du Bot
# ----------------------------------------------------------------------
async def fetch_channel_config(bot, storage_channel_id, important_msg_id, excluded_msg_id):
    """
    Récupère les messages contenant la configuration des canaux importants et exclus
    depuis un canal de stockage.
    """
    channel = bot.get_channel(int(storage_channel_id))
    important_msg = await channel.fetch_message(int(important_msg_id))
    excluded_msg = await channel.fetch_message(int(excluded_msg_id))
    data = {}
    try:
        data["important_channels"] = json.loads(important_msg.content)["important_channels"]
    except Exception:
        data["important_channels"] = []
    try:
        data["excluded_channels"] = json.loads(excluded_msg.content)["excluded_channels"]
    except Exception:
        data["excluded_channels"] = []
    return data

async def fetch_daily_messages(channel):
    """
    Récupère les messages du jour d'un canal donné.
    Pour cet exemple, cette fonction est simulée.
    """
    return [{
        "author": "TestUser",
        "content": f"Message de test de {channel.name}",
        "timestamp": datetime.now()
    }]

async def gather_daily_messages(channel_config):
    """
    Récupère les messages quotidiens de tous les canaux,
    en excluant ceux spécifiés dans channel_config.
    Retourne un dictionnaire structuré.
    """
    messages = {"important": {}, "general": {}}
    important_channels = channel_config.get("important_channels", [])
    excluded_channels = channel_config.get("excluded_channels", [])

    # Messages des canaux importants
    for channel_id in important_channels:
        chan = bot.get_channel(int(channel_id))
        if chan:
            msgs = await fetch_daily_messages(chan)
            messages["important"][chan.name] = msgs

    # Messages des canaux généraux (tous les canaux de texte sauf ceux exclus et importants)
    for guild in bot.guilds:
        for chan in guild.text_channels:
            if str(chan.id) in excluded_channels or str(chan.id) in important_channels:
                continue
            msgs = await fetch_daily_messages(chan)
            messages["general"][chan.name] = msgs
    return messages

def format_messages_for_email(messages_dict):
    """
    Construit le corps de l'e-mail à partir du dictionnaire de messages.
    """
    email_body = "**Mail de résumé quotidien du Discord de la Coalition Feminist For Justice.**\n\n"
    if messages_dict.get("important"):
        email_body += "### Canaux importants\n\n"
        for channel, msg_list in messages_dict["important"].items():
            email_body += f"## {channel}\n\n"
            for msg in msg_list:
                author = msg.get("author", "???")
                content = msg.get("content", "")
                date_str = msg.get("timestamp").strftime("%Y-%m-%d %H:%M") if isinstance(msg.get("timestamp"), datetime) else ""
                email_body += f"{date_str} - **{author}** : {content}\n\n"
    if messages_dict.get("general"):
        email_body += "### Autres canaux\n\n"
        for channel, msg_list in messages_dict["general"].items():
            email_body += f"## {channel}\n\n"
            for msg in msg_list:
                author = msg.get("author", "???")
                content = msg.get("content", "")
                date_str = msg.get("timestamp").strftime("%Y-%m-%d %H:%M") if isinstance(msg.get("timestamp"), datetime) else ""
                email_body += f"{date_str} - **{author}** : {content}\n\n"
    return email_body

# ----------------------------------------------------------------------
# 2) Événements et Tâches
# ----------------------------------------------------------------------
@bot.event
async def on_ready():
    print(f"[CORE] Bot connecté en tant que {bot.user} (ID: {bot.user.id})")
    daily_task.start()

@tasks.loop(hours=24)
async def daily_task():
    """
    Tâche quotidienne qui :
      1. Récupère la configuration des canaux.
      2. Rassemble les messages quotidiens.
      3. Formate le rapport.
      4. Envoie l’e-mail à RECIPIENT_EMAIL.
    """
    now = datetime.now(timezone.utc)
    print(f"[CORE] Tâche quotidienne déclenchée à {now} (UTC)")

    env_config = get_env_config()
    storage_channel_id = env_config.get("BOT_STORAGE_CHANNEL_ID")
    important_msg_id = env_config.get("IMPORTANT_MSG_ID")
    excluded_msg_id = env_config.get("EXCLUDED_MSG_ID")

    channel_config = await fetch_channel_config(bot, storage_channel_id, important_msg_id, excluded_msg_id)
    print("Configuration des canaux :", channel_config)

    messages = await gather_daily_messages(channel_config)
    email_body = format_messages_for_email(messages)

    recipient = env_config.get("RECIPIENT_EMAIL")
    if env_config.get("EMAIL_ADDRESS") and env_config.get("EMAIL_PASSWORD") and recipient:
        send_email(email_body, recipient)
        print("[CORE] Rapport quotidien envoyé par e-mail.")
    else:
        print("[ERROR] Informations d'e-mail manquantes dans la configuration.")

# ----------------------------------------------------------------------
# 3) Point d'entrée asynchrone
# ----------------------------------------------------------------------
async def main():
    env_config = get_env_config()
    token = env_config.get("DISCORD_TOKEN")
    if not token:
        print("[ERROR] DISCORD_TOKEN non défini dans le .env.")
        return
    try:
        await bot.start(token)
    except Exception as e:
        print(f"[ERROR] Bot crashed : {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
