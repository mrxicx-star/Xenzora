import discord
from discord.ext import commands, tasks
from discord.ui import View, Button
import asyncio
import sqlite3
import time
import random
import re
import os
from collections import defaultdict

# ===============================
# TOKEN FROM SECRETS
# ===============================
TOKEN = os.getenv("TOKEN")  # Make sure secret name is TOKEN
if not TOKEN:
    raise ValueError("TOKEN not found in environment variables!")

PREFIX = "."
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# ==================================================
# DATABASE SETUP
# ==================================================
conn = sqlite3.connect("security.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS guild_config (
    guild_id INTEGER PRIMARY KEY,
    antinuke_enabled INTEGER DEFAULT 0,
    antinuke_threshold INTEGER DEFAULT 3,
    antinuke_action TEXT DEFAULT 'ban',
    automod_enabled INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS whitelist (
    guild_id INTEGER,
    user_id INTEGER,
    PRIMARY KEY (guild_id, user_id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS filters (
    guild_id INTEGER,
    word TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS giveaways (
    message_id INTEGER PRIMARY KEY,
    guild_id INTEGER,
    channel_id INTEGER,
    end_time INTEGER,
    winners INTEGER,
    prize TEXT,
    ended INTEGER DEFAULT 0
)
""")
conn.commit()

# ==================================================
# CONFIG HELPERS
# ==================================================
def get_config(guild_id):
    cursor.execute("SELECT * FROM guild_config WHERE guild_id=?", (guild_id,))
    data = cursor.fetchone()
    if not data:
        cursor.execute("INSERT INTO guild_config (guild_id) VALUES (?)", (guild_id,))
        conn.commit()
        return get_config(guild_id)
    return data

def update_config(guild_id, field, value):
    cursor.execute(f"UPDATE guild_config SET {field}=? WHERE guild_id=?", (value, guild_id))
    conn.commit()

def is_whitelisted(guild_id, user_id):
    cursor.execute("SELECT * FROM whitelist WHERE guild_id=? AND user_id=?", (guild_id, user_id))
    return cursor.fetchone() is not None

# ==================================================
# ANTI-NUKE
# ==================================================
antinuke_tracker = defaultdict(lambda: defaultdict(int))
time_window = 10

async def punish(guild, member):
    config = get_config(guild.id)
    action = config[3]
    try:
        if action == "ban":
            await guild.ban(member, reason="Anti-Nuke Triggered")
        elif action == "kick":
            await guild.kick(member, reason="Anti-Nuke Triggered")
    except:
        pass

async def check_antinuke(guild, member):
    config = get_config(guild.id)
    if not config[1]:
        return
    if is_whitelisted(guild.id, member.id):
        return

    threshold = config[2]
    antinuke_tracker[guild.id][member.id] += 1

    if antinuke_tracker[guild.id][member.id] >= threshold:
        await punish(guild, member)
        antinuke_tracker[guild.id][member.id] = 0

    await asyncio.sleep(time_window)
    if antinuke_tracker[guild.id][member.id] > 0:
        antinuke_tracker[guild.id][member.id] -= 1

@bot.event
async def on_guild_channel_delete(channel):
    async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
        await check_antinuke(channel.guild, entry.user)

# ==================================================
# AUTOMOD
# ==================================================
spam_tracker = {}

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    config = get_config(message.guild.id)

    now = time.time()
    spam_tracker.setdefault(message.author.id, []).append(now)
    spam_tracker[message.author.id] = [t for t in spam_tracker[message.author.id] if now - t < 7]

    if config[4]:  # automod_enabled
        if len(spam_tracker[message.author.id]) > 5:
            await message.delete()
            return

        if "discord.gg/" in message.content.lower():
            await message.delete()
            return

        if "http://" in message.content.lower() or "https://" in message.content.lower():
            await message.delete()
            return

        cursor.execute("SELECT word FROM filters WHERE guild_id=?", (message.guild.id,))
        words = cursor.fetchall()
        for (word,) in words:
            if word in message.content.lower():
                await message.delete()
                return

    # Always process commands
    await bot.process_commands(message)

# ==================================================
# GIVEAWAY SYSTEM
# ==================================================
def parse_time(time_str):
    match = re.match(r"(\d+)([smhd])", time_str.lower())
    if not match:
        return None
    value, unit = match.groups()
    value = int(value)
    return {"s":1,"m":60,"h":3600,"d":86400}[unit] * value

async def end_giveaway(message_id):
    cursor.execute("SELECT * FROM giveaways WHERE message_id=?", (message_id,))
    data = cursor.fetchone()
    if not data:
        return

    _, guild_id, channel_id, end_time, winners_count, prize, ended = data
    if ended:
        return

    guild = bot.get_guild(guild_id)
    channel = guild.get_channel(channel_id)
    message = await channel.fetch_message(message_id)

    users = []
    for reaction in message.reactions:
        if str(reaction.emoji) == "🎉":
            async for user in reaction.users():
                if not user.bot:
                    users.append(user)

    if users:
        winners = random.sample(users, min(winners_count, len(users)))
        await channel.send(f"🎉 Winner(s): {', '.join(w.mention for w in winners)} | Prize: {prize}")

    cursor.execute("UPDATE giveaways SET ended=1 WHERE message_id=?", (message_id,))
    conn.commit()

@tasks.loop(seconds=10)
async def giveaway_loop():
    cursor.execute("SELECT message_id, end_time FROM giveaways WHERE ended=0")
    for message_id, end_time in cursor.fetchall():
        if int(time.time()) >= end_time:
            await end_giveaway(message_id)

@bot.command()
@commands.has_permissions(manage_guild=True)
async def gstart(ctx, time_str, winners: int, *, prize):
    seconds = parse_time(time_str)
    if not seconds:
        return await ctx.send("Use format: 10s / 10m / 1h / 1d")

    end_time = int(time.time()) + seconds

    embed = discord.Embed(
        title="🎉 Giveaway",
        description=f"Prize: **{prize}**\nWinners: {winners}\nDuration: {time_str}",
        color=discord.Color.purple()
    )

    msg = await ctx.send(embed=embed)
    await msg.add_reaction("🎉")

    cursor.execute("INSERT INTO giveaways VALUES (?,?,?,?,?,?,0)",
                   (msg.id, ctx.guild.id, ctx.channel.id, end_time, winners, prize))
    conn.commit()

# ==================================================
# ANTI-NUKE & AUTOMOD COMMANDS
# ==================================================
@bot.command()
@commands.has_permissions(administrator=True)
async def antinuke(ctx, state=None):
    if state == "enable":
        update_config(ctx.guild.id, "antinuke_enabled", 1)
        await ctx.send("Anti-Nuke Enabled")
    elif state == "disable":
        update_config(ctx.guild.id, "antinuke_enabled", 0)
        await ctx.send("Anti-Nuke Disabled")

@bot.command()
@commands.has_permissions(administrator=True)
async def automod(ctx, state=None):
    if state == "enable":
        update_config(ctx.guild.id, "automod_enabled", 1)
        await ctx.send("Automod Enabled")
    elif state == "disable":
        update_config(ctx.guild.id, "automod_enabled", 0)
        await ctx.send("Automod Disabled")

# ==================================================
# HELP COMMAND (Single Embed, Xrenza Style)
# ==================================================
@bot.command()
async def help(ctx):
    embed = discord.Embed(
        title="Xrenza • Help Menu",
        description=(
            "<:xrenza_antinuke:1396337103897493585> **Security & Anti-Nuke**\n"
            "`admin`, `admin add`, `admin remove`, `antinuke`, `antinuke enable`, `antinuke disable`, `extraowner`, `mainrole`, `modrole`, `nightmode`, `unwhitelist`, `whitelist`, `whitelisted`, `whitelistreset`\n\n"
            "<:xrenza_automod:1396412187270053960> **Automod**\n"
            "`automod`, `automod antispam setup`, `automod antilink setup`, `automod antibadwords setup`, `automod antizalgo setup`, `automod anticaps setup`, `automod whitelist manage`, `automod config`\n\n"
            "<:xrenza_moderation:1396336374361231421> **Moderation**\n"
            "`ban`, `kick`, `softban`, `unban`, `unbanall`, `mute`, `unmute`, `unmuteall`, `warn`, `warn reset`, `warn remove`, `nick`, `lock`, `unlock`, `lockall`, `unlockall`, `purge`\n\n"
            "<:xrenza_logs:1396413625471598705> **Logs & Config**\n"
            "`command`, `command config`, `command bypass role add`, `command bypass role remove`, `command bypass user add`, `command bypass user remove`, `autologs`, `channellog`, `memberlog`, `messagelog`, `modlog`, `resetlog`, `rolelog`, `serverlog`, `showlogs`, `voicelog`\n\n"
            "<:xrenza_customrole:1396419397861642370> **Custom / Auto**\n"
            "`customrole`, `customrole add`, `customrole remove`, `selfrole`, `selfrole setup`, `selfrole list`, `selfrole delete`, `selfrole reset`, `selfrole cleanup`, `selfrole edit`, `autoresponder`, `autoresponder add`, `autoresponder remove`, `autoresponder list`, `autoresponder test`, `autoresponder reset`\n\n"
            "<:xrenza_giveaway:1396336538463506463> **Giveaways**\n"
            "`giveaway`, `giveaway start`, `giveaway end`, `giveaway list`, `giveaway reroll`\n\n"
            "<:xrenza_settings:1396336923668123680> **Utility & Info**\n"
            "`afk`, `avatar`, `banner`, `banner user`, `banner server`, `setboost`, `boostcount`, `channelinfo`, `embed`, `help`, `invite`, `membercount`, `ping`, `roleicon`, `roleinfo`, `servericon`, `serverinfo`, `stats`, `steal`, `uptime`, `userinfo`, `vote`, `infoboard`, `infoboard create`, `infoboard delete`, `infoboard list`, `infoboard resend`\n\n"
            "<:xrenza_Autoresponder:1399667534550138910> **Fun / Media / Voice**\n"
            "`autonick`, `autonick setup`, `autonick config`, `autonick reset`, `cute`, `iq`, `wouldyourather`, `ad`, `affect`, `badstonk`, `batslap`, `beautiful`, `bed`, `blur`, `bobross`, `caption`, `clown`, `confused`, `dare`, `dblack`, `dblue`, `deepfry`, `delete`, `doublestonk`, `facepalm`, `gay`, `greyscale`, `heartbreaking`, `hitler`, `invert`, `jail`, `kiss`, `lisa`, `mms`, `reaction`, `spank`, `stonk`, `tictactoe`, `triggered`, `truth`"
        ),
        color=discord.Color.blurple()
    )
    embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)

# ==================================================
# READY
# ==================================================
@bot.event
async def on_ready():
    print(f"Xrenza Online as {bot.user}")
    if not giveaway_loop.is_running():
        giveaway_loop.start()

bot.run(TOKEN)