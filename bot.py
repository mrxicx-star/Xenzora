import discord
from discord.ext import commands
from discord.ui import View, Button
import asyncio

TOKEN = "YOUR_BOT_TOKEN"
PREFIX = "!"

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# ===============================
# HELP DATA (ALL YOUR COMMANDS)
# ===============================

HELP_PAGES = [

("🛡 Moderation", """
`!ban <user>`
`!unban <user>`
`!kick <user>`
`!mute <user>`
`!unmute <user>`
`!timeout <user>`
`!untimeout <user>`
`!warn <user>`
`!unwarn <id>`
`!warnings <user>`
`!clearwarns <user>`
`!purge <amount>`
`!purge-bots`
`!purge-user <user>`
`!purge-links`
`!purge-attachments`
`!lock`
`!unlock`
`!hide`
`!unhide`
`!slowmode <seconds>`
`!nick <user> <name>`
`!role add/remove/create/delete/color/rename`
`!vmute`
`!vunmute`
`!vdeafen`
`!vundeafen`
`!vkick`
`!softban`
`!nuke`
`!clone`
`!tempban`
`!massban`
`!masskick`
`!modlog`
`!jail`
`!unjail`
`!set-jail`
"""),

("🚨 Antinuke", """
`!antinuke enable/disable/status/settings`
`!antinuke action`
`!antinuke log`
`!antinuke punish-threshold`
`!anti-bot`
`!anti-link`
`!anti-spam`
`!anti-alt`
`!anti-webhook`
`!anti-vanity`
`!limit ban/kick/channel-create/etc`
`!recovery-setup`
`!panic-mode`
`!secure-server`
`!quarantine`
`!unquarantine`
"""),

("✅ Whitelist", """
`!whitelist add/remove/list/reset/show`
`!trust add/remove/list`
`!ignore channel/user/role`
`!unignore channel/user/role`
`!whitelist-admin`
`!whitelist-mod`
"""),

("⚙ Config & Prefix", """
`!prefix`
`!prefix reset`
`!config`
`!config view`
`!config autorole`
`!config welcome-channel`
`!config leave-channel`
`!config welcome-msg`
`!config leave-msg`
`!config boost-channel`
`!config logs-all`
`!config automod`
`!config starboard`
`!config suggest-channel`
`!config invite-tracker`
`!config sticky-roles`
`!config mute-role`
`!config jail-role`
`!setup`
`!reset-server`
"""),

("📊 Help & Info", """
`!help`
`!info`
`!stats`
`!ping`
`!uptime`
`!invite`
`!support`
`!serverinfo`
`!userinfo`
`!membercount`
`!roleinfo`
`!channelinfo`
`!avatar`
`!banner`
`!boosters`
`!permissions`
`!check-security`
`!bot-info`
"""),

("🛑 Automod & Filters", """
`!filter add/remove/list/clear`
`!automod caps`
`!automod links`
`!automod invites`
`!automod massmention`
`!automod lines`
`!automod spam`
`!automod badwords`
`!automod zalgo`
`!automod bypass`
`!automod punish`
"""),

("🎉 Giveaway", """
`!gstart`
`!gend`
`!greroll`
`!glist`
`!gcancel`
"""),

("🏆 Leveling", """
`!rank`
`!leaderboard`
`!level-config`
`!level-role add/remove`
`!level-reset`
`!level-multiplier`
"""),

("🎭 Utility / Fun", """
`!poll`
`!embed`
`!dm`
`!say`
`!remind`
`!calculator`
`!weather`
`!translate`
`!urban`
`!afk`
`!snipe`
`!editsnipe`
`!react`
`!steal`
`!enlarge`
""")

]

# ===============================
# PAGINATION VIEW
# ===============================

class HelpView(View):
    def __init__(self, ctx):
        super().__init__(timeout=120)
        self.ctx = ctx
        self.page = 0

    async def update_embed(self, interaction):
        title, content = HELP_PAGES[self.page]
        embed = discord.Embed(
            title=title,
            description=content,
            color=discord.Color.blurple()
        )
        embed.set_footer(text=f"Page {self.page+1}/{len(HELP_PAGES)}")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="⬅ Previous", style=discord.ButtonStyle.grey)
    async def previous(self, interaction: discord.Interaction, button: Button):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("Not for you.", ephemeral=True)
        self.page = (self.page - 1) % len(HELP_PAGES)
        await self.update_embed(interaction)

    @discord.ui.button(label="Next ➡", style=discord.ButtonStyle.grey)
    async def next(self, interaction: discord.Interaction, button: Button):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("Not for you.", ephemeral=True)
        self.page = (self.page + 1) % len(HELP_PAGES)
        await self.update_embed(interaction)

    @discord.ui.button(label="Close ❌", style=discord.ButtonStyle.red)
    async def close(self, interaction: discord.Interaction, button: Button):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("Not for you.", ephemeral=True)
        await interaction.message.delete()

# ===============================
# HELP COMMAND
# ===============================

@bot.command()
async def help(ctx):
    view = HelpView(ctx)
    title, content = HELP_PAGES[0]
    embed = discord.Embed(
        title=title,
        description=content,
        color=discord.Color.blurple()
    )
    embed.set_footer(text=f"Page 1/{len(HELP_PAGES)}")
    await ctx.send(embed=embed, view=view)

# ===============================
# AUTO PLACEHOLDER COMMANDS
# ===============================

@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong!")

# Generic placeholder generator
def create_placeholder(name):
    @bot.command(name=name)
    async def cmd(ctx, *args):
        await ctx.send("✅ Command executed.")
    return cmd

# Add every command automatically
ALL_COMMANDS = [
"ban","unban","kick","mute","unmute","timeout","untimeout",
"warn","unwarn","warnings","clearwarns","purge","lock","unlock",
"slowmode","nick","vmute","vunmute","vdeafen","vundeafen",
"vkick","softban","nuke","clone","tempban","massban","masskick",
"modlog","jail","unjail","set-jail",
"antinuke","quarantine","unquarantine",
"whitelist","trust","ignore","unignore",
"prefix","config","setup","reset-server",
"info","stats","uptime","invite","support",
"serverinfo","userinfo","membercount","roleinfo",
"channelinfo","avatar","banner","boosters",
"permissions","check-security","bot-info",
"filter","automod",
"gstart","gend","greroll","glist","gcancel",
"rank","leaderboard","level-config","level-reset",
"level-multiplier",
"poll","embed","dm","say","remind",
"calculator","weather","translate","urban",
"afk","snipe","editsnipe","react","steal","enlarge"
]

for cmd in ALL_COMMANDS:
    create_placeholder(cmd)

# ===============================
# RUN
# ===============================

bot.run(TOKEN)