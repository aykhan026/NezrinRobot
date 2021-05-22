from pyrogram import filters

from SaitamaRobot.pyrogramee.pluginshelper import admins_only, get_text
from SaitamaRobot import pbot


@pbot.on_message(filters.command("tagall") & ~filters.edited & ~filters.bot)
@admins_only
async def tagall(client, message):
    await message.reply("♻️`Tağ Prosesi Başladıldı.....`")
    sh = get_text(message)
    if not sh:
        sh = "Darıxmışam sizinçün 🤭"
    mentions = ""
    async for member in client.iter_chat_members(message.chat.id):
        mentions += member.user.mention + " "
    n = 4096
    kk = [mentions[i : i + n] for i in range(0, len(mentions), n)]
    for i in kk:
        j = f"<b>{sh}</b> \n{i}"
        await client.send_message(message.chat.id, j, parse_mode="html")


__mod_name__ = "🖇️Tağ"
__help__ = """
- /tagall : Hərkəsi tağ edər
- /tagall <mesaj> : Hərkəsi tağ edər və yazdığınız mesaj tağ da görsənər
"""
