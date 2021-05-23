from pyrogram import filters

from SaitamaRobot.pyrogramee.pluginshelper import admins_only, get_text
from SaitamaRobot import pbot
from SaitamaRobot.modules.helper_funcs.chat_status import (
    can_delete,
    is_user_admin,
    user_not_admin,
    is_bot_admin,
    user_admin,
)


@pbot.on_message(filters.command('all', ['!', '@', '/']) & ~filters.edited & ~filters.bot)
@user_admin
async def tagall(client, message):
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
@user_admin
async def tagall(client, message):
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
