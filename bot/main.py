# bot/main.py
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------
# Feminist For Justice Discord Bot
# This bot is designed to send daily email reports of messages from specific channels in a Discord server.
# It uses the discord.py library to interact with the Discord API and the smtplib library to send emails.
# The bot is configured using environment variables loaded from a .env file.
# The bot is designed to be run as a standalone script and can be started using the command line.
# It includes error handling and logging to help with debugging and monitoring.
# The bot is designed to be run on a server or a local machine with Python 3.8 or higher installed.
#
# - 0. Bot Initialisation
#     - 0.1 variables d'environnement (get_env_config) - OK
#     - 0.2 logging (setup_logging) - OK
#     - 0.3 intents (get_intents) - OK
#     - 0.4 test command - Create just one command to send a test e-mail (même fonction que la routine quotidienne, mais destinataire différent) - OK
# - 1. SendDailyMail (daily_task)
#     - 1.1 Read and store in a temporary list channels in #important_channels and #excluded_channels  (corriger et fusionner les 2 fonctions "parse_channels_list" et "fetch_channel_config")
#     - 1.2 Gather DailyMessages from all channels excepted #excluded_channels (gather_daily_messages(channel_config)) (il me semble que "channel_config" n'est pas déjà défini dans le code)
#     - 1.3 Format DailyMessages into HTML (format_messages_for_email(messages_dict)) (corriger et fusionner les 2 fonctions "format_messages_for_email" et "format_messages_html")(corriger le format de l'email, le corps doit être en texte brut et non en HTML)(messages_dict ne semble pas défini dans le code)
#     - 1.4 Send DailyReport (send_email et send_report ne font pas doublons ?)(En fait il faut une fonction permettant d'envoyer un email avec le rapport quotidien. Mais il faut que le destinataire soit différent selon que la fonction soit appelée par la tâche quotidienne ou par la commande de test.)
#     - 1.5 on_ready (on_ready) - OK
#     - 1.6 daily_task (tasks.loop) - Heure d'envoi du rapport quotidien non définie
# - 2. Entry point (main)
#     - 2.1 Run the bot (asyncio.run(main)) - OK
#     - 2.2 Handle exceptions (sys.excepthook) - OK
#     - 2.3 Run the bot (bot.run()) - OK
# ------------------------------------------------------------------------
import asyncio
import logging
import os
import sys
import traceback
import smtplib
import re

from datetime import datetime, timezone, timedelta, time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from dotenv import load_dotenv
import discord
from discord.ext import commands, tasks

# ----------------------------------------------------------------------
# 0) Initialisation
# ----------------------------------------------------------------------
load_dotenv()
def get_env_config():
    return {
        "DISCORD_TOKEN": os.getenv("DISCORD_TOKEN"),
        "EMAIL_ADDRESS": os.getenv("EMAIL_ADDRESS"),
        "EMAIL_PASSWORD": os.getenv("EMAIL_PASSWORD"),
        "RECIPIENT_EMAIL": os.getenv("RECIPIENT_EMAIL"),
        "TEST_RECIPIENT_EMAIL": os.getenv("TEST_RECIPIENT_EMAIL"),
        "BOT_STORAGE_CHANNEL_ID": os.getenv("BOT_STORAGE_CHANNEL_ID"),
        "IMPORTANT_MSG_ID": os.getenv("IMPORTANT_MSG_ID"),
        "EXCLUDED_MSG_ID": os.getenv("EXCLUDED_MSG_ID"),
    }

def setup_logging():
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    sys.excepthook = lambda etype, value, tb: traceback.print_exception(etype, value, tb)

def get_intents():
    intents = discord.Intents.default()
    intents.messages = True
    intents.message_content = True
    intents.guilds = True
    return intents

setup_logging()
intents = get_intents()
bot = commands.Bot(command_prefix="!", intents=intents)

# ----------------------------------------------------------------------
# 1) Config des canaux
# ----------------------------------------------------------------------
async def get_channel_config(bot_instance) -> dict:
    env = get_env_config()
    storage_id = env.get("BOT_STORAGE_CHANNEL_ID")
    important_id = env.get("IMPORTANT_MSG_ID")
    excluded_id = env.get("EXCLUDED_MSG_ID")

    def parse_list_from_content(content: str, prefix: str):
        if prefix not in content:
            return []
        after_prefix = content.replace(prefix, "").strip()
        return [c.strip() for c in after_prefix.split(",") if c.strip()]

    if not (storage_id and important_id and excluded_id):
        print("[ERROR] ID(s) manquant(s) dans .env.")
        return {"important_channels": [], "excluded_channels": []}

    channel = bot_instance.get_channel(int(storage_id))
    if not channel:
        print("[ERROR] Channel de stockage introuvable.")
        return {"important_channels": [], "excluded_channels": []}

    try:
        msg_important = await channel.fetch_message(int(important_id))
        msg_excluded = await channel.fetch_message(int(excluded_id))

        important_list = parse_list_from_content(msg_important.content, "Canaux_importants:")
        excluded_list = parse_list_from_content(msg_excluded.content, "Canaux_exclus:")
        return {
            "important_channels": important_list,
            "excluded_channels": excluded_list
        }
    except Exception as e:
        print(f"[ERROR] Impossible de récupérer la config des canaux: {e}")
        return {"important_channels": [], "excluded_channels": []}

# ----------------------------------------------------------------------
# 2) Récupération messages
# ----------------------------------------------------------------------
async def gather_daily_messages(bot_instance) -> dict:
    """
    Collecte les messages dans les canaux (excl. ou importants) depuis hier 06h00 UTC.
    """
    channel_config = await get_channel_config(bot_instance)
    important_names = channel_config["important_channels"]
    excluded_names = channel_config["excluded_channels"]

    now_utc = datetime.now(timezone.utc)
    today_6am_utc = now_utc.replace(hour=6, minute=0, second=0, microsecond=0)
    if now_utc.hour < 6:
        today_6am_utc -= timedelta(days=1)
    after_time = today_6am_utc - timedelta(days=1)
    
    daily_messages = {"important": {}, "general": {}}
    for guild in bot_instance.guilds:
        for chan in guild.text_channels:
            if chan.name in excluded_names:
                continue
            fetched_msgs = []
            try:
                async for msg in chan.history(limit=None, after=after_time, oldest_first=True):
                    if msg.created_at.replace(tzinfo=timezone.utc) <= today_6am_utc:
                        fetched_msgs.append({
                            "author": msg.author.display_name,
                            "content": msg.content,
                            "timestamp": msg.created_at
                        })
            except Exception as e:
                print(f"[ERROR] Impossible de récupérer {chan.name}: {e}")
                continue

            if not fetched_msgs:
                continue

            if chan.name in important_names:
                daily_messages["important"][chan.name] = fetched_msgs
            else:
                daily_messages["general"][chan.name] = fetched_msgs

    return daily_messages

# ----------------------------------------------------------------------
# 2.1) Aides pour dates FR & liens cliquables
# ----------------------------------------------------------------------
DAYS_FR = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
MONTHS_FR = [
    "",
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre"
]

def date_fr(dt: datetime, with_time=True) -> str:
    """
    Exemple: "Vendredi 4 avril 2025" ou "Vendredi 4 avril 2025 à 11h05"
    """
    weekday = DAYS_FR[dt.weekday()]
    day = dt.day
    month = MONTHS_FR[dt.month]
    year = dt.year
    if with_time:
        return f"{weekday} {day} {month} {year} à {dt.hour:02d}h{dt.minute:02d}"
    else:
        return f"{weekday} {day} {month} {year}"

def make_links_clickable(text: str) -> str:
    """
    Transforme toute URL http(s)://... en <a href="...">...</a>.
    """
    pattern = r'(https?://[^\s]+)'
    return re.sub(pattern, r'<a href="\1">\1</a>', text)

# Couleurs d'auteurs (alternées)
author_colors = {}
available_colors = ["#8E44AD", "#148F77"]  # mauve / vert
def get_author_color(author_name: str) -> str:
    if author_name not in author_colors:
        index = len(author_colors) % len(available_colors)
        author_colors[author_name] = available_colors[index]
    return author_colors[author_name]

# ----------------------------------------------------------------------
# 3) Regrouper par jour
# ----------------------------------------------------------------------
def group_messages_by_day(msg_list: list) -> dict:
    """
    Regroupe la liste de messages (chacun {timestamp, author, content})
    par journée (ex. "Vendredi 4 avril 2025").
    Retourne un dict : { "Vendredi 4 avril 2025" : [ msg, msg, ... ], ... }
    """
    day_groups = {}
    for msg in msg_list:
        # On veut la date sans l'heure
        dt = msg["timestamp"]
        day_str = date_fr(dt, with_time=False)  # ex. "Vendredi 4 avril 2025"
        if day_str not in day_groups:
            day_groups[day_str] = []
        day_groups[day_str].append(msg)

    return day_groups

# ----------------------------------------------------------------------
# 4) Construction du rapport HTML
# ----------------------------------------------------------------------
def build_html_report(daily_msgs: dict, date_debut: str, date_fin: str) -> str:
    """
    Construit le HTML en tenant compte:
     - Titre centré
     - Sous-titre: date_debut en mauve gras, date_fin en vert gras
     - Liens cliquables
     - Affichage par date (une seule fois), puis liste des msgs avec (Heure - auteur : contenu)
    """

    # On fabrique des f-strings HTML dans un grand "chunks"
    # 1) Bloc titre (centré)
    html_chunks = []
    html_chunks.append(f"""
    <div style="display:block; margin:20px auto; border:2px double #A32C39; border-radius:25px; padding:10px; width:70%; text-align:center;">
      <h1 style="font-size:24px; color:#A32C39; margin:5px 0;">
        <img src="https://i0.wp.com/femmesdedroit.be/wp-content/uploads/2024/11/Logo-FfJ.png?w=499&ssl=1" alt="Coalition Feminist For Justice" titre="Discord de la Coalition FFJ" width="70" style="vertical-align:middle; margin-right:10px; border-radius:50%;" />
        Rapport quotidien du  <a href="https://discord.gg/coalitionfeministforjustice" style="color:#31b9cd; text-decoration:bold;">Discord - Coalition Feminist For Justice</a>
      </h1>
    </div>
    """)

    # 2) Sous-titre, date début en mauve, date fin en vert
    html_chunks.append(f"""
    <p style="text-align:center; font-style:italic; font-size:16px; margin-top:10px;">
      Échanges du <strong style="color:#8E44AD;">{date_debut}</strong>
      au <strong style="color:#148F77;">{date_fin}</strong>.
    </p>
    """)

    # 3) Canaux Importants
    html_chunks.append("""
    <div style="border:2px solid #B1B1BD; border-radius:5px; 
                padding:20px; margin:20px; width:80%; margin-left:auto; margin-right:auto;">
      <h2 style="color:#31b9cd; font-size:22px; margin-top:0; text-transform:uppercase;">
        Canaux Importants
      </h2>
    """)

    for channel_name, msgs in daily_msgs.get("important", {}).items():
        if not msgs:
            continue

        # Grouper par jour
        day_dict = group_messages_by_day(msgs)

        html_chunks.append(f"""
        <div style="border:2px solid black; border-radius:5px;
                    padding:10px 20px; margin:20px;">
          <h3 style="color:#A32C39; font-size:18px; margin-top:0;">
            {channel_name}
          </h3>
        """)

        # Pour chaque jour => on l'affiche, puis la liste des messages
        for day_str, day_msgs in day_dict.items():
            html_chunks.append(f"""
            <p style="margin:10px 0; font-size:16px; font-weight:bold;">
              {day_str}
            </p>
            <ul style="list-style-type:none; padding-left:20px;">
            """)

            for m in day_msgs:
                # On met l'heure + auteur + contenu
                # Liens cliquables
                content_html = make_links_clickable(m["content"])
                # Couleur auteur
                author_color = get_author_color(m["author"])
                # Heure style "11h05"
                h_str = f"{m['timestamp'].hour:02d}h{m['timestamp'].minute:02d}"

                html_chunks.append(f"""
              <li style="margin-bottom:5px;">
                <span style="font-size:15px; color:{author_color}; font-weight:bold;">
                  {h_str} - {m['author']}
                </span>
                : {content_html}
              </li>
                """)

            html_chunks.append("</ul>")  # fin UL

        html_chunks.append("</div>")  # fin bloc canal

    html_chunks.append("</div>")  # fin bloc "Canaux Importants"

    # 4) Autres Canaux
    html_chunks.append("""
    <div style="border:2px solid black; border-radius:5px; padding:20px; 
                margin:20px; width:80%; margin-left:auto; margin-right:auto;">
      <h2 style="color:#31b9cd; font-size:22px; margin-top:0; text-transform:uppercase;">
        Autres Canaux
      </h2>
    """)

    for channel_name, msgs in daily_msgs.get("general", {}).items():
        if not msgs:
            continue
        day_dict = group_messages_by_day(msgs)
        html_chunks.append(f"""
        <div style="border:2px solid black; border-radius:5px;
                    padding:10px 20px; margin:20px;">
          <h3 style="color:#A32C39; font-size:18px; margin-top:0;">
            {channel_name}
          </h3>
        """)

        for day_str, day_msgs in day_dict.items():
            html_chunks.append(f"""
            <p style="margin:10px 0; font-size:16px; font-weight:bold;">
              {day_str}
            </p>
            <ul style="list-style-type:none; padding-left:20px;">
            """)

            for m in day_msgs:
                content_html = make_links_clickable(m["content"])
                author_color = get_author_color(m["author"])
                h_str = f"{m['timestamp'].hour:02d}h{m['timestamp'].minute:02d}"

                html_chunks.append(f"""
              <li style="margin-bottom:5px; font-size:18px;">
                <span style="color:{author_color}; font-weight:bold;">
                  {h_str} - {m['author']}
                </span>
                : {content_html}
              </li>
                """)
            html_chunks.append("</ul>")

        html_chunks.append("</div>")
    html_chunks.append("</div>")

    # 5) Pied de page

    html_chunks.append("""
    <div style="width:70%; margin:20px auto; border:2px double #A32C39; border-radius:25px; padding:10px; text-align:center; background:#fff;">

  <!-- Première rangée : Coalition Feminist for Justice + Femmes de droit -->
  <table border="0" cellspacing="0" cellpadding="0" width="100%" style="border-collapse:collapse;">
    <tr>
      <!-- Coalition sur la gauche -->
      <td style="vertical-align:middle; width:20%; text-align:center; padding:1px;">
        <a href="https://femmesdedroit.be/nos-actions/coalition-feminists-for-justice/" title="Coalition Feminist for Justice" target="_blank">
          <img src="https://i0.wp.com/femmesdedroit.be/wp-content/uploads/2024/11/Logo-FfJ.png?w=499&ssl=1" alt="Coalition Feminist for Justice" width="160" style="margin-bottom:0px;" />
        </a>
      </td>
      <td style="vertical-align:middle; width:30%; padding:2px;">
        <p style="margin:2px 0; font-weight:bold; color:#a32c39; font-size:26px; text-align:center;">
          Coalition Feminist for Justice
        </p>
      </td>
      <!-- Femmes de droit sur la droite -->
      <td style="vertical-align:middle; width:30%; text-align:center; padding:1px;">
        <p style="margin:1px 0; font-weight:bold; font-style: italic; color:#333; font-size:14px; text-align:center;">
          Portée par Femmes de droit
        </p>
        <a href="https://femmesdedroit.be/" title="Femmes de droit" target="_blank">
          <img src="https://i0.wp.com/femmesdedroit.be/wp-content/uploads/2018/04/cropped-FDD-AVATAR-Rond-RVB.jpg?w=240&ssl=1" alt="Femmes de droit" width="130" style="margin-bottom:0px;" />
        </a>
      </td>
    </tr>
  </table>

  <!-- Titre "Associations partenaires" si souhaité -->
  <p style="font-weight:bold; color:#333; font-size:18px; margin:0px; padding:0px;">
    Associations partenaires :
  </p>
  <!-- Deuxième rangée : 6 logos -->
  <table border="0" cellspacing="0" cellpadding="0" width="100%" style="border-collapse:collapse; padding:0; margin:0;">
    <tr>
      <!-- GAMS -->
      <td style="width:16.66%; text-align:center; padding:0; margin:0; border:1px">
        <a href="https://gams.be/" title="Le GAMS Belgique" target="_blank">
          <img src="https://i0.wp.com/femmesdedroit.be/wp-content/uploads/2025/01/LogoGAMS201-transparent-002.jpg?resize=1024%2C365&ssl=1" alt="Le GAMS Belgique" width="140" style="display:block; margin:0 auto;" />
        </a>
      </td>
      <!-- JUMP -->
      <td style="width:16.66%; text-align:center; padding:1px;">
        <a href="https://jump.eu.com/" title="JUMP" target="_blank">
          <img src="https://i0.wp.com/femmesdedroit.be/wp-content/uploads/2025/01/jump-for-equality.png?w=684&ssl=1" alt="JUMP" width="140" style="display:block; margin:0 auto;" />
        </a>
      </td>
      <!-- MEFH -->
      <td style="width:16.66%; text-align:center; padding:1px;">
        <a href="https://m-egalitefemmeshommes.be/" title="Le Mouvement pour l’Égalité entre les Femmes et les Hommes" target="_blank">
          <img src="https://i0.wp.com/femmesdedroit.be/wp-content/uploads/2025/01/MEFH.jpeg?resize=300%2C245&ssl=1" alt="MEFH" width="100" style="display:block; margin:0 auto;" />
        </a>
      </td>
      <!-- Université des femmes -->
      <td style="width:16.66%; text-align:center; padding:1px;">
        <a href="https://www.universitedesfemmes.be/" title="L'Université des femmes" target="_blank">
          <img src="https://i0.wp.com/femmesdedroit.be/wp-content/uploads/2023/03/UF_Capture.png?fit=237%2C73&ssl=1" alt="Université des femmes" width="150" style="display:block; margin:0 auto;" />
        </a>
      </td>
      <!-- Collectif des femmes -->
      <td style="width:16.66%; text-align:center; padding:1px;">
        <a href="https://www.collectifdesfemmes.be/" title="Le Collectif des femmes" target="_blank">
          <img src="https://i0.wp.com/femmesdedroit.be/wp-content/uploads/2025/01/Logo-CDF-court-mauve.png?resize=300%2C300&ssl=1" alt="Le Collectif des femmes" width="140" style="display:block; margin:0 auto;" />
        </a>
      </td>
      <!-- FACES -->
      <td style="width:16.66%; text-align:center; padding:1px;">
        <a href="https://www.facebook.com/people/R%C3%A9seau-FACES/100055148357144/" title="Le réseau FACES" target="_blank">
          <img src="https://i0.wp.com/femmesdedroit.be/wp-content/uploads/2025/01/FACES.jpg?resize=244%2C300&ssl=1" alt="Le réseau FACES" width="120" style="display:block; margin:0 auto;" />
        </a>
      </td>
    </tr>
  </table>
  <!-- Dernière ligne : lien de désabonnement, infos -->
  <hr style="border:none; border-top:1px solid #CCC; margin:10px 0;" />
  <p style="font-size:14px; color:#777; margin:5px;">
    <a href="http://votre-lien-de-desabonnement" style="color:#A32C39; text-decoration:none;">Se désabonner</a> - ----- - <strong>Contact :</strong>  secretariat@femmesdedroit.be
  </p>
</div>
    """)

    final_html = (
        "<html>"
        "<body style='margin:0; padding:0; font-family:Arial,sans-serif; background:#F9F9F9;'>"
        + "".join(html_chunks) +
        "</body></html>"
    )
    return final_html

# ----------------------------------------------------------------------
# 5) Envoi e-mail
# ----------------------------------------------------------------------
def send_email(plain_text: str, html_content: str, recipient: str):
    env = get_env_config()
    from_addr = env.get("EMAIL_ADDRESS")
    password = env.get("EMAIL_PASSWORD")

    if not (from_addr and password and recipient):
        print("[ERROR] Paramètres d'envoi d'e-mail manquants.")
        return

    subject = "Rapport quotidien Discord"
    if recipient == env.get("TEST_RECIPIENT_EMAIL"):
        subject += " - TEST"

    msg = MIMEMultipart("alternative")
    msg["From"] = from_addr
    msg["To"] = recipient
    msg["Subject"] = subject

    part_text = MIMEText(plain_text, "plain", "utf-8")
    part_html = MIMEText(html_content, "html", "utf-8")
    msg.attach(part_text)
    msg.attach(part_html)

    try:
        with smtplib.SMTP("ssl0.ovh.net", 587) as server:
            server.starttls()
            server.login(from_addr, password)
            server.sendmail(from_addr, [recipient], msg.as_string())
        print(f"[CORE] E-mail envoyé à {recipient}")
    except Exception as e:
        print(f"[ERROR] Échec de l'envoi de l'e-mail : {e}")

# ----------------------------------------------------------------------
# 6) Routine d'envoi
# ----------------------------------------------------------------------
async def send_report(recipient: str):
    """
    Récupère les messages du jour, construit un HTML stylé,
    et envoie un mail multipart (texte + HTML).
    """
    daily_msgs = await gather_daily_messages(bot)

    # Calcule date_debut / date_fin en FR (jour & heure)
    now_utc = datetime.now(timezone.utc)
    today_6am_utc = now_utc.replace(hour=6, minute=0, second=0, microsecond=0)
    if now_utc.hour < 6:
        today_6am_utc -= timedelta(days=1)
    date_fin_dt = today_6am_utc
    date_debut_dt = today_6am_utc - timedelta(days=1)

    date_debut_str = date_fr(date_debut_dt, with_time=True)
    date_fin_str = date_fr(date_fin_dt, with_time=True)

    # Construire HTML
    html_body = build_html_report(daily_msgs, date_debut_str, date_fin_str)

    # Construire un plain_text minimal
    text_lines = []
    text_lines.append(f"Rapport quotidien Discord - Coalition Feminist For Justice\n")
    text_lines.append(f"Échanges du {date_debut_str} au {date_fin_str}\n")

    for section_label in ["important", "general"]:
        if section_label == "important":
            text_lines.append("=== CANAUX IMPORTANTS ===\n")
        else:
            text_lines.append("=== AUTRES CANAUX ===\n")

        for chan_name, msgs in daily_msgs[section_label].items():
            if not msgs:
                continue
            text_lines.append(f"{chan_name.upper()} :")
            # On va regrouper par jour
            day_dict = group_messages_by_day(msgs)
            for day_str, day_msgs in day_dict.items():
                text_lines.append(f"  [ {day_str} ]")
                for m in day_msgs:
                    hhmm = f"{m['timestamp'].hour:02d}h{m['timestamp'].minute:02d}"
                    text_lines.append(f"    {hhmm} - {m['author']}: {m['content']}")
            text_lines.append("")

    plain_text = "\n".join(text_lines)

    # Envoi
    send_email(plain_text, html_body, recipient)

# ----------------------------------------------------------------------
# 7) Commandes
# ----------------------------------------------------------------------
@bot.command(name="testmail")
async def test_email_command(ctx):
    """
    Envoie un mail à TEST_RECIPIENT_EMAIL
    """
    env_config = get_env_config()
    test_recipient = env_config.get("TEST_RECIPIENT_EMAIL")
    if not test_recipient:
        await ctx.send("TEST_RECIPIENT_EMAIL non défini dans .env.")
        return
    await send_report(test_recipient)
    await ctx.send("Email de test envoyé.")

@bot.command(name="nextreport")
async def nextreport_cmd(ctx):
    """
    Affiche la date et l'heure d'envoi du prochain rapport quotidien.
    """
    if daily_task.next_iteration:
        # daily_task.next_iteration est un datetime (UTC)
        next_time_utc = daily_task.next_iteration
        # On peut le convertir en heure locale si besoin :
        local_time = next_time_utc.astimezone()  # fuseau local
        # Format
        out_str_utc = next_time_utc.strftime("%Y-%m-%d %H:%M:%S UTC")
        out_str_local = local_time.strftime("%Y-%m-%d %H:%M:%S (local)")
        await ctx.send(f"Le prochain rapport est prévu le {out_str_utc} / {out_str_local}.")
    else:
        await ctx.send("La tâche quotidienne n'est pas planifiée.")

# ----------------------------------------------------------------------
# 8) Tâche quotidienne
# ----------------------------------------------------------------------
@bot.event
async def on_ready():
    print(f"[CORE] Bot connecté en tant que {bot.user} (ID: {bot.user.id})")
    daily_task.change_interval(time=time(hour=6, minute=0, tzinfo=timezone.utc))
    daily_task.start()

@tasks.loop(hours=24)
async def daily_task():
    now = datetime.now(timezone.utc)
    print(f"[CORE] Tâche quotidienne déclenchée à {now} (UTC)")
    env = get_env_config()
    recipient = env.get("RECIPIENT_EMAIL")
    if recipient:
        await send_report(recipient)
    else:
        print("[ERROR] Aucune RECIPIENT_EMAIL pour l'envoi quotidien.")

# ----------------------------------------------------------------------
# 9) Main Asynchrone
# ----------------------------------------------------------------------
async def main():
    env_config = get_env_config()
    token = env_config.get("DISCORD_TOKEN")

    if not token:
        print("[ERROR] DISCORD_TOKEN non défini dans .env.")
        return

    try:
        await bot.start(token)
    except Exception as e:
        print(f"[ERROR] Bot crashed : {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
