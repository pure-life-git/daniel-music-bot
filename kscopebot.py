import asyncio
import datetime
import time
import math
import os
import random
import re
import pytz

import discord
from discord.ext import commands, tasks

import psycopg2

DEFAULT_PREFIX = "?"

TIME_TABLE = {
    "s": 1,
    "m": 60,
    "h": 3600,
    "d": 86400,
    "w": 604800,
}

ROLE_EMOTES = [
    "🔴", "🟠", "🟡", "🟢", "🔵", 
    "🟣", "🟤", "⚫", "⚪", "❤",
    "🧡", "💛", "💚", "💙", "💜",
    "🤎", "🖤", "🤍", "🔲", "🔳"
]

def col(hex:str):
    def hex2rgb(hex:str):
        hex = hex.lstrip('#')
        lv = len(hex)
        return tuple(int(hex[i:i + lv // 3], 16) for i in range(0, lv, lv //3))
    
    rgb = hex2rgb(hex)

    return discord.Color.from_rgb(rgb[0], rgb[1], rgb[2])



ROLE_COLORS = [
    col("#e52165"), col("#a2d5c6"), col("#077b8a"), col("#5c3c92"), col("#e75874"),
    col("#fbcbc9"), col("#7fe7dc"), col("#ffc13b"), col("#d9a5b3"), col("#1868ae"),
    col("#c6d7eb"), col("#408ec6"), col("#8a307f"), col("#6883bc"), col("#ff9a8d"),
    col("#da68a0"), col("#77c593"), col("#ced7d8"), col("#f162ff"), col("#daf2dc"),
    col("#4d5198"), col("#ffcce7"), col("#a9c0a6"), col("#cbd18f"), col("#9bc472"),
    col("#a7beae"), col("#1978a5"), col("#315f72"), col("#efb5a3"), col("#0073cf")
]

month_table = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

DATABASE_URL = os.environ['DATABASE_URL']
conn = psycopg2.connect(DATABASE_URL, sslmode='require')
cur = conn.cursor()
conn.autocommit = True

async def get_prefix(bot, message):
    cur.execute(f"SELECT prefix FROM prefixes WHERE server_id={message.guild.id};")
    return cur.fetchone()[0]

intents = discord.Intents.all()
bot = commands.Bot(command_prefix = get_prefix, description = "General purpose music bot", intents=intents, case_insensitive = True)
bot.remove_command('help')
bot_color = discord.Color.from_rgb(81,193,177)

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    await bot.change_presence(status = discord.Status.online, activity=discord.Game("?help"))
    check_reminders.start()

@bot.group(name='help', description = "Displays a link to the source code and README", aliases=["h"])
async def help(ctx):
    await ctx.send(f"`Source code and help found here:` https://github.com/pure-life-git/k-scope-bot")
    return


@bot.group(name="settings", description="Allows an admin to change the settings of the bot", invoke_without_command=True)
async def settings(ctx):
    server_name = "t"+str(ctx.guild.id)
    cur.execute(f"SELECT prefix FROM prefixes WHERE server_id={ctx.guild.id};")
    cur_prefix = cur.fetchone()[0]

    cur.execute(f"SELECT mods FROM {server_name};")
    modIDS = [id[0] for id in cur.fetchall() if type(id[0]) is int]

    if int(ctx.author.id) not in modIDS:
        await ctx.message.delete()
        await ctx.send(":x: You must have a moderator role to use that command.")
        await asyncio.sleep(5)
        return
    else:
        settings_embed = discord.Embed(title = "K-Scope Bot Settings", description = f"The prefix of the bot is `{cur_prefix}`", color=bot_color)
        settings_embed.add_field(name="Mods", value = f"This setting allows you to add or remove mods that can change bot settings \n `mods` - lets you view the current list of mods \n `addmod` - lets you add a mod \n `removemod` - lets you remove a mod")
        settings_embed.add_field(name="Prefix", value = f"This setting allows you to change the prefix the bot uses for commands \n `prefix` - lets you change the bot's prefix", inline=False)
        settings_embed.set_footer(text = f"ex. `{cur_prefix}settings prefix`, etc...")
        await ctx.send(embed=settings_embed)

@settings.command(name="mods", description = "Lets you view the current mods", aliases=["m"])
async def mods(ctx):
    server_name = "t"+str(ctx.guild.id)

    cur.execute(f"SELECT mods FROM {server_name};")
    modIDS = [int(id[0]) for id in cur.fetchall() if type(id[0]) is int]

    cur.execute(f"SELECT channels FROM {server_name};")
    channelWhitelist = [int(channel[0]) for channel in cur.fetchall() if type(channel[0]) is str]

    if int(ctx.author.id) not in modIDS:
        await ctx.message.delete()
        await ctx.send(":x: You must have a moderator role to use that command.")
        await asyncio.sleep(5)
        return
    elif len(channelWhitelist) > 0 and int(ctx.channel.id) not in channelWhitelist:
        await ctx.message.delete()
        mess = await ctx.send(":x: This channel is not on the bot's whitelist")
        await asyncio.sleep(5)
        await mess.delete()
        return
    elif len(modIDS) == 0:
        await ctx.send("There are no moderators in this server")
        return
    else:
        mod_embed = discord.Embed(title="Mod List", description = "List of added mods that have control over the bot", color=bot_color)
        for modID in modIDS:
            mod = bot.get_user(modID)
            mod_embed.add_field(name=mod.display_name, value = f":crossed_swords: This user is a moderator", inline=False)
        await ctx.send(embed=mod_embed)
        return

@settings.command(name="addmod", description="Lets you add a moderator to the bot", aliases=["am"])
async def add_mod(ctx):
    server_name = "t"+str(ctx.guild.id)

    cur.execute(f"SELECT mods FROM {server_name};")
    modIDS = [id[0] for id in cur.fetchall() if type(id[0]) is int]

    cur.execute(f"SELECT channels FROM {server_name};")
    channelWhitelist = [channel[0] for channel in cur.fetchall() if type(channel[0]) is str]

    if int(ctx.author.id) not in modIDS:
        await ctx.message.delete()
        await ctx.send(":x: You must have a moderator role to use that command.")
        await asyncio.sleep(5)
        return
    elif len(channelWhitelist) > 0 and int(ctx.channel.id) not in channelWhitelist:
        await ctx.message.delete()
        mess = await ctx.send(":x: This channel is not on the bot's whitelist")
        await asyncio.sleep(5)
        await mess.delete()
        return

    for i in range(len(ctx.message.mentions)):
        modUser = ctx.message.mentions[i-1]
        if modUser.id in modIDS:
            await ctx.send(":x: This user is already a moderator.")
            return
        elif modUser.bot:
            await ctx.send(":x: You cannot add other bots as moderators.")
            return
        else:
            SQL = f"INSERT INTO {server_name}(mods) VALUES ({modUser.id});"
            cur.execute(SQL)
            conn.commit()
            await ctx.send(f"{modUser.name} has been added to the bot's mod list.")
            return

@settings.command(name="removemod", description="Lets you remove a moderator from the bot", aliases=["rm"])
async def remove_mod(ctx):
    server_name = "t"+str(ctx.guild.id)

    cur.execute(f"SELECT mods FROM {server_name};")
    modIDS = [id[0] for id in cur.fetchall() if type(id[0]) is int]

    cur.execute(f"SELECT channels FROM {server_name};")
    channelWhitelist = [channel[0] for channel in cur.fetchall() if type(channel[0]) is str]

    if int(ctx.author.id) not in modIDS:
        await ctx.message.delete()
        await ctx.send(":x: You must have a moderator role to use that command.")
        await asyncio.sleep(5)
        return
    elif len(channelWhitelist) > 0 and int(ctx.channel.id) not in channelWhitelist:
        await ctx.message.delete()
        mess = await ctx.send(":x: This channel is not on the bot's whitelist")
        await asyncio.sleep(5)
        await mess.delete()
        return

    for i in range(len(ctx.message.mentions)):
        modUser = ctx.message.mentions[i-1]
        if modUser.id not in modIDS:
            await ctx.send(":x: This user is not a moderator.")
            return
        else:
            SQL = f"UPDATE {server_name} SET mods = NULL WHERE mods = {int(modUser.id)};"
            cur.execute(SQL)
            conn.commit()
            await ctx.send(f"{modUser.name} has been removed from the bot's mod list.")
            return

@settings.command(name="prefix", description="Lets you change the prefix the bot uses in commands")
async def change_prefix(ctx, prefix):
    server_name = "t"+str(ctx.guild.id)

    cur.execute(f"SELECT mods FROM {server_name};")
    modIDS = [id[0] for id in cur.fetchall() if type(id[0]) is int]

    cur.execute(f"SELECT channels FROM {server_name};")
    channelWhitelist = [channel[0] for channel in cur.fetchall() if type(channel[0]) is str]

    if int(ctx.author.id) not in modIDS:
        await ctx.message.delete()
        await ctx.send(":x: You must have a moderator role to use that command.")
        await asyncio.sleep(5)
        return
    elif len(channelWhitelist) > 0 and int(ctx.channel.id) not in channelWhitelist:
        await ctx.message.delete()
        mess = await ctx.send(":x: This channel is not on the bot's whitelist")
        await asyncio.sleep(5)
        await mess.delete()
        return

    server_name = "t"+str(ctx.guild.id)

    cur.execute(f"SELECT mods FROM {server_name};")
    modIDS = [id[0] for id in cur.fetchall() if type(id[0]) is int]

    cur.execute(f"SELECT channels FROM {server_name};")
    channelWhitelist = [channel[0] for channel in cur.fetchall() if type(channel[0]) is str]

    cur.execute(f"SELECT prefix FROM prefixes WHERE server_id={ctx.guild.id};")
    current_prefix = str(cur.fetchone()[0])

    if int(ctx.author.id) not in modIDS:
        await ctx.send(":x: You must have a moderator role to use that command.")
        return
    elif len(channelWhitelist) > 0 and int(ctx.channel.id) not in channelWhitelist:
        mess = await ctx.send(":x: This channel is not on the bot's whitelist")
        await mess.delete()
        return
    elif not isinstance(prefix, str):
        await ctx.send(":x: The prefix must be a string (like a letter or punctuation).")
        return
    elif prefix == current_prefix:
        await ctx.send(":x: That is the current prefix.")
        return
    else:
        SQL = f"UPDATE prefixes SET prefix = '{str(prefix)}' WHERE server_id={ctx.guild.id};"
        cur.execute(SQL)
        conn.commit()
        await ctx.send(f"Prefix successfully changed to `{prefix}`.")
        return



@bot.command(name="reminder", description="Lets you set a reminder", aliases=["r"])
async def reminder(ctx, channel:discord.TextChannel, repeat:bool, now:bool ,duration:str, *args):
    server_name = "t"+str(ctx.guild.id)

    cur.execute(f"SELECT mods FROM {server_name};")
    modIDS = [id[0] for id in cur.fetchall() if type(id[0]) is int]

    if int(ctx.author.id) not in modIDS:
        await ctx.message.delete()
        await ctx.send(":x: You must have a moderator role to use that command.")
        return
    elif not isinstance(channel, discord.TextChannel):
        await ctx.send("First argument must be a mentioned text channel.")
        return
    
    reminder_message = " ".join(args)

    duration, letter, rest = re.split(r"([a-z])", duration, 1, flags=re.I)

    secs = int(int(duration)*TIME_TABLE[letter])

    reminder_table = "r" + str(ctx.guild.id)

    reminder_id = random.randint(10000, 99999)

    execution_time = int(time.time()+secs)

    SQL = f"INSERT INTO {reminder_table}(reminder_id, execution_time, channel_id, repeat, duration, message) VALUES ({reminder_id}, {execution_time}, {channel.id}, {repeat}, {secs}, '{reminder_message}');"
    cur.execute(SQL)
    conn.commit()

    await ctx.send(f":white_check_mark: `[{reminder_id}]` Reminder Set! Will remind {channel} of `{reminder_message}` in `{duration+letter}`.")

    if now:
        await channel.send(content = f"`[{reminder_id}]`: {reminder_message}")

@bot.command(name = "deletereminder", description="Lets you delete a reminder", aliases=["dr"])
async def delete_reminder(ctx, reminder_id:int):
    server_name = "t"+str(ctx.guild.id)
    reminder_table = "r"+str(ctx.guild.id)


    cur.execute(f"SELECT mods FROM {server_name};")
    modIDS = [id[0] for id in cur.fetchall() if type(id[0]) is int]

    cur.execute(f"SELECT reminder_id FROM {reminder_table};")
    reminder_ids = [i[0] for i in cur.fetchall() if type(i[0]) is int]

    if int(ctx.author.id) not in modIDS:
        await ctx.message.delete()
        await ctx.send(":x: You must have a moderator role to use that ocmmand.")
        return
    elif reminder_id not in reminder_ids:
        await ctx.send(":x: That is not a valid reminder id.")
        return
    
    SQL = f"DELETE FROM {reminder_table} WHERE reminder_id = {reminder_id};"
    cur.execute(SQL)
    conn.commit()

    await ctx.send(f"Reminder `#{reminder_id}` successfully deleted.")

@bot.command(name = "reminders", description = "Lets you view the currently active reminders")
async def reminders(ctx):
    reminder_table = "r"+str(ctx.guild.id)

    cur.execute(f"SELECT * FROM {reminder_table};")
    reminders = cur.fetchall()

    reminder_embed = discord.Embed(title = f"{ctx.guild.name}'s Reminders", description = f"Currently active reminders for {ctx.guild.name}", color = bot_color)

    for reminder in reminders:
        reminder_id = reminder[0]
        execution_time = reminder[1]
        channel = ctx.guild.get_channel(reminder[2])
        reminder_message = str(reminder[3])
        duration = int(reminder[4])
        repeat = bool(reminder[5])

        days = math.floor(duration / (3600*24)) if math.floor(duration / (3600*24)) > 0 else 0
        duration -= days * 3600 * 24
        hours = math.floor(duration / 3600) if math.floor(duration / 3600) > 0 else 0
        duration -= hours * 3600
        minutes = math.floor(duration / 60) if math.floor(duration / 60) > 0 else 0
        duration -= minutes * 60
        duration = duration if duration > 0 else 0

        description = f"""Channel: {channel}
        Time Between Reminders: {days}d {hours}hr {minutes}m {duration}s
        Next Reminder: {datetime.datetime.fromtimestamp(execution_time).astimezone(pytz.timezone('US/Eastern')).strftime(f"%Y-%m-%d %H:%M:%S %Z")}
        Repeating: {repeat}
        """

        reminder_embed.add_field(name = f"`[{reminder_id}]`: {reminder_message}", value = description, inline=False)
    
    await ctx.send(embed = reminder_embed)

@bot.command(name="roleselect", description="Lets people assign themselves roles by reacting to a message.", aliases=["rs"])
async def role_select(ctx, channel:discord.TextChannel, title="Role Select", descr="Pick a Role!", *roles):
    server_name = "t"+str(ctx.guild.id)
    message_table = "m"+str(ctx.guild.id)

    cur.execute(f"SELECT mods FROM {server_name};")
    modIDS = [id[0] for id in cur.fetchall() if type(id[0]) is int]

    if int(ctx.author.id) not in modIDS:
        await ctx.message.delete()
        await ctx.send(":x: You must have a moderator role to use that command.")
        return
    elif not isinstance(channel, discord.TextChannel):
        await ctx.send("First argument must be a mentioned text channel.")
        return
    elif len(roles) > 20:
        await ctx.send("Only less than or equal to 20 roles are supported")
        return
    
    server_roles = [role.name for role in ctx.guild.roles]

    role_select_embed = discord.Embed(title = title, description = descr, color=bot_color)

    reaction_to_role = {}

    colors = random.sample(ROLE_COLORS, len(roles))

    for count, role_name in enumerate(roles):
        if role_name not in server_roles:
            await ctx.guild.create_role(name=role_name, reason="Created by `role_select` command.", color = colors[count])
        role_select_embed.add_field(name = f"{ROLE_EMOTES[count]} - {role_name}", value = f"Click the {ROLE_EMOTES[count]} to gain the role {role_name}.", inline=False)
        reaction_to_role[ROLE_EMOTES[count]] = role_name
    
    react_message = await channel.send(embed=role_select_embed)

    for emoji in reaction_to_role:
        await react_message.add_reaction(emoji)

    SQL = f"INSERT INTO {message_table} VALUES ({react_message.id}, '{';'.join(reaction_to_role.values())}');"
    cur.execute(SQL)
    conn.commit()

@tasks.loop(seconds=5, loop = bot.loop)
async def check_reminders():
    for guild in bot.guilds:
        reminder_table = "r"+str(guild.id)
        SQL = f"SELECT * FROM {reminder_table};"
        cur.execute(SQL)
        reminders = cur.fetchall()
        for reminder in reminders:
            if int(time.time()) >= reminder[1]:
                reminder_id = int(reminder[0])
                execution_time = reminder[1]
                channel = guild.get_channel(reminder[2])
                reminder_message = str(reminder[3])
                duration = int(reminder[4])
                repeat = bool(reminder[5])

                await channel.send(content = f"`[{reminder_id}]`: {reminder_message}")

                if repeat:
                    SQL = f"UPDATE {reminder_table} SET execution_time = {int(time.time()+duration)} WHERE reminder_id = {reminder_id};"
                    cur.execute(SQL)
                    conn.commit()
                else:
                    SQL = f"DELETE FROM {reminder_table} WHERE reminder_id = {reminder_id};"
                    cur.execute(SQL)
                    conn.commit()

@bot.event
async def on_raw_reaction_add(payload):
    guild = bot.get_guild(payload.guild_id)
    reactioner = guild.get_member(payload.user_id)
    if reactioner.bot:
        return
    
    channel = guild.get_channel(payload.channel_id)
    emoji = payload.emoji.name
    message_id = payload.message_id

    message_table = "m"+str(guild.id)

    SQL = f"SELECT mess_id FROM {message_table};"
    cur.execute(SQL)

    react_mess_ids = [i[0] for i in cur.fetchall() if type(i[0]) is not None]

    if message_id in react_mess_ids:
        SQL = f"SELECT role_names FROM {message_table} WHERE mess_id = {message_id};"
        cur.execute(SQL)
        role_list = cur.fetchone()[0].split(';')

        reaction_to_role = {}
        for count, role in enumerate(role_list):
            reaction_to_role[ROLE_EMOTES[count]] = role

        await reactioner.add_roles(discord.utils.get(guild.roles, name=reaction_to_role[emoji]))

@bot.event
async def on_raw_reaction_remove(payload):
    guild = bot.get_guild(payload.guild_id)
    reactioner = guild.get_member(payload.user_id)
    if reactioner.bot:
        return
    
    channel = guild.get_channel(payload.channel_id)
    emoji = payload.emoji.name
    message_id = payload.message_id

    message_table = "m"+str(guild.id)

    SQL = f"SELECT mess_id FROM {message_table};"
    cur.execute(SQL)

    react_mess_ids = [i[0] for i in cur.fetchall() if type(i[0]) is not None]

    if message_id in react_mess_ids:
        SQL = f"SELECT role_names FROM {message_table} WHERE mess_id = {message_id};"
        cur.execute(SQL)
        role_list = cur.fetchone()[0].split(';')

        reaction_to_role = {}
        for count, role in enumerate(role_list):
            reaction_to_role[ROLE_EMOTES[count]] = role

        await reactioner.remove_roles(discord.utils.get(guild.roles, name=reaction_to_role[emoji]))

@bot.event
async def on_raw_message_delete(payload):
    guild_id = int(payload.guild_id)
    message_table = "m"+str(guild_id)
    message_id = payload.message_id
    SQL = f"SELECT mess_id FROM {message_table};"
    cur.execute(SQL)

    react_mess_ids = [i[0] for i in cur.fetchall() if type(i[0]) is not None]

    if message_id in react_mess_ids:
        SQL = f"DELETE FROM {message_table} WHERE mess_id = {message_id};"
        cur.execute(SQL)
        conn.commit()

@bot.event
async def on_guild_join(guild):
    main_channel = guild.text_channels[0]
    await main_channel.send(f":wave: Thanks for welcoming me to `{guild.name}`! My default prefix is `?`. You can change this with `?settings`.")

    server_name = "t"+str(guild.id)
    reminder_name = "r"+str(guild.id)
    message_name = "m"+str(guild.id)

    SQL = f"CREATE TABLE {server_name} (channels bigint, mods bigint, prefix varchar(255));"
    cur.execute(SQL)
    conn.commit()

    SQL = f"CREATE TABLE {reminder_name} (reminder_id bigint, execution_time bigint, channel_id bigint, message text, duration bigint, repeat boolean);"
    cur.execute(SQL)
    conn.commit()

    SQL = f"CREATE TABLE {message_name} (mess_id bigint, role_names text);"
    cur.execute(SQL)
    conn.commit()

    SQL = f"INSERT INTO prefixes(server_id,prefix) VALUES ({guild.id}, '{DEFAULT_PREFIX}');"
    cur.execute(SQL)
    conn.commit()

    mod_ids = []

    SQL = f"INSERT INTO {server_name}(mods) VALUES (288710564367171595);"
    cur.execute(SQL)
    conn.commit()

    mod_ids.append(288710564367171595)

    for member in guild.members:
        if member.top_role.permissions.administrator and int(member.id) not in mod_ids and not member.bot:
            mod_ids.append(int(member.id))
            SQL = f"INSERT INTO {server_name}(mods) VALUES ({int(member.id)});"
            cur.execute(SQL)
            conn.commit()

@bot.event
async def on_guild_remove(guild):
    server_name = "t"+str(guild.id)
    reminder_table = "r"+str(guild.id)
    message_table = "m"+str(guild.id)
    
    SQL = f"DELETE FROM prefixes WHERE server_id={guild.id};"
    cur.execute(SQL)
    conn.commit()
    
    SQL = f"DROP TABLE {server_name};"
    cur.execute(SQL)
    conn.commit()

    SQL = f"DROP TABLE {reminder_table};"
    cur.execute(SQL)
    conn.commit()

    SQL = f"DROP TABLE {message_table};"
    cur.execute(SQL)
    conn.commit()


#--------------------------------------------------------------------------------------------------------------------------------------#
#runs the bot using the discord bot token provided within Heroku
bot.run(os.environ['token'])