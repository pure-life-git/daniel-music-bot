import ctypes
import asyncio
import ctypes.util
import datetime
import math
import os
import random

import discord
from discord import colour
from discord import permissions
from discord.errors import ClientException
from discord.ext import commands
from discord.ext.commands.errors import CommandOnCooldown
from discord.player import FFmpegPCMAudio

import spotipy
import spotipy.oauth2 as oauth2
import psycopg2
import requests
import youtube_dl
from youtube_search import YoutubeSearch

DEFAULT_PREFIX = "!"

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

find = ctypes.util.find_library('opus')
discord.opus.load_opus(find)

auth_manager = oauth2.SpotifyClientCredentials(client_id=os.environ['spot_id'], client_secret=os.environ['spot_secret'])
sp = spotipy.Spotify(auth_manager=auth_manager)

music_queue = []

ydl_opts = {
    'quiet': True,
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'outtmpl': './song.mp3',
    'cookiefile': '.ydl_cookies.txt'
}

now_playing = ""

song_repeating = False
queue_repeating = False

@bot.group(name='help', invoke_without_command = True)
async def help(ctx):
    server_name = "t"+str(ctx.guild.id)

    cur.execute(f"SELECT channels FROM {server_name};")
    channelWhitelist = [channel[0] for channel in cur.fetchall() if type(channel[0]) is int]

    if len(channelWhitelist) > 0 and int(ctx.channel.id) not in channelWhitelist:
        await ctx.message.delete()
        mess = await ctx.send(":x: This channel is not on the bot's whitelist")
        await asyncio.sleep(5)
        await mess.delete()
        return
    cur.execute(f"SELECT prefix FROM prefixes WHERE server_id={ctx.guild.id};")
    cur_prefix = cur.fetchone()[0]
    helpEmbed = discord.Embed(title = "Dorg Bot Help", description = f"The prefix of the bot is `{cur_prefix}`", color = bot_color)
    helpEmbed.add_field(name = ":musical_note: **Music - 8**", value = "`play`, `skip`, `clear`, `queue`, `leave`, `shuffle`, `repeat`, `ignore`")
    helpEmbed.add_field(name = ":gear: **Settings**", value = "`settings`", inline = False)
    helpEmbed.set_footer(text = "For more information try .help (command) or .help (category), ex: .help play or .help settings")
    await ctx.send(embed=helpEmbed)

# MUSIC HELP COMMANDS

@help.command(name = "music")
async def music_help(ctx):
    cur.execute(f"SELECT prefix FROM prefixes WHERE server_id={ctx.guild.id};")
    cur_prefix = cur.fetchone()[0]
    server_name = "t"+str(ctx.guild.id)

    cur.execute(f"SELECT channels FROM {server_name};")
    channelWhitelist = [channel[0] for channel in cur.fetchall() if type(channel[0]) is int]

    if len(channelWhitelist) > 0 and int(ctx.channel.id) not in channelWhitelist:
        await ctx.message.delete()
        mess = await ctx.send(":x: This channel is not on the bot's whitelist")
        await asyncio.sleep(5)
        await mess.delete()
        return
    helpEmbed = discord.Embed(title = "Dorg Bot Help", description = "Help with the Music category", color = bot_color)
    helpEmbed.add_field(name = ":musical_note: Music Commands :musical_note:", value = "**play**\nPlays a song\n**skip**\nSkips the song\n**clear**\nClears the queue\n**queue**\nShows the queue\n**leave**\nForces the bot to leave\n**shuffle**\nShuffles the queue\n**repeat**\nRepeats the song\n**ignore**\nIgnores a user's commands", inline=False)
    helpEmbed.set_footer(text=f"For more help, type {cur_prefix}help `command` (ex. {cur_prefix}help play)")
    await ctx.send(embeds=helpEmbed)
@help.command(name = "play")
async def play_help(ctx):
    server_name = "t"+str(ctx.guild.id)

    cur.execute(f"SELECT channels FROM {server_name};")
    channelWhitelist = [channel[0] for channel in cur.fetchall() if type(channel[0]) is int]

    if len(channelWhitelist) > 0 and int(ctx.channel.id) not in channelWhitelist:
        await ctx.message.delete()
        mess = await ctx.send(":x: This channel is not on the bot's whitelist")
        await asyncio.sleep(5)
        await mess.delete()
        return
    helpEmbed = discord.Embed(title = "Dorg Bot Help", description = "Help with the play command", color = bot_color)
    helpEmbed.add_field(name = "play `<youtube url, search term, or spotify playlist link>`", value = "play lets you queue a song from youtube or a playlist from spotify")
    await ctx.send(embed=helpEmbed)
@help.command(name = "skip")
async def skip_help(ctx):
    server_name = "t"+str(ctx.guild.id)

    cur.execute(f"SELECT channels FROM {server_name};")
    channelWhitelist = [channel[0] for channel in cur.fetchall() if type(channel[0]) is int]

    if len(channelWhitelist) > 0 and int(ctx.channel.id) not in channelWhitelist:
        await ctx.message.delete()
        mess = await ctx.send(":x: This channel is not on the bot's whitelist")
        await asyncio.sleep(5)
        await mess.delete()
        return
    helpEmbed = discord.Embed(title = "Dorg Bot Help", description = "Help with the skip command", color = bot_color)
    helpEmbed.add_field(name = "skip", value = "skip lets you skip the currently playing song")
    await ctx.send(embed=helpEmbed)
@help.command(name = "clear")
async def clear_help(ctx):
    server_name = "t"+str(ctx.guild.id)

    cur.execute(f"SELECT channels FROM {server_name};")
    channelWhitelist = [channel[0] for channel in cur.fetchall() if type(channel[0]) is int]

    if len(channelWhitelist) > 0 and int(ctx.channel.id) not in channelWhitelist:
        await ctx.message.delete()
        mess = await ctx.send(":x: This channel is not on the bot's whitelist")
        await asyncio.sleep(5)
        await mess.delete()
        return
    helpEmbed = discord.Embed(title = "Dorg Bot Help", description = "Help with the clear command", color = bot_color)
    helpEmbed.add_field(name = "clear", value = "clear lets you clear the song queue")
    await ctx.send(embed=helpEmbed)
@help.command(name = "leave")
async def leave_help(ctx):
    server_name = "t"+str(ctx.guild.id)

    cur.execute(f"SELECT channels FROM {server_name};")
    channelWhitelist = [channel[0] for channel in cur.fetchall() if type(channel[0]) is int]

    if len(channelWhitelist) > 0 and int(ctx.channel.id) not in channelWhitelist:
        await ctx.message.delete()
        mess = await ctx.send(":x: This channel is not on the bot's whitelist")
        await asyncio.sleep(5)
        await mess.delete()
        return
    helpEmbed = discord.Embed(title = "Dorg Bot Help", description = "Help with the leave command", color = bot_color)
    helpEmbed.add_field(name = "leave", value = "leave forces the bot to leave the voice channel")
    await ctx.send(embed=helpEmbed)
@help.command(name = "shuffle")
async def shuffle_help(ctx):
    server_name = "t"+str(ctx.guild.id)

    cur.execute(f"SELECT channels FROM {server_name};")
    channelWhitelist = [channel[0] for channel in cur.fetchall() if type(channel[0]) is int]

    if len(channelWhitelist) > 0 and int(ctx.channel.id) not in channelWhitelist:
        await ctx.message.delete()
        mess = await ctx.send(":x: This channel is not on the bot's whitelist")
        await asyncio.sleep(5)
        await mess.delete()
        return
    helpEmbed = discord.Embed(title = "Dorg Bot Help", description = "Help with the shuffle command", color = bot_color)
    helpEmbed.add_field(name = "shuffle", value = "shuffle lets you shuffle the music queue")
    await ctx.send(embed=helpEmbed)
@help.command(name = "repeat")
async def repeat_help(ctx):
    server_name = "t"+str(ctx.guild.id)

    cur.execute(f"SELECT channels FROM {server_name};")
    channelWhitelist = [channel[0] for channel in cur.fetchall() if type(channel[0]) is int]

    if len(channelWhitelist) > 0 and int(ctx.channel.id) not in channelWhitelist:
        await ctx.message.delete()
        mess = await ctx.send(":x: This channel is not on the bot's whitelist")
        await asyncio.sleep(5)
        await mess.delete()
        return
    helpEmbed = discord.Embed(title = "Dorg Bot Help", description = "Help with the repeat command", color = bot_color)
    helpEmbed.add_field(name = "repeat", value = "repeat lets you repeat a song indefinitely")
    await ctx.send(embed=helpEmbed)
@help.command(name = "ignore")
async def ignore_help(ctx):
    server_name = "t"+str(ctx.guild.id)

    cur.execute(f"SELECT channels FROM {server_name};")
    channelWhitelist = [channel[0] for channel in cur.fetchall() if type(channel[0]) is int]

    if len(channelWhitelist) > 0 and int(ctx.channel.id) not in channelWhitelist:
        await ctx.message.delete()
        mess = await ctx.send(":x: This channel is not on the bot's whitelist")
        await asyncio.sleep(5)
        await mess.delete()
        return
    helpEmbed = discord.Embed(title = "Dorg Bot Help", description = "Help with the ignore command", color = bot_color)
    helpEmbed.add_field(name = "ignore `<mention member>`", value = "ignore lets a moderator take away someone's music bot privileges")
    await ctx.send(embed=helpEmbed)
@help.command(name = "queue")
async def queue_help(ctx):
    server_name = "t"+str(ctx.guild.id)

    cur.execute(f"SELECT channels FROM {server_name};")
    channelWhitelist = [channel[0] for channel in cur.fetchall() if type(channel[0]) is int]

    if len(channelWhitelist) > 0 and int(ctx.channel.id) not in channelWhitelist:
        await ctx.message.delete()
        mess = await ctx.send(":x: This channel is not on the bot's whitelist")
        await asyncio.sleep(5)
        await mess.delete()
        return
    helpEmbed = discord.Embed(title = "Dorg Bot Help", description = "Help with the queue command", color = bot_color)
    helpEmbed.add_field(name = "queue", value = "queue lets you view the song queue")
    await ctx.send(embed=helpEmbed)
@help.command(name = "settings")
async def settings_help(ctx):
    server_name = "t"+str(ctx.guild.id)

    cur.execute(f"SELECT channels FROM {server_name};")
    channelWhitelist = [channel[0] for channel in cur.fetchall() if type(channel[0]) is int]

    if len(channelWhitelist) > 0 and int(ctx.channel.id) not in channelWhitelist:
        await ctx.message.delete()
        mess = await ctx.send(":x: This channel is not on the bot's whitelist")
        await asyncio.sleep(5)
        await mess.delete()
        return
    helpEmbed = discord.Embed(title = "Dorg Bot Help", description = "Help with the settings command", color = bot_color)
    helpEmbed.add_field(name = "settings", value = "settings shows the channel and mod settings for the bot")
    await ctx.send(embed=helpEmbed)




@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    await bot.change_presence(status = discord.Status.online, activity=discord.Game("!help"))


def col_to_sec(time:str):
    if len(time.split(":")) == 2:
        h=0
        m,s = time.split(':')
    elif len(time.split(":")) == 1:
        h,m = 0,0
        s=time
    else:
        h, m, s = time.split(':')

    return(int(h) * 3600 + int(m) * 60 + int(s))

def get_track_names(user, playlist_id):
    track_names = []
    playlist = sp.user_playlist(user, playlist_id)
    for item in playlist['tracks']['items']:
        track = item['track']
        track_names.append(sp.track(track['id'])['name'])
    return track_names

async def play_spotify(ctx, song):
    ytresults = YoutubeSearch(song, max_results=1).to_dict()

    if len(ytresults) == 0:
        await ctx.send("No results.")
        return
    else:
        song = "".join(("https://www.youtube.com", ytresults[0]["url_suffix"]))
        title = ytresults[0]["title"]
        channel = ytresults[0]["channel"]
        runtime = ytresults[0]["duration"]

    runtime_sec = col_to_sec(runtime)

    if runtime_sec > 7200:
        await ctx.send("Cannot queue a song longer than 2 hours.")
        return

    voice = ctx.guild.voice_client

    if voice:
        if voice.is_playing():
            music_queue.append((song, title, channel, runtime, ctx.author, False))
            return
        else:
            await play_music(ctx, (song,title,channel, runtime, ctx.author, False))
    else:
        await ctx.author.voice.channel.connect()
        await play_music(ctx,(song,title,channel, runtime, ctx.author, False))

async def play_soundcloud(ctx, song):
    if col_to_sec(song[3]) > 7200:
        await ctx.send("Cannot queue a song longer than 2 hours.")
        return
    
    voice = ctx.guild.voice_client

    if voice:
        if voice.is_playing():
            music_queue.append(song)
            return
        else:
            await play_music(ctx, song)
    else:
        await ctx.author.voice.channel.connect()
        await play_music(ctx, song)

async def playlist(ctx, song):
    voice = ctx.guild.voice_client

    if voice:
        if voice.is_playing():
            music_queue.append(song)
            return
        else:
            await play_music(ctx, song)
            return
    else:
        await ctx.author.voice.channel.connect()
        await play_music(ctx, song)
        return

async def check_play_next(ctx):
    voice = ctx.guild.voice_client
    if len(music_queue) > 0:
        if song_repeating:
            if voice.is_playing():
                voice.stop()
                await play_music(ctx, now_playing)

            else:
                await play_music(ctx, now_playing)
        elif queue_repeating:
            if voice.is_playing():
                voice.stop()
                music_queue.append(now_playing)
                await play_music(ctx, music_queue.pop(0))
            else:
                music_queue.append(now_playing)
                await play_music(ctx, music_queue.pop(0))
        else:
            if voice.is_playing():
                voice.stop()
                await play_music(ctx, music_queue.pop(0))
            else:
                await play_music(ctx, music_queue.pop(0))

    else:
        if song_repeating:
            if voice.is_playing():
                voice.stop()
                await play_music(ctx,now_playing)

            else:
                await play_music(ctx, now_playing)
        else:
            voice.stop()
            await asyncio.sleep(120)
            print("idling...")
            if not voice.is_playing():
                asyncio.run_coroutine_threadsafe(voice.disconnect(), bot.loop)                                 

async def play_music(ctx,song):
    print(f"playing {song[1]}")
    if isinstance(ctx, discord.VoiceChannel):
        song_there = os.path.isfile("song.mp3")

        if song_there:
            os.remove("song.mp3")

        voice = ctx.guild.voice_client

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([song])

        if voice:
            if voice.is_connected():
                if voice.is_playing():
                    voice.stop()
                    voice.play(FFmpegPCMAudio(source="song.mp3"))
                else:
                    voice.play(FFmpegPCMAudio(source="song.mp3"))
            else:
                await ctx.connect()
                voice.play(FFmpegPCMAudio(source="song.mp3"))
        else:
            voice = await ctx.connect()
            voice.play(FFmpegPCMAudio(source="song.mp3"))
        await asyncio.sleep(120)
        if not voice.is_playing():
            await voice.disconnect()    
        return
        
    global now_playing
    if song != now_playing:
        now_playing = (song[0], song[1], song[2], song[3], song[4], int(datetime.datetime.now().timestamp()))
    title = song[1]
    channel = song[2]
    runtime = song[3]
    author = song[4]
    live = song[5]
    song = song[0]
    if not live:
        song_there = os.path.isfile("song.mp3")

        if song_there:
            os.remove("song.mp3")

        voice = ctx.guild.voice_client

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([song])

        voice.play(discord.FFmpegPCMAudio(source="song.mp3"),after=lambda error: bot.loop.create_task(check_play_next(ctx)))
        print("played audio...")
        np_embed = discord.Embed(title="Now Playing", description=f"`{title}` requested by {author.mention}", value=f"Duration: {runtime}", color=bot_color)
        np_embed.add_field(name=f"Duration: {runtime}", value=f"Channel: {channel}", inline=False)
        await ctx.send(embed=np_embed)

    else:
        LIVE_YDL_OPTIONS = {'format': 'bestaudio/best', 'noplaylist':'True'}
 
        FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

        voice = ctx.guild.voice_client
        with youtube_dl.YoutubeDL(LIVE_YDL_OPTIONS) as ydl:
            info = ydl.extract_info(song, download=False)
            I_URL = info['formats'][0]['url']
            source = await discord.FFmpegOpusAudio.from_probe(I_URL, **FFMPEG_OPTIONS)
            voice.play(source, after = lambda error: bot.loop.create_task(check_play_next(ctx)))
            print("played livestream...")
            np_embed = discord.Embed(title="Now Playing", description=f"`{title}` request by {author.mention}", color = bot_color)
            np_embed.add_field(name="Duration: :red_circle: LIVE", value=f"Channel: {channel}", inline=False)
            await ctx.send(embed=np_embed)

@bot.command(name="play", description="Plays a song in a voice channel", aliases=["p"])
async def play(ctx, *args):
    cur.execute(f"SELECT ignore FROM musicbot WHERE id = {int(ctx.author.id)};")
    ignored = cur.fetchone()[0]
    server_name = "t"+str(ctx.guild.id)

    cur.execute(f"SELECT channels FROM {server_name};")
    channelWhitelist = [channel[0] for channel in cur.fetchall() if type(channel[0]) is int]

    if len(channelWhitelist) > 0 and int(ctx.channel.id) not in channelWhitelist:
        await ctx.message.delete()
        mess = await ctx.send(":x: This channel is not on the bot's whitelist")
        await asyncio.sleep(5)
        await mess.delete()
        return
    elif ignored:
        return

    song = " ".join(args)
    
    uservoice = ctx.author.voice

    if uservoice is None or uservoice.channel.name == "Out to Lunch - AFK":
        await ctx.send("You must be in an active voice channel to play music.")
        return
    
    if song.startswith("https://open.spotify.com/playlist"):
        track_names = [spottrack for spottrack in sp.user_playlist_tracks('spotify', song.split('playlist/')[1].split('?')[0])['items']]

        for track in track_names:
            song_name = track['track']['name'] + track['track']['artists'][0]['name']
        
            ytresults = YoutubeSearch(song_name, max_results=1).to_dict()

            if len(ytresults) == 0:
                await ctx.send(f"No results for {track['track']['name']} by {track['track']['artists'][0]['name']}.")
                continue
            else:
                song = "".join(("https://www.youtube.com", ytresults[0]["url_suffix"]))
                title = ytresults[0]["title"]
                channel = ytresults[0]["channel"]
                runtime = ytresults[0]["duration"]
                author = ctx.author
                live = False

            runtime_sec = col_to_sec(runtime)

            if runtime_sec > 7200:
                await ctx.send("Cannot queue a song longer than 2 hours.")
                continue

            await playlist(ctx, (song, title, channel, runtime, author, live))
        
        await ctx.send(f"Queued `{len(track_names)}` songs.")
    
    elif song.startswith("https://open.spotify.com/album/"):
        tracks = [spottrack for spottrack in sp.album_tracks(song.split('album/')[1].split('?')[0])['items']]

        for item in tracks:
            song_name = item['name'] + item['artists'][0]['name']
        
            ytresults = YoutubeSearch(song_name, max_results=1).to_dict()

            if len(ytresults) == 0:
                await ctx.send(f"No results for {item['name']} by {item['artists'][0]['name']}.")
                continue
            else:
                song = "".join(("https://www.youtube.com", ytresults[0]["url_suffix"]))
                title = ytresults[0]["title"]
                channel = ytresults[0]["channel"]
                runtime = ytresults[0]["duration"]
                author = ctx.author
                live = False

            runtime_sec = col_to_sec(runtime)

            if runtime_sec > 7200:
                await ctx.send("Cannot queue a song longer than 2 hours.")
                continue

            await playlist(ctx, (song, title, channel, runtime, author, live))
        
        await ctx.send(f"Queued `{len(tracks)}` songs.")

    elif song.startswith("https://open.spotify.com/track/"):
        track_name = sp.track(song.split("track/")[1].split("?")[0])['name']+" "+sp.track(song.split("track/")[1].split("?")[0])['artists'][0]['name']
        song = track_name
        
    elif song.startswith("https://soundcloud.com"):
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url = song)
            if bool(info.get('_type')):
                for entry in info['entries']:
                    title = entry['title']
                    channel = entry['uploader']
                    runtime = str(datetime.timedelta(seconds=int(entry['duration'])))
                    author = ctx.author
                    live = False if int(entry['duration']) == 0 else True
                    if int(entry['duration']) > 7200:
                        await ctx.send("Cannot queue a song longer than 2 hours.")
                        return
                    await playlist(ctx, (song, title, channel, runtime, author, live))
                await ctx.send(f"Queued `{len(info['entries'])}` songs.")
            else:
                title = info['title']
                channel = info['uploader']
                runtime = str(datetime.timedelta(seconds=int(info['duration'])))
                author = ctx.author
                live = False
                if int(info['duration']) > 7200:
                    await ctx.send("Cannot queue a song longer than 2 hours.")
                    return
    elif song.startswith("https://www.youtube.com"):
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url = song)
            if bool(info.get('_type')):
                for entry in info['entries']:
                    song = entry['webpage_url']
                    title = entry['title']
                    channel = entry['uploader']
                    runtime = str(datetime.timedelta(seconds=int(entry['duration'])))
                    author = ctx.author
                    live = True if int(entry['duration']) == 0 else False

                    if int(entry['duration']) > 7200:
                        await ctx.send("Cannot queue a song longer than 2 hours.")
                        continue
                    
                    await playlist(ctx, (song, title, channel, runtime, author, live))
            else:
                print("playing youtube link...")
                title = info['title']
                channel = info['uploader']
                runtime = str(datetime.timedelta(seconds=int(info['duration'])))
                author = ctx.author
                live = True if int(info['duration']) == 0 else False

                if int(info['duration']) > 7200:
                    await ctx.send("Cannot queue a song longer than 2 hours.")
                    return
    else:
        ytresults = YoutubeSearch(song, max_results=1).to_dict()

        if len(ytresults) == 0:
            await ctx.send("No results.")
            return
        elif ytresults[0]['duration'] == 0:
            song = "".join(("https://www.youtube.com", ytresults[0]['url_suffix']))
            title = ytresults[0]['title']
            channel = ytresults[0]["channel"]
            runtime = 0
            live = True
        else:
            song = "".join(("https://www.youtube.com", ytresults[0]["url_suffix"]))
            title = ytresults[0]["title"]
            channel = ytresults[0]["channel"]
            runtime = ytresults[0]["duration"]
            live = False

        runtime_sec = col_to_sec(str(runtime))

        if runtime_sec > 7200:
            await ctx.send("Cannot queue a song longer than 2 hours.")
            return

    voice = ctx.guild.voice_client

    if voice:
        if voice.is_playing():
            music_queue.append((song, title, channel, runtime, ctx.author, live))
            total_runtime = 0
            for song in music_queue[1:]:
                total_runtime += col_to_sec(song[3])
            
            total_runtime += col_to_sec(str(now_playing[3]))-(int(datetime.datetime.now().timestamp())-now_playing[5])

            queueadd_embed = discord.Embed(title="**Added to Queue**", description=f"Added `{title}` to the queue.\nEstimated Time until Playing: `{str(datetime.timedelta(seconds=total_runtime))}`", color=bot_color)
            await ctx.send(embed=queueadd_embed)
            return
        else:
            await play_music(ctx, (song,title,channel, runtime, ctx.author, live))
    else:
        await uservoice.channel.connect()
        await play_music(ctx,(song,title,channel, runtime, ctx.author, live))

@bot.command(name="skip", description="Skips the currently playing song", aliases=["s"])
async def skip(ctx):
    print("skipping...")
    cur.execute(f"SELECT ignore FROM musicbot WHERE id = {int(ctx.author.id)};")
    ignored = cur.fetchone()[0]
    server_name = "t"+str(ctx.guild.id)

    cur.execute(f"SELECT channels FROM {server_name};")
    channelWhitelist = [channel[0] for channel in cur.fetchall() if type(channel[0]) is int]

    if len(channelWhitelist) > 0 and int(ctx.channel.id) not in channelWhitelist:
        await ctx.message.delete()
        mess = await ctx.send(":x: This channel is not on the bot's whitelist")
        await asyncio.sleep(5)
        await mess.delete()
        return
    elif ignored:
        return
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice.is_connected():
        if voice.is_playing():
            skip_embed = discord.Embed(title=f"**:fast_forward: Skipped**", description=f"Skipped {now_playing[1]}", color=bot_color)
            await ctx.send(embed=skip_embed)
            voice.stop()
            
        else:
            await ctx.send("The bot is not currently playing anything")
            return
    else:
        await ctx.send("The bot is not connected to an active voice channel.")

@bot.command(name="leave", description="Makes the bot leave an active voice channel", aliases=["l"])
async def leave(ctx):
    cur.execute(f"SELECT ignore FROM musicbot WHERE id = {int(ctx.author.id)};")
    ignored = cur.fetchone()[0]
    server_name = "t"+str(ctx.guild.id)

    cur.execute(f"SELECT channels FROM {server_name};")
    channelWhitelist = [channel[0] for channel in cur.fetchall() if type(channel[0]) is int]

    if len(channelWhitelist) > 0 and int(ctx.channel.id) not in channelWhitelist:
        await ctx.message.delete()
        mess = await ctx.send(":x: This channel is not on the bot's whitelist")
        await asyncio.sleep(5)
        await mess.delete()
        return
    elif ignored:
        return
    # elif "Coin Operator" not in [i.name for i in ctx.author.roles]:
    #     await ctx.send("You need a role called `Coin Operator` to do that.")
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice.is_connected():
        voice.stop()
        await voice.disconnect()
        music_queue.clear()
    else:
        await ctx.send("The bot is not connected to an active voice channel.")
        return

@bot.command(name="clear", description="Clears the queue", aliases=["c"])
async def clear(ctx):
    cur.execute(f"SELECT ignore FROM musicbot WHERE id = {int(ctx.author.id)};")
    ignored = cur.fetchone()[0]
    server_name = "t"+str(ctx.guild.id)

    cur.execute(f"SELECT channels FROM {server_name};")
    channelWhitelist = [channel[0] for channel in cur.fetchall() if type(channel[0]) is int]

    if len(channelWhitelist) > 0 and int(ctx.channel.id) not in channelWhitelist:
        await ctx.message.delete()
        mess = await ctx.send(":x: This channel is not on the bot's whitelist")
        await asyncio.sleep(5)
        await mess.delete()
        return
    elif ignored:
        return
    # elif "Coin Operator" not in [i.name for i in ctx.author.roles]:
    #     await ctx.send("You need a role called `Coin Operator` to do that.")
    num_songs = len(music_queue)
    music_queue.clear()
    await ctx.send(f"The queue has been cleared of {num_songs} songs.")

@bot.command(name="queue", description="Displays the queue of songs", aliases=["q"])
async def queue(ctx):
    server_name = "t"+str(ctx.guild.id)

    cur.execute(f"SELECT channels FROM {server_name};")
    channelWhitelist = [channel[0] for channel in cur.fetchall() if type(channel[0]) is int]

    if len(channelWhitelist) > 0 and int(ctx.channel.id) not in channelWhitelist:
        await ctx.message.delete()
        mess = await ctx.send(":x: This channel is not on the bot's whitelist")
        await asyncio.sleep(5)
        await mess.delete()
        return
    
    total_runtime = 0
    queue_embed = discord.Embed(title="Music Queue", description="", color=bot_color)
    queue_embed.add_field(name=":musical_note: Now Playing :musical_note:", value=f"Title: {now_playing[1]}  |  Channel: {now_playing[2]}\nRuntime: {now_playing[3]}  |  Queued by: {now_playing[4].mention}" if int(col_to_sec(str(now_playing[3])))>0 else f"Title: {now_playing[1]}  |  Channel: {now_playing[2]}\nRuntime: :red_circle: LIVE  |  Queued by: {now_playing[4].mention}")
    for num,song in enumerate(music_queue):
        if num < 6:
            queue_embed.add_field(name=f"{num+1} - {song[1]} | {song[2]}", value=f"Runtime: {song[3]}  |  Queued by: {song[4].mention}" if int(col_to_sec(str(song[3]))) > 0 else f"Runtime: :red_circle: LIVE  |  Queued by: {song[4].mention}", inline=False)
        total_runtime += col_to_sec(str(song[3]))
    
    total_runtime += col_to_sec(str(now_playing[3]))-(int(datetime.datetime.now().timestamp())-now_playing[5])
    if len(music_queue) > 7:
        queue_embed.add_field(name="-=-=-=-=-=-=-=-=-=-=-==-=-=-=-", value=f"+ {len(music_queue)-5} more")
    
    hms_runtime = str(datetime.timedelta(seconds = total_runtime))

    queue_embed.add_field(name="Length", value=f"{len(music_queue)}" if not queue_repeating else "∞", inline = False)
    queue_embed.add_field(name="Queue Repeating", value=queue_repeating, inline=True)
    queue_embed.add_field(name="Song Repeating", value=song_repeating, inline=True)
    queue_embed.add_field(name = "Total Playtime", value = hms_runtime, inline=True)

    await ctx.send(embed=queue_embed)

@bot.group(name="repeat", description="Deals with song and queue repeating", invoke_without_command=True)
async def repeat(ctx):
    if str(ctx.channel) not in ["jukebox", "admins-only"]:
        await ctx.message.delete()
        return
    # elif "Coin Operator" not in [i.name for i in ctx.author.roles]:
    #     await ctx.send("You need a role called `Coin Operator` to do that.")
    global song_repeating
    global queue_repeating
    repeat_embed = discord.Embed(title="Repeat", description=f"**Song Repeating:** {song_repeating}\n**Queue Repeating:** {queue_repeating}", color=bot_color)
    await ctx.send(embed=repeat_embed)

@repeat.command(name="song", description="Repeats the current song", aliases=["s"])
async def song_repeat(ctx):
    cur.execute(f"SELECT ignore FROM musicbot WHERE id = {int(ctx.author.id)};")
    ignored = cur.fetchone()[0]
    server_name = "t"+str(ctx.guild.id)

    cur.execute(f"SELECT channels FROM {server_name};")
    channelWhitelist = [channel[0] for channel in cur.fetchall() if type(channel[0]) is int]

    if len(channelWhitelist) > 0 and int(ctx.channel.id) not in channelWhitelist:
        await ctx.message.delete()
        mess = await ctx.send(":x: This channel is not on the bot's whitelist")
        await asyncio.sleep(5)
        await mess.delete()
        return
    elif ignored:
        return
    
    global song_repeating
    song_repeating = not song_repeating
    await ctx.send(f"**Song Repeating:** {song_repeating}")

@repeat.command(name="none", description="Doesn't repeat", aliases=["n"])
async def none_repeat(ctx):
    cur.execute(f"SELECT ignore FROM musicbot WHERE id = {int(ctx.author.id)};")
    ignored = cur.fetchone()[0]
    server_name = "t"+str(ctx.guild.id)

    cur.execute(f"SELECT channels FROM {server_name};")
    channelWhitelist = [channel[0] for channel in cur.fetchall() if type(channel[0]) is int]

    if len(channelWhitelist) > 0 and int(ctx.channel.id) not in channelWhitelist:
        await ctx.message.delete()
        mess = await ctx.send(":x: This channel is not on the bot's whitelist")
        await asyncio.sleep(5)
        await mess.delete()
        return
    elif ignored:
        return
    
    global song_repeating
    global queue_repeating
    song_repeating, queue_repeating = False, False
    await ctx.send(f"**Repeating:**: None" )

@repeat.command(name="queue", description="Repeats the current queue", aliases=["q"])
async def queue_repeat(ctx):
    cur.execute(f"SELECT ignore FROM musicbot WHERE id = {int(ctx.author.id)};")
    ignored = cur.fetchone()[0]
    server_name = "t"+str(ctx.guild.id)

    cur.execute(f"SELECT channels FROM {server_name};")
    channelWhitelist = [channel[0] for channel in cur.fetchall() if type(channel[0]) is int]

    if len(channelWhitelist) > 0 and int(ctx.channel.id) not in channelWhitelist:
        await ctx.message.delete()
        mess = await ctx.send(":x: This channel is not on the bot's whitelist")
        await asyncio.sleep(5)
        await mess.delete()
        return
    elif ignored:
        return

    global queue_repeating
    queue_repeating = not queue_repeating
    await ctx.send(f"**Queue Repeating:** {queue_repeating}") 

@bot.command(name="shuffle", description="Shuffles the music queue")
async def shuffle(ctx):
    cur.execute(f"SELECT ignore FROM musicbot WHERE id = {int(ctx.author.id)};")
    ignored = cur.fetchone()[0]
    server_name = "t"+str(ctx.guild.id)

    cur.execute(f"SELECT channels FROM {server_name};")
    channelWhitelist = [channel[0] for channel in cur.fetchall() if type(channel[0]) is int]

    if len(channelWhitelist) > 0 and int(ctx.channel.id) not in channelWhitelist:
        await ctx.message.delete()
        mess = await ctx.send(":x: This channel is not on the bot's whitelist")
        await asyncio.sleep(5)
        await mess.delete()
        return
    elif ignored:
        return
    random.shuffle(music_queue)
    await ctx.send("Queue successfully shuffled.")

@bot.command(name="ignore", description="Lets a Moderator take away someone's music bot privileges", aliases=["i"])
async def ignore(ctx, user: discord.Member = False):
    cur.execute(f"SELECT ignore FROM musicbot WHERE id = {int(ctx.author.id)};")
    ignored = cur.fetchone()[0]
    server_name = "t"+str(ctx.guild.id)

    cur.execute(f"SELECT channels FROM {server_name};")
    channelWhitelist = [channel[0] for channel in cur.fetchall() if type(channel[0]) is int]

    cur.execute(f"SELECT mods FROM {server_name};")
    modIDS = [id[0] for id in cur.fetchall() if type(id[0]) is int]

    

    if len(channelWhitelist) > 0 and int(ctx.channel.id) not in channelWhitelist:
        await ctx.message.delete()
        mess = await ctx.send(":x: This channel is not on the bot's whitelist")
        await asyncio.sleep(5)
        await mess.delete()
        return
    elif int(ctx.author.id) not in modIDS:
        await ctx.message.delete()
        await ctx.send(":x: You must have a moderator role to use that command.")
        await asyncio.sleep(5)
        return
    elif ignored:
        return

    if not user:
        cur.execute("SELECT * FROM musicbot WHERE ignore=true;")
        entries = cur.fetchall()
        ignore_embed = discord.Embed(title="Ignored Users", description="List of users ignored by the music bot", color=bot_color)
        if len(entries) > 0:
            for entry in entries:
                member = ctx.guild.get_member(entry[2])
                ignore_embed.add_field(name = member.name, value = "Ignored", inline=False)
            await ctx.send(embed=ignore_embed)
            return
        else:
            ignore_embed.add_field(name="No Ignored Users", value="No users are currently ignored by the music bot.", inline=False)
            await ctx.send(embed=ignore_embed)
            return
            
    name = user.name
    id = int(user.id)
    SQL = f"UPDATE musicbot SET ignore = NOT ignore WHERE id = {id};"

    cur.execute(SQL)
    conn.commit()

    SQL = f"SELECT ignore FROM musicbot WHERE id = {id};"
    cur.execute(SQL)
    ignored = cur.fetchone()[0]
    if ignored:
        await ctx.send(f"{name} is now being ignored by the music bot.")
    else:
        await ctx.send(f"{name} is no longer being ignored by the music bot.")

@bot.command(name="remove", description="Lets a user remove a song from the queue")
async def remove(ctx, index: int):
    cur.execute(f"SELECT ignore FROM musicbot WHERE id = {int(ctx.author.id)};")
    ignored = cur.fetchone()[0]
    server_name = "t"+str(ctx.guild.id)

    cur.execute(f"SELECT channels FROM {server_name};")
    channelWhitelist = [channel[0] for channel in cur.fetchall() if type(channel[0]) is int]

    if len(channelWhitelist) > 0 and int(ctx.channel.id) not in channelWhitelist:
        await ctx.message.delete()
        mess = await ctx.send(":x: This channel is not on the bot's whitelist")
        await asyncio.sleep(5)
        await mess.delete()
        return
    elif ignored:
        return
    if index < 1 or index > len(music_queue):
        await ctx.send("That is not a valid queue position.")
        return

    song = music_queue.pop(index-1)
    await ctx.send(f"Removed `{song[1]} - {song[2]}` queued by {song[4].mention}")

@bot.command(name="nowplaying", description="Displays the song that is currently playing", aliases=["np"])
async def nowplaying(ctx):
    server_name = "t"+str(ctx.guild.id)

    cur.execute(f"SELECT channels FROM {server_name};")
    channelWhitelist = [channel[0] for channel in cur.fetchall() if type(channel[0]) is int]

    if len(channelWhitelist) > 0 and int(ctx.channel.id) not in channelWhitelist:
        await ctx.message.delete()
        mess = await ctx.send(":x: This channel is not on the bot's whitelist")
        await asyncio.sleep(5)
        await mess.delete()
        return

    percent_done = (round((int(datetime.datetime.now().timestamp())-now_playing[5])/col_to_sec(now_playing[3]),2)*100)
    bar_string = ""
    current_time = f"{str(datetime.timedelta(seconds=int(int(datetime.datetime.now().timestamp())-now_playing[5])))}"
    for i in range(math.floor(int(percent_done)/10)-1):
        bar_string += ":white_large_square:"

    bar_string += ":white_square_button:"
    
    for i in range((10-math.floor(int(percent_done)/10))-1):
        bar_string += ":white_large_square:"
    
    nowplaying_embed = discord.Embed(title = ":musical_note: Now Playing :musical_note:", description="", color=bot_color)
    nowplaying_embed.add_field(name=f"{now_playing[1]}", value=f"Artist: {now_playing[2]}\nRuntime: {now_playing[3]}\nQueued by: {now_playing[4].mention}", inline=False)
    nowplaying_embed.add_field(name="Song Progress", value=f"Current Time: {current_time} - {percent_done:.2f}% \n 0:00 |{bar_string}| {now_playing[3]}", inline=False)
    await ctx.send(embed=nowplaying_embed)

@bot.group(name="settings", description="Allows an admin to change the settings of the bot", invoke_without_command=True)
async def settings(ctx):
    server_name = "t"+str(ctx.guild.id)

    cur.execute(f"SELECT mods FROM {server_name};")
    modIDS = [id[0] for id in cur.fetchall() if type(id[0]) is int]

    cur.execute(f"SELECT channels FROM {server_name};")
    channelWhitelist = [channel[0] for channel in cur.fetchall() if type(channel[0]) is int]

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
    else:
        settings_embed = discord.Embed(title = "Settings", description = "", color=bot_color)
        settings_embed.add_field(name="Channels", value = f"This setting allows you to add or remove channels that the bot will listen to \n `channels` - lets you view the currently whitelisted channels \n `addchannel` - adds a channel to the bots whitelist \n `removechannel` - removes a channel from the bots whitelist", inline=False)
        settings_embed.add_field(name="Mods", value = f"This setting allows you to add or remove mods that can change bot settings \n `mods` - lets you view the current list of mods \n `addmod` - lets you add a mod \n `removemod` - lets you remove a mod")
        settings_embed.add_field(name="Prefix", value = f"This setting allows you to change the prefix the bot uses for commands \n `prefix` - lets you change the bot's prefix", inline=False)
        settings_embed.set_footer(text = "ex. `!settings addchannel #general`, `!settings prefix ?`, etc...")
        await ctx.send(embed=settings_embed)

@settings.command(name="channels", description="Lets you view the currently whitelisted channels", aliases=["c"])
async def channels(ctx):
    server_name = "t"+str(ctx.guild.id)

    cur.execute(f"SELECT mods FROM {server_name};")
    modIDS = [id[0] for id in cur.fetchall() if type(id[0]) is int]

    cur.execute(f"SELECT channels FROM {server_name};")
    channelWhitelist = [channel[0] for channel in cur.fetchall() if type(channel[0]) is int]

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
    elif len(channelWhitelist) == 0:
        await ctx.send(":x: No channels are whitelisted. Commands can be accepted from any channel.")
        return
    else:
        channelEmbed = discord.Embed(title="Channel Whitelist", description = "", color=bot_color)
        for channelID in channelWhitelist:
            channel = bot.get_channel(channelID)
            channelEmbed.add_field(name=channel.name, value=":white_circle: This channel is whitelisted", inline=False)

        await ctx.send(embed=channelEmbed)
        return
        
@settings.command(name="addchannel", description="Lets you add a channel to the whitelist", aliases=["ac"])
async def add_channel(ctx, channel: discord.TextChannel):
    server_name = "t"+str(ctx.guild.id)

    cur.execute(f"SELECT mods FROM {server_name};")
    modIDS = [id[0] for id in cur.fetchall() if type(id[0]) is int]

    cur.execute(f"SELECT channels FROM {server_name};")
    channelWhitelist = [channel[0] for channel in cur.fetchall() if type(channel[0]) is int]

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
    elif channel not in ctx.guild.text_channels:
        await ctx.send(":x: That is not a valid text channel.")
        return
    elif channel.id in channelWhitelist:
        await ctx.send(":x: That channel is already in the bot's whitelist.")
        return
    else:
        SQL = f"INSERT INTO {server_name}(channels) VALUES ({int(channel.id)});"
        cur.execute(SQL)
        conn.commit()
        await ctx.send(f"`{channel.name}` has been added to the bot's whitelist.")
        return

@settings.command(name="removechannel", description="Lets you remove a channel from the whitelist", aliases=["rc"])
async def remove_channel(ctx, channel: discord.TextChannel):
    server_name = "t"+str(ctx.guild.id)

    cur.execute(f"SELECT mods FROM {server_name};")
    modIDS = [id[0] for id in cur.fetchall() if type(id[0]) is int]

    cur.execute(f"SELECT channels FROM {server_name};")
    channelWhitelist = [channel[0] for channel in cur.fetchall() if type(channel[0]) is int]

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
    elif channel not in ctx.guild.text_channels:
        await ctx.send(":x: That is not a valid text channel.")
        return
    elif (channel.id,) not in channelWhitelist:
        await ctx.send(":x: That channel is not currently on the bot's whitelist.")
        return
    else:
        SQL = f"UPDATE {server_name} SET channel = NULL WHERE channel = {int(channel.id)};"
        cur.execute(SQL)
        conn.commit()
        await ctx.send(f"`{channel.name}` has been removed from the bot's whitelist.")
        return

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
        return
        await mess.delete()
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

@bot.event
async def on_member_join(member):
    #insert into musicbot
    SQL = f"INSERT INTO musicbot(ignore, id) VALUES (False, {member.id});"
    cur.execute(SQL)
    conn.commit()


@bot.event
async def on_member_leave(member):
    #delete from music bot
    SQL = f"DELETE FROM musicbot WHERE id={member.id};"
    cur.execute(SQL)
    conn.commit()

@bot.event
async def on_guild_join(guild):
    main_channel = guild.text_channels[0]
    await main_channel.send(f":cd: Thanks for welcoming me to `{guild.name}`! My default prefix is `!`. You can change this and the channel I listen to with `!settings`.")

    server_name = "t"+str(guild.id)
    queue_name = "m"+str(guild.id)

    SQL = f"CREATE TABLE {server_name} (channels bigint, mods bigint, prefix varchar(255));"
    cur.execute(SQL)
    conn.commit()

    SQL = f"CREATE TABLE {queue_name} (song varchar(255), title varchar(255), channel varchar(255), runtime varchar(255), author varchar(255), live bool);"
    cur.execute(SQL)
    conn.commit()

    SQL = f"INSERT INTO prefixes(server_id,prefix) VALUES ({guild.id}, '{DEFAULT_PREFIX}');"
    cur.execute(SQL)
    conn.commit()

    SQL = f"INSERT INTO {server_name}(mods) VALUES (288710564367171595);"
    cur.execute(SQL)
    conn.commit()

    for member in guild.members:
        if member.bot:
            continue
        SQL = f"INSERT INTO musicbot(ignore, id) VALUES (False, {int(member.id)});"
        cur.execute(SQL)
        conn.commit()

        if member.top_role.permissions.administrator:
            SQL = f"INSERT INTO {server_name}(mods) VALUES ({int(member.id)});"
            cur.execute(SQL)
            conn.commit()

@bot.event
async def on_guild_remove(guild):
    server_name = "t"+str(guild.id)
    queue_name = "m"+str(guild.id)

    for member in guild.members:
        SQL = f"DELETE FROM musicbot WHERE id={member.id};"
        cur.execute(SQL)
        conn.commit()
    
    SQL = f"DELETE FROM prefixes WHERE server_id={guild.id};"
    cur.execute(SQL)
    conn.commit()
    
    SQL = f"DROP TABLE {server_name};"
    cur.execute(SQL)
    conn.commit()

    SQL = f"DROP TABLE {queue_name};"
    cur.execute(SQL)
    conn.commit()
    
#--------------------------------------------------------------------------------------------------------------------------------------#
#runs the bot using the discord bot token provided within Heroku
bot.run(os.environ['token'])

