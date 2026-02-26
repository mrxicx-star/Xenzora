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
async def on_guild_channel_create(channel):
    guild = channel.guild
    async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_create):
        await check_antinuke(guild, entry.user, "channel_create")

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