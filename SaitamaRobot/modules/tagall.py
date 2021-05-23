# Bu plugin aykhan_s tərəfindən yaradılıb !
# Kopyalamaq dəyişdirməy qadağandır
# t.me/aykhan_s | t.me/RoBotlarimTg


import html
from pyrogram import filters

from SaitamaRobot.pyrogramee.pluginshelper import admins_only, get_text
from SaitamaRobot import pbot
from telegram import ParseMode, Update #aykhan
from telegram.error import BadRequest
from telegram.ext import CallbackContext, CommandHandler, Filters, run_async
from telegram.utils.helpers import mention_html

from SaitamaRobot import (DEV_USERS, LOGGER, OWNER_ID, DRAGONS, DEMONS, TIGERS,
                          WOLVES, dispatcher)
from SaitamaRobot.modules.disable import DisableAbleCommandHandler
from SaitamaRobot.modules.helper_funcs.chat_status import (
    bot_admin, can_restrict, connection_status, is_user_admin,
    is_user_ban_protected, is_user_in_chat, user_admin, user_can_ban)
from SaitamaRobot.modules.helper_funcs.extraction import extract_user_and_text
from SaitamaRobot.modules.helper_funcs.string_handling import extract_time
from SaitamaRobot.modules.log_channel import gloggable, loggable



@pbot.on_message(filters.command('all', ['!', '@', '/']) & ~filters.edited & ~filters.bot)
@run_async
@bot_admin
@can_restrict
@user_admin
@user_can_ban
@loggable
async def all(client, message):
    await message.reply("🥳 Qarışıq Tağ Prosesi Başladı...")
    chat_id = message.chat.id
    string = ""
    limit = 1
    icm = client.iter_chat_members(message.chat.id)
    async for member in icm:
        tag = member.user.mention
        if limit <= 5:
            if tag != None:
                string += f"🥳 {tag}\n"
            else:
                string += f"{member.user.mention}\n"
            limit += 1
        else:
            await client.send_message(chat_id, text=string)
            limit = 1
            string = ""


@pbot.on_message(filters.command('tag', ['!', '@', '/']) & ~filters.edited & ~filters.bot)
@run_async
@bot_admin
@can_restrict
@user_admin
@user_can_ban
@loggable
async def tag(client, message):
    await message.reply("🥳 Tək-Tək Tağ Prosesi Başladı...")
    chat_id = message.chat.id
    string = ""
    limit = 1
    icm = client.iter_chat_members(message.chat.id)
    async for member in icm:
        tag = member.user.mention
        if limit <= 1:
            if tag != None:
                string += f"❤️ {tag} Bayaqdan səni gözləyirəm gəl qrupa 🥰\n"
            else:
                string += f"{member.user.mention}\n"
            limit += 1
        else:
            await client.send_message(chat_id, text=string)
            limit = 1
            string = ""
            


__mod_name__ = "🖇️Tağ"
__help__ = """
✅ *Yalnız adminlər* tərəfindən istifadə oluna bilər !
✅ Bu əmrlər *@, /, !* ilə işlədilir
- `@all` : Son görülməsi yaxın olan hərkəsi qarışıq tağ edər
- `@tag` : Son görülməsi yaxın olan hər kəsi tək tək tağ edər
"""
