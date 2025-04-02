import os
STORAGE_MODE = os.getenv("STORAGE_MODE", "discord")  # "discord" par défaut

class StorageManager:
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # si mode json, on peut définir un chemin de fichier par exemple
        self.json_path = "data/channels.json"

    async def initialize_storage(self):
        if STORAGE_MODE == "discord":
            # ton code pour Discord (comme précédemment)
            channel = self.bot.get_channel(BOT_STORAGE_CHANNEL_ID)
            # ... etc.
        else:
            # Mode JSON externe
            if not os.path.exists(self.json_path):
                data = {"important_channels": [], "excluded_channels": []}
                with open(self.json_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)

    async def get_storage_data(self):
        if STORAGE_MODE == "discord":
            # Code pour lire les messages de stockage Discord
            channel = self.bot.get_channel(BOT_STORAGE_CHANNEL_ID)
            important_msg = await channel.fetch_message(IMPORTANT_MSG_ID)
            excluded_msg  = await channel.fetch_message(EXCLUDED_MSG_ID)
            data = {}
            try:
                data["important_channels"] = json.loads(important_msg.content)["important_channels"]
            except Exception as e:
                data["important_channels"] = []
            try:
                data["excluded_channels"] = json.loads(excluded_msg.content)["excluded_channels"]
            except Exception as e:
                data["excluded_channels"] = []
            return data
        else:
            # Mode JSON
            with open(self.json_path, "r", encoding="utf-8") as f:
                return json.load(f)

    async def update_storage(self, important_channels, excluded_channels):
        if STORAGE_MODE == "discord":
            # Code pour mettre à jour les messages Discord
            channel = self.bot.get_channel(BOT_STORAGE_CHANNEL_ID)
            important_msg = await channel.fetch_message(IMPORTANT_MSG_ID)
            excluded_msg  = await channel.fetch_message(EXCLUDED_MSG_ID)
            await important_msg.edit(content=json.dumps({"important_channels": important_channels}, indent=2))
            await excluded_msg.edit(content=json.dumps({"excluded_channels": excluded_channels}, indent=2))
        else:
            # Mode JSON
            data = {"important_channels": important_channels, "excluded_channels": excluded_channels}
            with open(self.json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
