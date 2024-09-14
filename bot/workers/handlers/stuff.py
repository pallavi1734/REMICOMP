import os
import shutil
import time

import psutil

from bot import Button, botStartTime, dt, subprocess, version_file
from bot.config import _bot, conf
from bot.fun.emojis import enmoji
from bot.utils.bot_utils import add_temp_user, get_readable_file_size, rm_temp_user
from bot.utils.bot_utils import time_formatter as tf
from bot.utils.db_utils import save2db2
from bot.utils.msg_utils import (
    edit_message,
    pm_is_allowed,
    reply_message,
    temp_is_allowed,
    user_is_allowed,
    user_is_owner,
)
from bot.utils.os_utils import file_exists


async def up(event, args, client):
    """ping bot!"""
    if not user_is_allowed(event.sender_id):
        return await event.delete()
    ist = dt.now()
    msg = await reply_message(event, "…")
    st = dt.now()
    ims = (st - ist).microseconds / 1000
    msg1 = "**Pong! ——** `{}`__ms__"
    st = dt.now()
    await edit_message(msg, msg1.format(ims))
    ed = dt.now()
    ms = (ed - st).microseconds / 1000
    await edit_message(msg, f"1. {msg1.format(ims)}\n2. {msg1.format(ms)}")


async def status(event, args, client):
    """Gets status of bot and server where bot is hosted.
    Requires no arguments."""
    if not user_is_allowed(event.sender_id):
        return await event.delete()
    branch = _bot.repo_branch or "❓"
    last_commit = "UNAVAILABLE!"
    if os.path.exists(".git"):
        try:
            last_commit = subprocess.check_output(
                ["git log -1 --date=short --pretty=format:'%cd || %cr'"], shell=True
            ).decode()
        except Exception:
            pass

    if file_exists(version_file):
        with open(version_file, "r") as file:
            vercheck = file.read().strip()
            file.close()
    else:
        vercheck = "Tf?"
    currentTime = tf(time.time() - botStartTime)
    ostime = tf(time.time() - psutil.boot_time())
    swap = psutil.swap_memory()
    total, used, free = shutil.disk_usage(".")
    total = get_readable_file_size(total)
    used = get_readable_file_size(used)
    free = get_readable_file_size(free)
    sent = get_readable_file_size(psutil.net_io_counters().bytes_sent)
    recv = get_readable_file_size(psutil.net_io_counters().bytes_recv)
    cpuUsage = psutil.cpu_percent(interval=0.5)
    p_cores = psutil.cpu_count(logical=False)
    t_cores = psutil.cpu_count(logical=True)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/").percent
    await event.reply(
        f"**Version:** `{vercheck}`\n"
        f"**Branch:** `{branch}`\n"
        f"**Commit Date:** `{last_commit}`\n\n"
        f"**Bot Uptime:** `{currentTime}`\n"
        f"**System Uptime:** `{ostime}`\n\n"
        f"**Total Disk Space:** `{total}`\n"
        f"**Used:** `{used}` "
        f"**Free:** `{free}`\n\n"
        f"**SWAP:** `{get_readable_file_size(swap.total)}`"
        f"** | **"
        f"**Used:** `{swap.percent}%`\n\n"
        f"**Upload:** `{sent}`\n"
        f"**Download:** `{recv}`\n\n"
        f"**Physical Cores:** `{p_cores}`\n"
        f"**Total Cores:** `{t_cores}`\n\n"
        f"**CPU:** `{cpuUsage}%` "
        f"**RAM:** `{memory.percent}%` "
        f"**DISK:** `{disk}%`\n\n"
        f"**Total RAM:** `{get_readable_file_size(memory.total)}`\n"
        f"**Used:** `{get_readable_file_size(memory.used)}` "
        f"**Free:** `{get_readable_file_size(memory.available)}`"
    )


async def start(event, args, client):
    """A function for the start command, accepts no arguments yet!"""
    currentTime = tf(time.time() - botStartTime)
    msg = ""
    msg1 = f"Hi **{event.sender.first_name}**\n"
    msg2 = (
        f"{msg1}\n**__I've been alive for {currentTime} and i'm ready to encode videos 😗__**\n"
    )
    msg3 = f"{msg2}\nand by the way you're a temporary user"
    user = event.sender_id
    if not user_is_owner(user) and event.is_private:
        if not pm_is_allowed(in_pm=True):
            return await event.delete()
    if temp_is_allowed(user):
        msg = msg3
    elif not user_is_allowed(user):
        priv = await event.client.get_entity(int(conf.OWNER.split()[0]))
        msg = f"{msg1}\n__**I've been alive for {currentTime} and i'm ready to encode videos 😗**__\n"
       # msg += "\n```Resolution: 854x480```\n"
        msg += f"\n**OWNER:** [{priv.first_name}](tg://user?id={conf.OWNER.split()[0]}) "
   
    if not msg:
        msg = msg2
    await event.reply(
        msg,
        buttons=[
            [Button.url("⚡ 𝖴𝗉𝖽𝖺𝗍𝖾𝗌", url='t.me/Rokubotz'), Button.url('⚡ 𝖲𝗎𝗉𝗉𝗈𝗋𝗍', url='t.me/Team_Roku')],
            [Button.url('👨‍💻 𝖣𝖾𝗏𝖾𝗅𝗈𝗉𝖾𝗋', url='t.me/MysteryDemon'), Button.inline('❗ 𝖧𝖾𝗅𝗉', data="ihelp")]
        ],
    )



async def help(event, args, client):
    return await start(event, args, client)


async def ihelp(event):
    await event.edit(
        "**⛩️ An Encode bot**\n\n+"
        "This bot encodes videos With your custom ffmpeg or handbrake-cli settings."
        "\n+Easy to Use (Depends)\n"
        "-Due to your custom Settings & hosting server bot may or may not take a long time to encode"
        "\n\nFor available commands click the Commands button below.",
        buttons=[
            [Button.inline("Commands", data="icommands")],
            [Button.inline("« Bᴀᴄᴋ", data="beck")],
        ],
    )


async def beck(event):
    sender = event.query.user_id
    currentTime = tf(time.time() - botStartTime)
    msg = ""
    msg1 = f"Hi **{event.sender.first_name}**\n"
    msg2 = (
        f"{msg1}\n**__I've been alive for {currentTime} and i'm ready to encode videos 😗__**\n"
     )
    msg3 = f"{msg2}\nand by the way you're a temporary user"
    if temp_is_allowed(sender):
        msg = msg3
    elif not user_is_allowed(sender):
        priv = await event.client.get_entity(int(conf.OWNER.split()[0]))
        msg = f"{msg1}\n__**I've been alive for {currentTime} and i'm ready to encode videos 😗**__\n"
       # msg += "\n```Resolution: 854x480```\n"
        msg += f"\n**OWNER:** [{priv.first_name}](tg://user?id={conf.OWNER.split()[0]}) "
    if not msg:
        msg = msg2
    await event.edit(
        msg,
        buttons=[
            [Button.url("⚡ 𝖴𝗉𝖽𝖺𝗍𝖾𝗌", url='t.me/Rokubotz'), Button.url('⚡ 𝖲𝗎𝗉𝗉𝗈𝗋𝗍', url='t.me/Team_Roku')],
            [Button.url('👨‍💻 𝖣𝖾𝗏𝖾𝗅𝗈𝗉𝖾𝗋', url='t.me/MysteryDemon'), Button.inline('❗ 𝖧𝖾𝗅𝗉', data="ihelp")]
        ],
    )


async def icommands(event):
    s = conf.CMD_SUFFIX or str()
    await event.edit(
        f"""
/start{s} - check if bot is awake and get usage.
/restart{s} -  restart bot
/leech{s} - download torrent or magnet links 
/ping - ping!
/queue{s} - list queue
/forward{s} - manually forward a message to fchannel
/upload{s} - upload from a local directory or link
/get{s} - get current ffmpeg code
/status{s} - get bot's status
/showthumb{s} - show current thumbnail
/cancelall{s} - clear cached downloads & queued files
/clear{s} - clear queued files
/logs{s} - get bot logs
/help{s} - same as start
 """,
        buttons=[Button.inline("« Bᴀᴄᴋ", data="ihelp")],
)
