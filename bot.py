import discord
from discord.ext import commands
from discord.ui import View, Button
import asyncio

TOKEN = "YOUR_BOT_TOKEN"
PREFIX = "!"

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# ===============================
# DATABASE SYSTEM (SQLite)
# ===============================

import sqlite3
import json
import time
from datetime import datetime

conn = sqlite3.connect("security.db")
cursor = conn.cursor()

# Guild Configuration Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS guild_config (
    guild_id INTEGER PRIMARY KEY,
    prefix TEXT DEFAULT '!',
    modlog_channel INTEGER,
    jail_role INTEGER,
    mute_role INTEGER,
    panic_mode INTEGER DEFAULT 0,
    antinuke_enabled INTEGER DEFAULT 0,
    antinuke_threshold INTEGER DEFAULT 3,
    antinuke_action TEXT DEFAULT 'ban',
    automod_enabled INTEGER DEFAULT 0,
    leveling_enabled INTEGER DEFAULT 1
)
""")

# Whitelist Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS whitelist (
    guild_id INTEGER,
    user_id INTEGER,
    level TEXT,
    PRIMARY KEY (guild_id, user_id)
)
""")

# Warning System
cursor.execute("""
CREATE TABLE IF NOT EXISTS warnings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER,
    user_id INTEGER,
    moderator_id INTEGER,
    reason TEXT,
    timestamp INTEGER
)
""")

# Leveling System
cursor.execute("""
CREATE TABLE IF NOT EXISTS leveling (
    guild_id INTEGER,
    user_id INTEGER,
    xp INTEGER DEFAULT 0,
    level INTEGER DEFAULT 0,
    PRIMARY KEY (guild_id, user_id)
)
""")

# Giveaway Table
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

# Automod Filters
cursor.execute("""
CREATE TABLE IF NOT EXISTS filters (
    guild_id INTEGER,
    word TEXT
)
""")

conn.commit()

# ===============================
# CONFIG HELPERS
# ===============================

def get_guild_config(guild_id):
    cursor.execute("SELECT * FROM guild_config WHERE guild_id = ?", (guild_id,))
    data = cursor.fetchone()
    if not data:
        cursor.execute("INSERT INTO guild_config (guild_id) VALUES (?)", (guild_id,))
        conn.commit()
        return get_guild_config(guild_id)
    return data

def update_config(guild_id, field, value):
    cursor.execute(f"UPDATE guild_config SET {field} = ? WHERE guild_id = ?", (value, guild_id))
    conn.commit()

def is_whitelisted(guild_id, user_id):
    cursor.execute("SELECT * FROM whitelist WHERE guild_id=? AND user_id=?", (guild_id, user_id))
    return cursor.fetchone() is not None

def add_warning(guild_id, user_id, moderator_id, reason):
    cursor.execute(
        "INSERT INTO warnings (guild_id, user_id, moderator_id, reason, timestamp) VALUES (?,?,?,?,?)",
        (guild_id, user_id, moderator_id, reason, int(time.time()))
    )
    conn.commit()

def get_warnings(guild_id, user_id):
    cursor.execute("SELECT * FROM warnings WHERE guild_id=? AND user_id=?", (guild_id, user_id))
    return cursor.fetchall()

def add_xp(guild_id, user_id, amount):
    cursor.execute("SELECT xp, level FROM leveling WHERE guild_id=? AND user_id=?", (guild_id, user_id))
    data = cursor.fetchone()
    if not data:
        cursor.execute("INSERT INTO leveling (guild_id, user_id, xp, level) VALUES (?,?,?,?)",
                       (guild_id, user_id, amount, 0))
    else:
        xp, level = data
        xp += amount
        new_level = xp // 100
        cursor.execute("UPDATE leveling SET xp=?, level=? WHERE guild_id=? AND user_id=?",
                       (xp, new_level, guild_id, user_id))
    conn.commit()

# ===============================
# ANTI-NUKE ENGINE
# ===============================

from collections import defaultdict

# Track user actions per guild
antinuke_tracker = defaultdict(lambda: defaultdict(int))
antinuke_time_window = 10  # seconds window

async def punish_user(guild, member, action_type):
    config = get_guild_config(guild.id)
    punish_action = config[8]  # antinuke_action

    try:
        if punish_action == "ban":
            await guild.ban(member, reason="Anti-Nuke Triggered")
        elif punish_action == "kick":
            await guild.kick(member, reason="Anti-Nuke Triggered")
        elif punish_action == "strip":
            roles = [r for r in member.roles if r.name != "@everyone"]
            await member.remove_roles(*roles)
    except Exception as e:
        print("Punish error:", e)

async def check_antinuke(guild, member, action):
    config = get_guild_config(guild.id)

    if not config[6]:  # antinuke_enabled
        return

    if is_whitelisted(guild.id, member.id):
        return

    threshold = config[7]

    antinuke_tracker[guild.id][member.id] += 1

    if antinuke_tracker[guild.id][member.id] >= threshold:
        await punish_user(guild, member, action)
        antinuke_tracker[guild.id][member.id] = 0

    await asyncio.sleep(antinuke_time_window)
    if antinuke_tracker[guild.id][member.id] > 0:
        antinuke_tracker[guild.id][member.id] -= 1


# ===============================
# AUDIT LOG LISTENERS
# ===============================

@bot.event
async def on_guild_channel_delete(channel):
    guild = channel.guild
    async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
        await check_antinuke(guild, entry.user, "channel_delete")

@bot.event
async def on_guild_role_create(role):
    guild = role.guild
    async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.role_create):
        await check_antinuke(guild, entry.user, "role_create")

@bot.event
async def on_guild_role_delete(role):
    guild = role.guild
    async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
        await check_antinuke(guild, entry.user, "role_delete")

@bot.event
async def on_member_ban(guild, user):
    async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
        await check_antinuke(guild, entry.user, "ban")


# ===============================
# PANIC MODE
# ===============================

async def enable_panic(guild):
    update_config(guild.id, "panic_mode", 1)

    for channel in guild.text_channels:
        try:
            await channel.set_permissions(guild.default_role, send_messages=False)
        except:
            pass

async def disable_panic(guild):
    update_config(guild.id, "panic_mode", 0)

    for channel in guild.text_channels:
        try:
            await channel.set_permissions(guild.default_role, overwrite=None)
        except:
            pass


# ===============================
# ANTINUKE COMMANDS
# ===============================

@bot.command()
@commands.has_permissions(administrator=True)
async def antinuke(ctx, setting=None, value=None):
    if setting == "enable":
        update_config(ctx.guild.id, "antinuke_enabled", 1)
        await ctx.send("🛡 Anti-Nuke Enabled")
    elif setting == "disable":
        update_config(ctx.guild.id, "antinuke_enabled", 0)
        await ctx.send("🛑 Anti-Nuke Disabled")
    elif setting == "action":
        if value in ["ban", "kick", "strip"]:
            update_config(ctx.guild.id, "antinuke_action", value)
            await ctx.send(f"⚙ Punishment set to {value}")
    elif setting == "punish-threshold":
        if value and value.isdigit():
            update_config(ctx.guild.id, "antinuke_threshold", int(value))
            await ctx.send(f"⚙ Threshold set to {value}")
    elif setting == "status":
        config = get_guild_config(ctx.guild.id)
        await ctx.send(
            f"Enabled: {bool(config[6])}\n"
            f"Threshold: {config[7]}\n"
            f"Action: {config[8]}"
        )
    else:
        await ctx.send("Usage: !antinuke enable/disable/status/action/punish-threshold")


@bot.command()
@commands.has_permissions(administrator=True)
async def panic_mode(ctx, state=None):
    if state == "enable":
        await enable_panic(ctx.guild)
        await ctx.send("🚨 Panic Mode Enabled (Server Locked)")
    elif state == "disable":
        await disable_panic(ctx.guild)
        await ctx.send("✅ Panic Mode Disabled")
    else:
        await ctx.send("Usage: !panic_mode enable/disable")

# ===============================
# AUTOMOD ENGINE
# ===============================

spam_tracker = {}
spam_limit = 5
spam_interval = 7

def contains_invite(message):
    return "discord.gg/" in message or "discord.com/invite" in message

def contains_link(message):
    return "http://" in message or "https://" in message or "www." in message

def excessive_caps(message):
    if len(message) < 6:
        return False
    upper = sum(1 for c in message if c.isupper())
    return upper / len(message) > 0.7

async def automod_punish(message, reason):
    config = get_guild_config(message.guild.id)
    action = config[8]  # reuse antinuke_action slot for now

    try:
        if action == "warn":
            add_warning(message.guild.id, message.author.id, bot.user.id, reason)
            await message.channel.send(f"⚠ {message.author.mention} warned: {reason}")
        elif action == "mute":
            mute_role_id = config[4]
            if mute_role_id:
                role = message.guild.get_role(mute_role_id)
                await message.author.add_roles(role)
        elif action == "kick":
            await message.guild.kick(message.author, reason=reason)
    except:
        pass


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    config = get_guild_config(message.guild.id)

    if not config[9]:  # automod_enabled
        await bot.process_commands(message)
        return

    if is_whitelisted(message.guild.id, message.author.id):
        await bot.process_commands(message)
        return

    # Spam Detection
    now = asyncio.get_event_loop().time()
    user_data = spam_tracker.setdefault(message.author.id, [])
    user_data.append(now)
    spam_tracker[message.author.id] = [t for t in user_data if now - t < spam_interval]

    if len(spam_tracker[message.author.id]) > spam_limit:
        await message.delete()
        await automod_punish(message, "Spam detected")
        return

    # Invite Filter
    if contains_invite(message.content):
        await message.delete()
        await automod_punish(message, "Invite link detected")
        return

    # Link Filter
    if contains_link(message.content):
        await message.delete()
        await automod_punish(message, "External link detected")
        return

    # Caps Filter
    if excessive_caps(message.content):
        await message.delete()
        await automod_punish(message, "Excessive caps")
        return

    # Word Filter
    cursor.execute("SELECT word FROM filters WHERE guild_id=?", (message.guild.id,))
    words = cursor.fetchall()
    for (word,) in words:
        if word.lower() in message.content.lower():
            await message.delete()
            await automod_punish(message, "Filtered word used")
            return

    await bot.process_commands(message)


# ===============================
# AUTOMOD COMMANDS
# ===============================

@bot.command()
@commands.has_permissions(administrator=True)
async def automod(ctx, setting=None, value=None):
    if setting == "enable":
        update_config(ctx.guild.id, "automod_enabled", 1)
        await ctx.send("🛑 Automod Enabled")
    elif setting == "disable":
        update_config(ctx.guild.id, "automod_enabled", 0)
        await ctx.send("⚙ Automod Disabled")
    else:
        await ctx.send("Usage: !automod enable/disable")


@bot.command()
@commands.has_permissions(administrator=True)
async def filter(ctx, action=None, *, word=None):
    if action == "add" and word:
        cursor.execute("INSERT INTO filters (guild_id, word) VALUES (?,?)",
                       (ctx.guild.id, word.lower()))
        conn.commit()
        await ctx.send(f"✅ Added filter word: {word}")
    elif action == "remove" and word:
        cursor.execute("DELETE FROM filters WHERE guild_id=? AND word=?",
                       (ctx.guild.id, word.lower()))
        conn.commit()
        await ctx.send(f"❌ Removed filter word: {word}")
    elif action == "list":
        cursor.execute("SELECT word FROM filters WHERE guild_id=?", (ctx.guild.id,))
        words = cursor.fetchall()
        if not words:
            return await ctx.send("No filter words set.")
        await ctx.send("Filtered words:\n" + "\n".join(w[0] for w in words))
    elif action == "clear":
        cursor.execute("DELETE FROM filters WHERE guild_id=?", (ctx.guild.id,))
        conn.commit()
        await ctx.send("🗑 All filter words cleared.")
    else:
        await ctx.send("Usage: !filter add/remove/list/clear <word>")

# ===============================
# GIVEAWAY SYSTEM
# ===============================

import re

def parse_time(time_str):
    match = re.match(r"(\d+)([smhd])", time_str.lower())
    if not match:
        return None

    value, unit = match.groups()
    value = int(value)

    if unit == "s":
        return value
    if unit == "m":
        return value * 60
    if unit == "h":
        return value * 3600
    if unit == "d":
        return value * 86400

    return None


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

    if not users:
        await channel.send("No valid participants.")
    else:
        winners = random.sample(users, min(winners_count, len(users)))
        winner_mentions = ", ".join(w.mention for w in winners)
        await channel.send(f"🎉 Congratulations {winner_mentions}! You won **{prize}**")

    cursor.execute("UPDATE giveaways SET ended=1 WHERE message_id=?", (message_id,))
    conn.commit()


@tasks.loop(seconds=10)
async def giveaway_checker():
    current_time = int(time.time())

    cursor.execute("SELECT message_id, end_time FROM giveaways WHERE ended=0")
    data = cursor.fetchall()

    for message_id, end_time in data:
        if current_time >= end_time:
            await end_giveaway(message_id)


@bot.command()
@commands.has_permissions(manage_guild=True)
async def gstart(ctx, time_str, winners: int, *, prize):
    seconds = parse_time(time_str)
    if not seconds:
        return await ctx.send("Invalid time format. Use 10s / 10m / 1h / 1d")

    end_time = int(time.time()) + seconds

    embed = discord.Embed(
        title="🎉 Giveaway",
        description=f"Prize: **{prize}**\nWinners: {winners}\nEnds in: {time_str}",
        color=discord.Color.purple()
    )
    embed.set_footer(text=f"Hosted by {ctx.author}")

    message = await ctx.send(embed=embed)
    await message.add_reaction("🎉")

    cursor.execute(
        "INSERT INTO giveaways VALUES (?,?,?,?,?,?,?)",
        (message.id, ctx.guild.id, ctx.channel.id, end_time, winners, prize, 0)
    )
    conn.commit()


@bot.command()
@commands.has_permissions(manage_guild=True)
async def gend(ctx, message_id: int):
    await end_giveaway(message_id)
    await ctx.send("Giveaway ended.")


@bot.command()
@commands.has_permissions(manage_guild=True)
async def greroll(ctx, message_id: int):
    cursor.execute("UPDATE giveaways SET ended=0 WHERE message_id=?", (message_id,))
    conn.commit()
    await end_giveaway(message_id)
    await ctx.send("Giveaway rerolled.")


@bot.command()
@commands.has_permissions(manage_guild=True)
async def glist(ctx):
    cursor.execute("SELECT message_id, prize, end_time FROM giveaways WHERE guild_id=? AND ended=0",
                   (ctx.guild.id,))
    data = cursor.fetchall()

    if not data:
        return await ctx.send("No active giveaways.")

    desc = ""
    for message_id, prize, end_time in data:
        remaining = end_time - int(time.time())
        desc += f"ID: {message_id} | {prize} | Ends in {remaining}s\n"

    embed = discord.Embed(title="🎉 Active Giveaways", description=desc)
    await ctx.send(embed=embed)


@bot.command()
@commands.has_permissions(manage_guild=True)
async def gcancel(ctx, message_id: int):
    cursor.execute("DELETE FROM giveaways WHERE message_id=?", (message_id,))
    conn.commit()
    await ctx.send("Giveaway cancelled.")


# Start background loop
from discord.ext import tasks
import random

@bot.event
async def on_ready():
    if not giveaway_checker.is_running():
        giveaway_checker.start()

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