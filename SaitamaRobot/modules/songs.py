import os

import aiohttp
from pyrogram import filters
from pytube import YouTube
from youtubesearchpython import VideosSearch

from SaitamaRobot import LOGGER, pbot
from SaitamaRobot.utils.ut import get_arg


def yt_search(song):
    videosSearch = VideosSearch(song, limit=1)
    result = videosSearch.result()
    if not result:
        return False
    else:
        video_id = result["result"][0]["id"]
        url = f"https://youtu.be/{video_id}"
        return url


class AioHttp:
    @staticmethod
    async def get_json(link):
        async with aiohttp.ClientSession() as session:
            async with session.get(link) as resp:
                return await resp.json()

    @staticmethod
    async def get_text(link):
        async with aiohttp.ClientSession() as session:
            async with session.get(link) as resp:
                return await resp.text()

    @staticmethod
    async def get_raw(link):
        async with aiohttp.ClientSession() as session:
            async with session.get(link) as resp:
                return await resp.read()


@pbot.on_message(filters.command("song"))
async def song(client, message):
    message.chat.id
    user_id = message.from_user["id"]
    args = get_arg(message) + " " + "song"
    if args.startswith(" "):
        await message.reply("Axtarmaq üçün heçnə yazmadın😐\nNümunə:\n/song Okaber - Taboo")
        return ""
    status = await message.reply("🥳Axtarıram...")
    video_link = yt_search(args)
    if not video_link:
        await status.edit("Bu mahnını tapa bilmədim 😕")
        return ""
    yt = YouTube(video_link)
    audio = yt.streams.filter(only_audio=True).first()
    try:
        download = audio.download(filename=f"{str(user_id)}")
    except Exception as ex:
        await status.edit("Mahnını yükləyərkən xəta baş verdi 😕")
        LOGGER.error(ex)
        return ""
    os.rename(download, f"{str(user_id)}.mp3")
    await pbot.send_chat_action(message.chat.id, "upload_audio")
    await pbot.send_audio(
        chat_id=message.chat.id,
        audio=f"{str(user_id)}.mp3",
        duration=int(yt.length),
        title=str(yt.title),
        performer=str(yt.author),
        reply_to_message_id=message.message_id,
    )
    await status.delete()
    os.remove(f"{str(user_id)}.mp3")


__help__ = """
 *Mahnı adı və yaxudda Musiqiçi adı yaza bilərsiniz. *

 ✪ /song <musiqi adı>*:* Musiqini YouTubedən yükləyəcəm
 ✪ /video <video, klip adı>*:* uploads the video song in it's best quality available
 ✪ /lyrics <song>*:* returns the lyrics of that song.

"""

__mod_name__ = "🎧Musiqi"
