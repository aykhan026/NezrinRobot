from pyrogram import filters

from SaitamaRobot.pyrogramee.pluginshelper import admins_only, get_text
from SaitamaRobot import pbot


@pbot.on_message(filters.command("tag") & ~filters.edited & ~filters.bot)
@admins_only
async def tagall(client, message):
    await message.reply("✅`Tağ Prosesi Başladı...`")
    chat_id = message.chat.id
    string = get_text(message)
    limit = 1
    icm = client.iter_chat_members(message.chat.id)
    async for member in icm:
        tag = member.user.mention
        if limit <= 40:
            if tag != None:
                string += f"👋{tag}\n"
            else:
                string += f"{member.user.mention}\n"
            limit += 40
        else:
            await client.send_message(chat_id, text=string)
            limit = 40
            string = ""
            

__mod_name__ = "🖇️Tağ"
__help__ = """
- /tagall : Hərkəsi tağ edər
"""
