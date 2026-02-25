import discord
from discord.ext import commands
import os

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=",", intents=intents, help_command=None)

BOT_NAME = "Xrenza"

# ===============================
# READY EVENT
# ===============================

@bot.event
async def on_ready():
    print(f"{BOT_NAME} is online!")

# ===============================
# HELP COMMAND
# ===============================

@bot.command()
async def help(ctx):
    embed = discord.Embed(
        title=f"🔥 {BOT_NAME} Help Menu",
        description="All Available Commands",
        color=discord.Color.purple()
    )

    embed.add_field(name="🛡️ Antinuke", value="protect, antinuke, nightmode", inline=False)
    embed.add_field(name="🤖 Automod", value="automod", inline=False)
    embed.add_field(name="🔨 Moderation", value="ban, kick, mute, warn, purge, role, lock", inline=False)
    embed.add_field(name="⚙️ General", value="ping, avatar, serverinfo, userinfo, stats", inline=False)
    embed.add_field(name="🎉 Giveaway", value="gstart, gend, greroll, gjoins", inline=False)
    embed.add_field(name="👑 Staff", value="crew, promote, demote", inline=False)

    await ctx.send(embed=embed)

# ===============================
# GENERAL COMMANDS
# ===============================

@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong!")

@bot.command()
async def avatar(ctx):
    await ctx.send(ctx.author.avatar.url if ctx.author.avatar else "No avatar.")

@bot.command()
async def serverinfo(ctx):
    await ctx.send(f"Server Name: {ctx.guild.name}")

@bot.command()
async def userinfo(ctx):
    await ctx.send(f"User: {ctx.author}")

# ===============================
# MODERATION COMMANDS
# ===============================

@bot.command()
async def ban(ctx):
    await ctx.send("🔨 Ban command executed (example).")

@bot.command()
async def kick(ctx):
    await ctx.send("👢 Kick command executed (example).")

@bot.command()
async def mute(ctx):
    await ctx.send("🔇 Mute command executed (example).")

@bot.command()
async def unmute(ctx):
    await ctx.send("🔊 Unmute command executed (example).")

@bot.command()
async def warn(ctx):
    await ctx.send("⚠️ Warn command executed (example).")

@bot.command()
async def purge(ctx):
    await ctx.send("🧹 Purge command executed (example).")

@bot.command()
async def lock(ctx):
    await ctx.send("🔒 Channel locked (example).")

@bot.command()
async def unlock(ctx):
    await ctx.send("🔓 Channel unlocked (example).")

# ===============================
# ANTINUKE GROUP
# ===============================

@bot.group(invoke_without_command=True)
async def antinuke(ctx):
    await ctx.send("🛡️ Antinuke main command.")

@antinuke.command()
async def enable(ctx):
    await ctx.send("Antinuke Enabled.")

@antinuke.command()
async def disable(ctx):
    await ctx.send("Antinuke Disabled.")

@antinuke.command()
async def whitelist(ctx):
    await ctx.send("Antinuke whitelist command.")

@antinuke.command()
async def logging(ctx):
    await ctx.send("Antinuke logging configured.")

@antinuke.command()
async def config(ctx):
    await ctx.send("Antinuke config panel.")

# ===============================
# AUTOMOD GROUP
# ===============================

@bot.group(invoke_without_command=True)
async def automod(ctx):
    await ctx.send("🤖 Automod main command.")

@automod.command()
async def enable(ctx):
    await ctx.send("Automod Enabled.")

@automod.command()
async def disable(ctx):
    await ctx.send("Automod Disabled.")

@automod.command()
async def reset(ctx):
    await ctx.send("Automod Reset.")

# ===============================
# GIVEAWAY
# ===============================

@bot.command()
async def gstart(ctx):
    await ctx.send("🎉 Giveaway Started!")

@bot.command()
async def gend(ctx):
    await ctx.send("🎉 Giveaway Ended!")

@bot.command()
async def greroll(ctx):
    await ctx.send("🎉 Giveaway Rerolled!")

@bot.command()
async def gjoins(ctx):
    await ctx.send("🎉 Giveaway Joins Listed!")

# ===============================
# AUTOROLE
# ===============================

@bot.group(invoke_without_command=True)
async def autorole(ctx):
    await ctx.send("Autorole main command.")

@autorole.command()
async def humans(ctx):
    await ctx.send("Autorole humans command.")

@autorole.command()
async def bots(ctx):
    await ctx.send("Autorole bots command.")

# ===============================
# AUTOREACT
# ===============================

@bot.group(invoke_without_command=True)
async def autoreact(ctx):
    await ctx.send("Autoreact main command.")

@autoreact.command()
async def add(ctx):
    await ctx.send("Autoreact added.")

@autoreact.command()
async def remove(ctx):
    await ctx.send("Autoreact removed.")

# ===============================
# IGNORE
# ===============================

@bot.group(invoke_without_command=True)
async def ignore(ctx):
    await ctx.send("Ignore main command.")

@ignore.command()
async def command(ctx):
    await ctx.send("Ignore command setting.")

@ignore.command()
async def user(ctx):
    await ctx.send("Ignore user setting.")

# ===============================
# STICKY
# ===============================

@bot.group(invoke_without_command=True)
async def sticky(ctx):
    await ctx.send("Sticky main command.")

@sticky.command()
async def set(ctx):
    await ctx.send("Sticky set.")

@sticky.command()
async def remove(ctx):
    await ctx.send("Sticky removed.")

# ===============================
# STAFF
# ===============================

@bot.group(invoke_without_command=True)
async def crew(ctx):
    await ctx.send("Crew system main.")

@crew.command()
async def setup(ctx):
    await ctx.send("Crew setup done.")

@bot.command()
async def promote(ctx):
    await ctx.send("User promoted.")

@bot.command()
async def demote(ctx):
    await ctx.send("User demoted.")

# ===============================
# RUN BOT
# ===============================

bot.run(os.getenv("TOKEN"))
