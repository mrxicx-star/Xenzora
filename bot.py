
import discord
from discord.ext import commands
from discord.ui import View, Button
import os

TOKEN = os.getenv("TOKEN")
PREFIX = "!"

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# ===== COMMAND CATEGORIES =====
COMMAND_CATEGORIES = {
    "🛡 Security & Anti-Nuke": [
        "/antinuke enable", "/antinuke disable", "/antinuke config",
        "/nightmode enable", "/nightmode disable", "/nightmode auto", "/nightmode status",
        "/admin add", "/admin remove", "/admin list", "/admin edit", "/admin reset",
        "/extraowner add", "/extraowner remove", "/mainrole add", "/mainrole remove",
        "/mainrole list", "/mainrole reset", "/modrole set", "/modrole view", "/modrole reset",
        "/whitelist user add", "/unwhitelist user", "/whitelisted", "/whitelistreset"
    ],
    "🤖 Automod": [
        "/automod antispam setup", "/automod antilink setup", "/automod antibadwords setup",
        "/automod antizalgo setup", "/automod anticaps setup", "/automod whitelist manage",
        "/automod config"
    ],
    "⚖️ Moderation": [
        "/ban <user> [reason]", "/kick <user> [reason]", "/mute <user> [duration]", 
        "/unmute <user>", "/unmuteall", "/softban <user>", "/unban <user>", 
        "/unbanall", "/warn <user> [reason]", "/warn list [user]", "/warn reset [user]",
        "/warn remove <warning_id>", "/nick <user> <new_nickname>"
    ],
    "🧰 Channel & Role Management": [
        "/role user add/remove", "/role all add/remove", "/role humans add/remove",
        "/role bots add/remove", "/role cancel", "/role status", "/lock <channel>",
        "/unlock <channel>", "/lockall", "/unlockall", "/hide <channel>", "/unhide <channel>",
        "/hideall", "/unhideall", "/block <user> <channel>", "/unblock <user> <channel>",
        "/slowmode <channel> <duration>"
    ],
    "📨 Message & Content Tools": [
        "/purge [filters]", "/snipe channel [index]"
    ],
    "📊 Server & Bot Info": [
        "/membercount", "/serverinfo", "/userinfo <user>", "/stats", "/ping", "/uptime", "/boostcount"
    ],
    "📜 Logs & Setup": [
        "/autologs set channel", "/channellog set/reset", "/memberlog set/reset", "/messagelog set/reset",
        "/modlog set/reset", "/rolelog set/reset", "/serverlog set/reset", "/voicelog set/reset",
        "/showlogs", "/resetlog"
    ],
    "🙋‍♂️ Utility & Misc": [
        "/help", "/prefix", "/invite", "/list", "/command config"
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
        # Split commands if too long for Discord (optional, can paginate more if needed)
        description = "\n".join(commands_list)
        embed = discord.Embed(
            title=f"Xrenza Bot • {category}",
            description=description,
            color=discord.Color.blurple()
        )
        embed.set_footer(text=f"Page {self.index+1}/{len(self.categories)} | Requested by {self.ctx.author}", icon_url=self.ctx.author.display_avatar.url)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="⬅", style=discord.ButtonStyle.grey)
    async def back(self, interaction: discord.Interaction, button: Button):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("This isn't your help menu!", ephemeral=True)
        self.index = (self.index - 1) % len(self.categories)
        await self.update_embed(interaction)

    @discord.ui.button(label="➡", style=discord.ButtonStyle.grey)
    async def forward(self, interaction: discord.Interaction, button: Button):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("This isn't your help menu!", ephemeral=True)
        self.index = (self.index + 1) % len(self.categories)
        await self.update_embed(interaction)

# ===== HELP COMMAND =====
@bot.command()
async def help(ctx):
    view = HelpView(ctx)
    first_category = list(COMMAND_CATEGORIES.keys())[0]
    description = "\n".join(COMMAND_CATEGORIES[first_category])
    embed = discord.Embed(
        title=f"Xrenza Bot • {first_category}",
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