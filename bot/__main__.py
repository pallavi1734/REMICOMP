#    This file is part of the Encoder distribution.
#    Copyright (c) 2023 Danish_00, Nubuki-all
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
#    General Public License for more details.
#
# License can be found in
# <https://github.com/Nubuki-all/Enc/blob/main/License> .

import asyncio
import itertools

from pyrogram import filters

from . import LOGS, conf, events, pyro, re, tele
from .startup.after import on_startup
from .utils.msg_utils import event_handler
from .workers.handlers.dev import bash
from .workers.handlers.dev import eval as eval_
from .workers.handlers.dev import eval_message_p
from .workers.handlers.e_callbacks import pres, skip, stats
from .workers.handlers.manage import (
    allowgroupenc,
    auto_rename,
    change,
    check,
    clean,
    del_auto_rename,
    discap,
    fc_forward,
)
from .workers.handlers.manage import filter as filter_
from .workers.handlers.manage import (
    get_mux_args,
    nuke,
    pause,
    reffmpeg,
    restart,
    rmfilter,
   # rss_handler,
    save_thumb,
    set_mux_args,
    update2,
    v_auto_rename,
    version2,
    vfilter,
)
from .workers.handlers.queue import (
    addqueue,
    clearqueue,
    edit_batch,
    enleech,
    enleech2,
    enselect,
    listqueue,
    pencode,
)
from .workers.handlers.rebut import (
    en_airing,
    en_anime,
    en_download,
    en_list,
    en_mux,
    en_rename,
    en_upload,
    getlogs,
    getthumb,
)
from .workers.handlers.stuff import beck
from .workers.handlers.stuff import help as help_
from .workers.handlers.stuff import (
    icommands,
    ihelp,
    start,
    status,
    up,
)

cmd_suffix = conf.CMD_SUFFIX.strip()
LOGS.info("Starting...")


######## Connect ########


try:
    tele.start(bot_token=conf.BOT_TOKEN)
    pyro.start()
except Exception as er:
    LOGS.info(er)


####### CMD FILTER ########
async def get_me():
    globals()["me"] = await tele.get_me()


loop = asyncio.get_event_loop()
loop.run_until_complete(get_me())

LOGS.info(f"@{me.username} is ready!")


def command(commands: list, prefixes: list = ["/"]):
    while len(commands) < len(prefixes):
        commands.append(commands[-1])
    pattern = ""
    for command, prefix in itertools.zip_longest(commands, prefixes, fillvalue="/"):
        if cmd_suffix:
            command += cmd_suffix
        pattern += rf"{prefix}{command}(?:@{me.username})?(?!\S)|"
    return pattern.rstrip("|")


####### GENERAL CMDS ########


@tele.on(events.NewMessage(pattern=command(["start"])))
async def _(e):
    await event_handler(e, start)


@tele.on(events.NewMessage(pattern="/ping"))
async def _(e):
    await event_handler(e, up)


@tele.on(events.NewMessage(pattern=command(["help"])))
async def _(e):
    await event_handler(e, help_)


@tele.on(events.NewMessage(pattern=command(["showthumb"])))
async def _(e):
    await event_handler(e, getthumb)


@tele.on(events.NewMessage(pattern=command(["status"])))
async def _(e):
    await event_handler(e, status)


####### POWER CMDS #######


@tele.on(events.NewMessage(pattern=command(["restart"])))
async def _(e):
    await event_handler(e, restart)


@tele.on(events.NewMessage(pattern=command(["nuke"])))
async def _(e):
    await event_handler(e, nuke)


@pyro.on_message(filters.incoming & filters.command([f"update{cmd_suffix}"]))
async def _(pyro, message):
    await update2(pyro, message)


@tele.on(events.NewMessage(pattern=command(["clean", "cancelall"])))
async def _(e):
    await event_handler(e, clean)


@tele.on(events.NewMessage(pattern=command(["clear"])))
async def _(e):
    await event_handler(e, clearqueue, require_args=True)


@tele.on(events.NewMessage(pattern=command(["get"])))
async def _(e):
    await event_handler(e, check)


@tele.on(events.NewMessage(pattern=command(["set"])))
async def _(e):
    await event_handler(e, change, require_args=True)


@tele.on(events.NewMessage(pattern=command(["reset"])))
async def _(e):
    await event_handler(e, reffmpeg)


@tele.on(events.NewMessage(pattern=command(["lock", "pause"])))
async def _(e):
    await event_handler(e, pause)


######## Callbacks #########


@tele.on(events.callbackquery.CallbackQuery(data=re.compile(b"stats(.*)")))
async def _(e):
    await stats(e)


@tele.on(events.callbackquery.CallbackQuery(data=re.compile(b"pres(.*)")))
async def _(e):
    await pres(e)


@tele.on(events.callbackquery.CallbackQuery(data=re.compile(b"skip(.*)")))
async def _(e):
    await skip(e)


@tele.on(events.callbackquery.CallbackQuery(data=re.compile(b"dl_stat(.*)")))
async def _(e):
    await dl_stat(e)


@tele.on(events.callbackquery.CallbackQuery(data=re.compile(b"cancel_dl(.*)")))
async def _(e):
    await cancel_dl(e)


@tele.on(events.callbackquery.CallbackQuery(data=re.compile("ihelp")))
async def _(e):
    await ihelp(e)


@tele.on(events.callbackquery.CallbackQuery(data=re.compile("icommands")))
async def _(e):
    await icommands(e)


@tele.on(events.callbackquery.CallbackQuery(data=re.compile("beck")))
async def _(e):
    await beck(e)


########## Direct ###########


@tele.on(events.NewMessage(pattern=command(["eval"])))
async def _(e):
    await event_handler(e, eval_, pyro, True)


@tele.on(events.NewMessage(pattern=command(["leech", "l"])))
async def _(e):
    await event_handler(e, enleech, pyro)


@tele.on(events.NewMessage(pattern=command(["list"], ["/", "!"])))
async def _(e):
    await event_handler(e, en_list, pyro, require_args=True)


@tele.on(events.NewMessage(pattern=command(["upload", "ul"], ["/", "!", "/"])))
async def _(e):
    await event_handler(e, en_upload, pyro, require_args=True)


@pyro.on_message(filters.incoming & filters.command([f"peval{cmd_suffix}"]))
async def _(pyro, message):
    await event_handler(message, eval_message_p, tele, require_args=True)


@pyro.on_message(
    filters.incoming
    & filters.command([f"fforward{cmd_suffix}", f"forward{cmd_suffix}"])
)
async def _(pyro, message):
    await event_handler(message, fc_forward)


@tele.on(events.NewMessage(pattern=command(["bash"])))
async def _(e):
    await event_handler(e, bash, require_args=True)



@tele.on(events.NewMessage(pattern=command(["queue"], ["/", "!"])))
async def _(e):
    await event_handler(e, listqueue)


######## DEBUG #########


@tele.on(events.NewMessage(pattern=command(["logs"])))
async def _(e):
    await event_handler(e, getlogs)


########## AUTO ###########


@tele.on(events.NewMessage(incoming=True))
async def _(e):
    await event_handler(e, save_thumb, disable_help=True)


# @tele.on(events.NewMessage(incoming=True))
# async def _(e):
#    await encod(e)


@pyro.on_message(filters.incoming & (filters.video | filters.document))
async def _(pyro, message):
    await pencode(message)


########### Start ############

LOGS.info(f"{me.first_name} has started.")
with tele:
    tele.loop.run_until_complete(on_startup())
    tele.loop.run_forever()
