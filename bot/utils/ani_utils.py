import pyrogram 

from telethon.tl.types import InputPeerEmpty, InputPeerChannel, InputPeerUser, PeerChannel
from telethon.errors.rpcerrorlist import PeerFloodError, UserPrivacyRestrictedError
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.functions.messages import SendMessageRequest
import sys
import os
import random
import time
import logging
import requests
#from bs4 import BeautifulSoup
import re

from pyrogram import Client 

from telethon import events, Button 
import string
from datetime import datetime

import aiohttp
import anitopy
import country_converter as coco
import flag
import humanize
import pycountry

from bot import conf, parse_file #, release_name, release_name_b

from .bot_utils import (
    auto_rename,
    crc32,
    get_codec,
    post_to_tgph,
    sync_to_async,
    text_filter,
    txt_to_str,
)
from .log_utils import log, logger
from .os_utils import check_ext, file_exists, get_stream_info, info, p_dl

ar_file = "Auto-rename.txt"
filter_file = "filter.txt"
url = "https://graphql.anilist.co"

anime_query = """
query ($id: Int, $idMal:Int, $search: String, $type: MediaType, $asHtml: Boolean) {
  Media (id: $id, idMal: $idMal, search: $search, type: $type) {
    id
    idMal
    title {
      romaji
      english
      native
    }
    format
    status
    description (asHtml: $asHtml)
    startDate {
      year
      month
      day
    }
    season
    episodes
    duration
    countryOfOrigin
    source (version: 2)
    trailer {
      id
      site
      thumbnail
    }
    coverImage {
      extraLarge
    }
    bannerImage
    genres
    averageScore
    nextAiringEpisode {
      airingAt
      timeUntilAiring
      episode
    }
    isAdult
    characters (role: MAIN, page: 1, perPage: 10) {
      nodes {
        id
        name {
          full
          native
        }
        image {
          large
        }
        description (asHtml: $asHtml)
        siteUrl
      }
    }
    studios (isMain: true) {
      nodes {
        name
        siteUrl
      }
    }
    siteUrl
  }
}
"""


airing_query = """
query ($id: Int, $mediaId: Int, $notYetAired: Boolean) {
  Page(page: 1, perPage: 50) {
    airingSchedules (id: $id, mediaId: $mediaId, notYetAired: $notYetAired) {
      id
      airingAt
      timeUntilAiring
      episode
      mediaId
      media {
        title {
          romaji
          english
          native
        }
        duration
        coverImage {
          extraLarge
        }
        nextAiringEpisode {
          airingAt
          timeUntilAiring
          episode
        }
        bannerImage
        averageScore
        siteUrl
      }
    }
  }
}
"""


async def get_ani_info(title=None, query=anime_query, var=None):
    variables = var or {"search": title, "type": "ANIME"}
    async with aiohttp.ClientSession() as requests:
        result = await requests.post(url, json={"query": query, "variables": variables})
        if var:
            return await result.json()
        info = (await result.json())["data"].get("Media")
    return info


async def get_cus_tag(fn, rg, caption=False):
    release_tag, file_tag, caption_tag = None, str(), None
    file_filter, release_filter, caption_filter = await text_filter()
    if release_filter and rg:
        for item in release_filter.split("\n"):
            if len(item.split("|")) <= 2:
                continue
            check, out, out1 = item.split("|")
            out = out1 if caption else out
            if check.casefold() != rg.casefold():
                continue
            if out.casefold() == "disable":
                break
            release_tag = out
            break

    if file_filter:
        for item in file_filter.split("\n"):
            if len(item.split("|")) <= 2:
                continue
            check, out, out1 = item.split("|")
            out = out1 if caption else out
            if check.startswith("^"):
                if not check.lstrip("^") in fn:
                    continue
                if out.casefold() == "disable":
                    break
            else:
                if not check.casefold() in fn.casefold():
                    continue
            if out.casefold() == "disable":
                continue
            file_tag += out
            if check.startswith("^"):
                break
            if not caption:
                break
            file_tag += " "

    if caption_filter and caption:
        for item in caption_filter.split("\n"):
            if len(item.split("||")) < 2:
                continue
            _check_r, _check_i = item.split("||", maxsplit=1)
            if _check_r != rg:
                continue
            for items in _check_i.split("||"):
                if len(items.split("|")) < 2:
                    continue
                check, out = items.split("|")
                if check in fn:
                    caption_tag = out
                    break

    final_output = release_tag
    if caption_tag:
        final_output = (
            caption_tag + " : " + final_output if final_output else caption_tag
        )

    return file_tag.strip() if not final_output else final_output


async def get_file_tag(_infile, caption=False, audio_only=False):
    _ainfo, _sinfo = await get_stream_info(_infile)
    if caption:
        if _ainfo:
            if len(_ainfo.split("|")) > 3:
                out = "MULTi"
            elif len(_ainfo.split("|")) == 3:
                out = "Tri"
            elif len(_ainfo.split("|")) == 2:
                out = "Dual"
            else:
                out = None if not audio_only else _ainfo
        elif _ainfo is None:
            out = "TBD"
    else:
        if caption: #_ainfo or _sinfo:
            out = ""
            if _ainfo:
                audio_count = len(_ainfo.split("|"))
                if audio_count > 3:
                    out += f"(Multi-Audio)[{audio_count}] "
                elif audio_count == 3:
                    out += "(Tri-Audio) "
                elif audio_count == 2:
                    out += f"(Dual-Audio) "
            if _sinfo:
                subs = _sinfo.split("|")
                sub_count = len(subs)
                if sub_count > 2:
                    out += f"(Multi-Subs)[{sub_count}]"
                elif sub_count > 1:
                    __dual = False
                    if _ainfo and audio_count == 2:
                        if subs[0] == "eng" and subs[0] == subs[1]:
                            __dual = True
                    if not __dual:
                        if subs[0] != subs[1]:
                            out += f"({subs[0]} & {subs[1]} subs)"
                        else:
                            out += f"({subs[0].title()}-subs)"
                else:
                    __dual = False
                    if _ainfo and audio_count == 2:
                        if _sinfo == "eng":
                            __dual = True
                    if not __dual:
                        out += f"({_sinfo.title()}-sub)"

        else:
            out = None
    return out


def get_flag(lang_t):
    if not lang_t == "?":
        if "-" in lang_t:
            lang_t1, lang_t2 = lang_t.split("-", maxsplit=1)
            if lang_t2.isdigit():
                lang_t = lang_t1
            else:
                lang_t = lang_t2
        if lang_t.casefold() == "eng":
            lang_t = "US"
        elif lang_t.casefold() == "ara":
            lang_t = "Arabia"
        elif lang_t.casefold() == "hin":
            lang_t = "ind"
        elif lang_t.casefold() == "ind":
            lang_t = "Indonesia"
        try:
            lang_t = pycountry.countries.search_fuzzy(lang_t)
        except Exception:
            return " 🇱🇱͜ "
        lang_t = lang_t[0].alpha_2
        lang_t = flag.flag(lang_t)
    return lang_t


async def filter_name(name, _filter):
    fil1 = fil2 = fil3 = str()
    try:
        if _filter:
            fil = _filter.strip("\n")
            if len(fil.split("\n")) < 3:
                raise Exception("Malformed filter!")
            fil1, fil2, fil3 = fil.split("\n")

        elif file_exists(filter_file):
            with open(filter_file, "r") as file:
                fil = file.read().strip("\n")
            if len(fil.split("\n")) < 3:
                raise Exception("Malformed filter!")
            fil1, fil2, fil3 = fil.split("\n")

        if fil1 and fil1.casefold() != "disable":
            for i in fil1.split("|"):
                name = name.replace(i, "")
        if fil2.casefold() == "disable":
            fil2 = None
        if fil3.casefold() == "disable":
            fil3 = None
    except Exception:
        await logger(Exception)

    return name, fil2, fil3


def conconvert(iso2_codes):
    try:
        iso3_codes = coco.convert(names=iso2_codes, to="ISO3").capitalize()
    except Exception:
        log(Exception)
    return iso3_codes

async def parse(
    name,
    _file=None,
    _ext=".mkv",
    anilist=True,
    cust_con=None,
    v=None,
    folder="downloads/",
    _filter=None,
    ccodec=None,
):
    try:
        if _file:
            file_name = _file
            file_name2 = file_name
        else:
            file_name = f"{name}"
            file_name2 = file_name
    except Exception as e:
        print("An error occurred:", e)
    if "/" in file_name:
        file_name = file_name.replace("/", " ")
    return file_name, file_name2


async def dynamicthumb(name, thum="thumb2.jpg", anilist=True, _filter=None):
    try:
        name, fil2, fil3 = await filter_name(name, _filter)
        ## Get info ##
        parsed = anitopy.parse(name)
        # title
        title = parsed.get("anime_title")
        # episode number
        epi = parsed.get("episode_number")
        # season number
        sn = parsed.get("anime_season")
        if isinstance(sn, list):
            sn = sn[0]
        if sn and sn.startswith("0"):
            sn = str(int(sn))
        if sn == "1":
            sn = None
        # release group
        rg = parsed.get("release_group")
        if file_exists(parse_file) or not anilist:
            raise Exception("Parsing turned off")
        try:
            json = await get_ani_info(title)
            t_title = json["title"]["english"]
            t_title = json["title"]["romaji"] if not t_title else t_title
        except Exception:
            t_title = title
        s_title = t_title
        if sn:
            s_title += " " + sn
        try:
            json = await get_ani_info(s_title)
            link = json.get("coverImage")["extraLarge"]
        except Exception:
            try:
                json = await get_ani_info(title)
                link = json.get("coverImage")["extraLarge"]
            except Exception:
                pass
                # await logger(Exception)
        await sync_to_async(p_dl, link, thum)
    except Exception:
        pass
        # log(Exception)
    return title, epi, sn, rg

async def custcap(
    name,
    fname,
    anilist=True, 
    cust_type=None,
    folder="encode/",
    ccd=None,
    ver=None,
    encoder=None,
    _filter=None,
    ccodec=None,
):
    try:
        caption = f"{fname}"
    except Exception:
        await logger(Exception)
        caption = f"{fname}"
    return caption
    
    
    if not conf.EXT_CAP:
        return await simplecap(
            name, fname, anilist, cust_type, folder, ver, encoder, _filter, ccodec
        )
    try:
        om = fname.split(".")[0]
        ot = om.split("@")[0]
        caption = f"**{ot}**\n\n**🔗 {conf.C_LINK}**"
        return caption
    except Exception:
        await logger(Exception)
        om = fname.split(".")[0]
        ot = om.split("@")[0]
        caption = f"**{ot}**\n\n**🔗 {conf.C_LINK}**"
    return caption


async def simplecap(
    name,
    fname,
    anilist=True,
    cust_type=None,
    folder="encode/",
    ver=None,
    encoder=None,
    _filter=None,
    ccodec=None,
):
    if conf.FL_CAP:
        return f"`{fname}`"
    if not conf.EXT_CAP:
        return await simplecap(
            name, fname, anilist, cust_type, folder, ver, encoder, _filter, ccodec
        )
    try:
        om = fname.split(".")[0]
        ot = om.split("@")[0]
        caption = f"**{ot}**\n\n**🔗 {conf.C_LINK}**"
        return caption
    except Exception:
        await logger(Exception)
        om = fname.split(".")[0]
        ot = om.split("@")[0]
        caption = f"**{ot}**\n\n**🔗 {conf.C_LINK}**"
    return caption


async def qparse(name, ver=None, fil=None):
    return (await parse(name, v=ver, _filter=fil))[0]


async def qparse_t(name, ver=None, fil=None):
    re = anitopy.parse(await qparse(name, ver, fil))
    return re.get("anime_title") + str().join(
        f" {x}" if x else str() for x in [re.get("anime_year"), re.get("anime_season")]
    )


async def f_post(name, out, fcodec=None, mi=None, _filter=None, evt=True):
    if conf.NO_BANNER:
        return None, None
    try:
        name = (await filter_name(name, _filter))[0]
        ## Get info ##
        parsed = anitopy.parse(name)
        # title
        title = parsed.get("anime_title")
        # episode number
        epi = parsed.get("episode_number")
        if epi and not evt:
            if epi in ("1", "01", "001"):
                epi = None
            else:
                return None, None
        # season number
        sn = parsed.get("anime_season")
        # release group
        rg = parsed.get("release_group")
        if isinstance(sn, list):
            sn = sn[0]
        if sn and sn.startswith("0"):
            sn = str(int(sn))
        if sn == "1":
            sn = None

        codec = fcodec if fcodec else await get_codec()

        try:
            if file_exists(parse_file):
                raise Exception("Parsing turned off")
            json = await get_ani_info(title)
            if sn:
                s_title = title + " " + sn
                json2 = await get_ani_info(s_title)
            else:
                json2 = json
            title = json["title"]["english"]
            title = json["title"]["romaji"] if title is None else title
            title_r = json["title"]["romaji"]
            try:
                id_ = json2["id"]
            except Exception:
                id_ = json["id"]
            pic_url = f"https://img.anili.st/media/{id_}"
            con = f"{json['countryOfOrigin']}"
            gen = json.get("genres")
            genre = str()

        except Exception:
            title_r = "N/A"
            cflag = con = "?"
            gen = None
            pic_url = "https://upload.wikimedia.org/wikipedia/commons/d/d1/Image_not_available.png"
        a_lang = ""
        s_lang = ""

        _ainfo, _sinfo = await get_stream_info(out)
        if _ainfo:
            for a_lang_t in _ainfo.split("|"):
                a_lang += await sync_to_async(get_flag, a_lang_t)
                a_lang += ", "
            a_lang = a_lang.strip(", ")
        else:
            a_lang = "N/A"
        if _sinfo:
            for s_lang_t in _sinfo.split("|"):
                s_lang += get_flag(s_lang_t)
                s_lang += ", "
            s_lang = s_lang.strip(", ")
        else:
            s_lang = "N/A"

        cflag = flag.flag(con) if not con == "?" else con
        if gen:
            for x in gen:
                genre += "#" + (x.replace(" ", "_")).replace("-", "_") + " "

        msg = f"[{cflag}]"
        if title == title_r:
            msg += f"`{title}`"
        else:
            msg += f"**{title_r}** | `{title}`"
        msg += "\n\n"
        if rg or mi:
            msg += f"**Source:** **[[{rg}]]({mi})**"
            msg += "\n\n"
        if gen and genre:
            msg += f"**‣ Genre** : {genre}\n"
        if epi:
            msg += f"**‣ Episode** : `{epi}`\n"
        if sn:
            msg += f"**‣ Season** : `{sn}`\n"
        msg += f"**‣ Quality** : `{codec}`\n"
        msg += f"**‣ Audio(s)** : `{a_lang}`\n"
        msg += f"**‣ Subtitle(s)** : `{s_lang}`\n"
    except Exception:
        pic_url = None
        msg = None
        await logger(Exception)
    return pic_url, msg


# Default templates for Query Formatting
# https://github.com/UsergeTeam/Userge-Plugins/blob/dev/plugins/utils/anilist/__main__.py
ANIME_TEMPLATE = """[{c_flag}]**{romaji}**

**ID | MAL ID:** `{idm}` | `{idmal}`
➤ **SOURCE:** `{source}`
➤ **TYPE:** `{formats}`
➤ **GENRES:** `{genre}`
➤ **SEASON:** `{season}`
➤ **EPISODES:** `{episodes}`
➤ **STATUS:** `{status}`
➤ **NEXT AIRING:** `{air_on}`
➤ **SCORE:** `{score}%` 🌟
➤ **ADULT RATED:** `{adult}`
🎬 {trailer_link}
📖 [Synopsis & More]({synopsis_link})"""


def make_it_rw(time_stamp, as_countdown=False):
    """Converting Time Stamp to Readable Format"""
    if as_countdown:
        now = datetime.now()
        air_time = datetime.fromtimestamp(time_stamp)
        return str(humanize.naturaltime(now - air_time))
    return str(humanize.naturaldate(datetime.fromtimestamp(time_stamp)))


async def anime_arch(query, arg):
    """Search Anime Info"""
    vars_ = {"search": query, "asHtml": True, "type": "ANIME"}
    if query.isdigit():
        if arg.m:
            vars_ = {"idMal": int(query), "asHtml": True, "type": "ANIME"}
        else:
            vars_ = {"id": int(query), "asHtml": True, "type": "ANIME"}

    result = await get_ani_info(query=anime_query, var=vars_)
    error = result.get("errors")
    if error:
        log(e=f"**ANILIST RETURNED FOLLOWING ERROR:**\n\n`{error}`")
        error_sts = error[0].get("message")
        raise Exception(f"[{error_sts}]")

    data = result["data"]["Media"]
    # Data of all fields in returned json
    # pylint: disable=possibly-unused-variable
    idm = data.get("id")
    idmal = data.get("idMal")
    romaji = data["title"]["romaji"]
    english = data["title"]["english"]
    native = data["title"]["native"]
    formats = data.get("format")
    status = data.get("status")
    synopsis = data.get("description")
    season = data.get("season")
    episodes = data.get("episodes")
    duration = data.get("duration")
    country = data.get("countryOfOrigin")
    c_flag = flag.flag(country)
    source = data.get("source")
    coverImg = data.get("coverImage")["extraLarge"]
    bannerImg = data.get("bannerImage")
    genres = data.get("genres")
    genre = genres[0] if genres else genres
    if genre and len(genres) > 1:
        genre = ", ".join(genres)
    score = data.get("averageScore")
    air_on = None
    if data["nextAiringEpisode"]:
        nextAir = data["nextAiringEpisode"]["airingAt"]
        air_on = make_it_rw(nextAir)
    s_date = data.get("startDate")
    adult = data.get("isAdult")
    trailer_link = "N/A"

    if data["trailer"] and data["trailer"]["site"] == "youtube":
        trailer_link = f"[Trailer](https://youtu.be/{data['trailer']['id']})"
    html_char = ""
    for character in data["characters"]["nodes"]:
        html_ = ""
        html_ += "<br>"
        html_ += f"""<a href="{character['siteUrl']}">"""
        html_ += f"""<img src="{character['image']['large']}"/></a>"""
        html_ += "<br>"
        html_ += f"<h3>{character['name']['full']}</h3>"
        html_ += f"<em>{c_flag} {character['name']['native']}</em><br>"
        html_ += f"<b>Character ID</b>: {character['id']}<br>"
        html_ += (
            f"<h4>About Character and Role:</h4>{character.get('description', 'N/A')}"
        )
        html_char += f"{html_}<br><br>"

    studios = ""
    for studio in data["studios"]["nodes"]:
        studios += "<a href='{}'>• {}</a> ".format(studio["siteUrl"], studio["name"])
    url = data.get("siteUrl")

    title_img = coverImg or bannerImg
    html_pc = ""
    html_pc += f"<img src='{title_img}' title={romaji}/>"
    html_pc += f"<h1>[{c_flag}] {native}</h1>"
    html_pc += "<h3>Synopsis:</h3>"
    html_pc += synopsis
    html_pc += "<br>"
    if html_char:
        html_pc += "<h2>Main Characters:</h2>"
        html_pc += html_char
        html_pc += "<br><br>"
    html_pc += "<h3>More Info:</h3>"
    html_pc += f"<b>Started On:</b> {s_date['day']}/{s_date['month']}/{s_date['year']}"
    html_pc += f"<br><b>Studios:</b> {studios}<br>"
    html_pc += f"<a href='https://myanimelist.net/anime/{idmal}'>View on MAL</a>"
    html_pc += f"<a href='{url}'> View on anilist.co</a>"
    html_pc += f"<img src='{bannerImg}'/>"

    title_h = english or romaji
    synopsis_link = (await post_to_tgph(title_h, html_pc))["url"]
    finals_ = ANIME_TEMPLATE.format(**locals())
    return title_img, finals_


async def airing_anim(query):
    """Get Airing Detail of Anime"""
    vars_ = {"search": query, "asHtml": True, "type": "ANIME"}
    if query.isdigit():
        vars_ = {"id": int(query), "asHtml": True, "type": "ANIME"}
    result = await get_ani_info(query=anime_query, var=vars_)
    error = result.get("errors")
    if error:
        alog(e=f"**ANILIST RETURNED FOLLOWING ERROR:**\n\n`{error}`")
        error_sts = error[0].get("message")
        raise Exception(f"[{error_sts}]")

    data = result["data"]["Media"]

    # Airing Details
    mid = data.get("id")
    romaji = data["title"]["romaji"]
    english = data["title"]["english"]
    native = data["title"]["native"]
    status = data.get("status")
    episodes = data.get("episodes")
    country = data.get("countryOfOrigin")
    c_flag = flag.flag(country)
    source = data.get("source")
    coverImg = data.get("coverImage")["extraLarge"]
    genres = data.get("genres")
    genres = data.get("genres")
    genre = genres[0] if genres else genres
    if genre and len(genres) > 1:
        genre = ", ".join(genres)
    score = data.get("averageScore")
    air_on = None
    if data["nextAiringEpisode"]:
        nextAir = data["nextAiringEpisode"]["airingAt"]
        episode = data["nextAiringEpisode"]["episode"]
        air_on = make_it_rw(nextAir, True)

    title_ = english or romaji
    out = f"[{c_flag}] **{native}** \n   (`{title_}`)"
    out += f"\n\n**ID:** `{mid}`"
    out += f"\n**Status:** `{status}`\n"
    out += f"**Source:** `{source}`\n"
    out += f"**Score:** `{score}`\n"
    out += f"**Genres:** `{genre}`\n"
    if air_on:
        out += f"**Airing Episode:** `[{episode}/{episodes}]`\n"
        out += f"\n`{air_on}`"
    return coverImg, out
