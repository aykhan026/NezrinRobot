import secrets
import string
import aiohttp
from pyrogram import filters
from cryptography.fernet import Fernet
from SaitamaRobot import pbot
from SaitamaRobot.utils import random_line


@pbot.on_message(filters.command("sehid") & ~filters.edited)
async def commit(_, message):
    await message.reply_text((await random_line('AykhanPro/txt/sehid.txt')))

__mod_name__ = "🇦🇿Şəhidlər"
__help__ = """

🇦🇿*Şəhidlər*
 - `/sehid` - Bu əmr vaistəsiylə sizə *Şəhid* adları göndərəcəm
*Allah bütün Şəhidimizə rəhmət eləsin*
Qazilərimizə şəfa versin 
Başın sağolsun Azərbaycan 🇦🇿
Bazada *2881* Şəhid adı mövcuddur

"""
