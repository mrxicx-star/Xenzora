import discord
from discord.ext import commands
from discord.ui import View, Button
import os

TOKEN = os.getenv("TOKEN")
PREFIX = "!"

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# ===== COMMAND CATEGORIES WITH ALL COMMANDS =====
COMMAND_CATEGORIES = {
    "🛡 Security": [
        "admin", "admin add", "admin remove", "admin edit", "admin list", "admin reset", "admin cleanup",
        "antinuke", "antinuke enable", "antinuke disable", "antinuke config", "antinuke settings",
        "extraowner", "extraowner add", "extraowner remove", "extraowner list", "extraowner reset",
        "mainrole", "mainrole add", "mainrole remove", "mainrole list", "mainrole reset",
        "modrole", "modrole set", "modrole view", "modrole reset",
        "nightmode", "nightmode enable", "nightmode disable", "nightmode auto", "nightmode status",
        "nightmode reset", "nightmode logs", "unwhitelist", "whitelist", "whitelisted", "whitelistreset"
    ],
    "🤖 Automod": [
        "automod", "automod antispam setup", "automod antilink setup", "automod antibadwords setup",
        "automod antizalgo setup", "automod anticaps setup", "automod whitelist manage", "automod config"
    ],
    "⚖️ Moderation": [
        "ban", "kick", "softban", "unban", "unbanall", "mute", "unmute", "unmuteall", "warn", "warn reset",
        "warn remove", "warn @member", "nick", "lock", "unlock", "lockall", "unlockall", "purge",
        "purge @user/id", "purge bots", "purge humans", "purge links", "purge attachments", "purge mentions",
        "purge emojis", "purge stickers", "purge contains"
    ],
    "🧰 Role & Channel": [
        "role", "role user", "role all", "role humans", "role bots", "role cancel", "role status",
        "slowmode", "block", "unblock", "hide", "hideall", "unhide", "unhideall"
    ],
    "📜 Logs & Config": [
        "command", "command config", "command bypass role add", "command bypass role remove", "command bypass role list",
        "command bypass role reset", "command bypass user add", "command bypass user remove", "command bypass user list",
        "command bypass user reset", "command reset", "autologs", "channellog", "memberlog", "messagelog", "modlog",
        "resetlog", "rolelog", "serverlog", "showlogs", "voicelog"
    ],
    "🎉 Giveaways & SelfRole": [
        "giveaway", "giveaway start", "giveaway end", "giveaway list", "giveaway reroll",
        "selfrole", "selfrole setup", "selfrole list", "selfrole delete", "selfrole reset", "selfrole cleanup", "selfrole edit"
    ],
    "🙋 Utility & Misc": [
        "afk", "avatar", "banner", "banner user", "banner server", "setboost", "boostcount", "channelinfo",
        "embed", "help", "invite", "membercount", "ping", "roleicon", "roleinfo", "servericon", "serverinfo",
        "stats", "steal", "uptime", "userinfo", "vote", "infoboard", "infoboard create", "infoboard delete",
        "infoboard list", "infoboard resend", "prefix", "list", "list joinpos", "list muted", "list noroles",
        "list roles", "list admin", "list mod", "list bot", "list inrole", "list booster", "list bans",
        "list emojis", "list channels", "list activedeveloper", "list earlysupporter"
    ],
    "🛠 Custom / Auto": [
        "customrole", "customrole add", "customrole remove", "customrole reqrole add", "customrole reqrole remove",
        "customrole reqrole reset", "customrole reqrole list", "customrole list", "customrole reset", "customrole config",
        "autoresponder", "autoresponder add", "autoresponder remove", "autoresponder list", "autoresponder test", "autoresponder reset",
        "autorole humans add", "autorole humans remove", "autorole humans list", "autorole humans reset",
        "autorole bots add", "autorole bots remove", "autorole bots list", "autorole bots reset",
        "welcome", "welcome setup", "welcome test", "welcome delete", "welcome list", "welcome keyword", "welcome reset", "welcome edit"
    ],
    "🎤 Voice & Ticket": [
        "vcdeafen", "vcdeafenall", "vckick", "vckickall", "vcmoveall", "vcmute", "vcmuteall", "vcpull", "vcpush",
        "vcrole", "vcrole humans add", "vcrole humans remove", "vcrole humans list", "vcrole humans reset",
        "vcrole bots add", "vcrole bots remove", "vcrole bots list", "vcrole bots reset", "vcundeafen", "vcundeafenall",
        "vcunmute", "vcunmuteall", "voicemaster", "voicemaster setup", "voicemaster list", "voicemaster reset",
        "ticket", "ticket panel setup", "ticket panel list", "ticket panel reset"
    ],
    "📌 Fun & Media": [
        "sticky", "sticky add", "sticky remove", "sticky list", "sticky reset",
        "media", "media channel add", "media channel remove", "media channel list", "media channel reset",
        "media whitelist role add", "media whitelist role remove", "media whitelist role list", "media whitelist role reset",
        "media whitelist user add", "media whitelist user remove", "media whitelist user list", "media whitelist user reset",
        "autonick", "autonick setup", "autonick config", "autonick reset",
        "cute", "iq", "wouldyourather", "ad", "affect", "badstonk", "batslap", "beautiful", "bed", "blur",
        "bobross", "caption", "clown", "confused", "dare", "dblack", "dblue", "deepfry", "delete", "doublestonk",
        "facepalm", "gay", "greyscale", "heartbreaking", "hitler", "invert", "jail", "kiss", "lisa", "mms",
        "reaction", "spank", "stonk", "tictactoe", "triggered", "truth"
    ]
}

# ===== HELP VIEW WITH BUTTONS =====
class HelpView(View):
    def __init__(self, ctx):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.categories = list(COMMAND_CATEGORIES.keys())
        self.index = 0

    async def update_embed(self, interaction):
        category = self.categories[self.index]
        commands_list = COMMAND_CATEGORIES[category]
        # join commands with backticks
        description = " • ".join(f"`{cmd}`" for cmd in commands_list)
        embed = discord.Embed(
            title=f"Xrenza • {category}",
            description=description,
            color=discord.Color.blurple()
        )
        embed.set_footer(text=f"Page {self.index+1}/{len(self.categories)} | Requested by {self.ctx.author}", icon_url=self.ctx.author.display_avatar.url)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="⬅", style=discord.ButtonStyle.grey)
    async def back(self, interaction: discord.Interaction, button: Button):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("This is not your menu!", ephemeral=True)
        self.index = (self.index - 1) % len(self.categories)
        await self.update_embed(interaction)

    @discord.ui.button(label="➡", style=discord.ButtonStyle.grey)
    async def forward(self, interaction: discord.Interaction, button: Button):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("This is not your menu!", ephemeral=True)
        self.index = (self.index + 1) % len(self.categories)
        await self.update_embed(interaction)

# ===== HELP COMMAND =====
@bot.command()
async def help(ctx):
    view = HelpView(ctx)
    first_category = list(COMMAND_CATEGORIES.keys())[0]
    description = " • ".join(f"`{cmd}`" for cmd in COMMAND_CATEGORIES[first_category])
    embed = discord.Embed(
        title=f"Xrenza • {first_category}",
        description=description,
        color=discord.Color.blurple()
    )
    embed.set_footer(text=f"Page 1/{len(COMMAND_CATEGORIES)} | Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed, view=view)

# ===== READY =====
@bot.event
async def on_ready():
    print(f"Xrenza Online as {bot.user}")

bot.run(TOKEN)