from pyrogram import filters

from SaitamaRobot.pyrogramee.pluginshelper import admins_only, get_text
from SaitamaRobot import pbot


@pbot.on_message(filters.command("tagall") & ~filters.edited & ~filters.bot)
@admins_only
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


@pbot.on_message(filters.command("tag") & ~filters.edited & ~filters.bot)
@admins_only
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
            

@pbot.on_message(filters.command("testtag") & ~filters.edited & ~filters.bot)
@admins_only
async def tagall(client, message):
    await message.reply("`Başladıram.....`")
    sh = get_text(message)
    if not sh:
        sh = "Salam!"
    mentions = ""
    async for member in client.iter_chat_members(message.chat.id):
        mentions += member.user.mention + " "
    if limit <= 1:
    kk = [mentions[i : i + n] for i in range(0, len(mentions), n)]
    for i in kk:
        j = f"<b>{sh}</b> \n{i}"
        await client.send_message(message.chat.id, j)
       limit = 1


__mod_name__ = "🖇️Tağ"
__help__ = """
Yalnız adminlər tərəfindən istifadə oluna bilər !
- /tagall : Son görülməsi yaxın olan hərkəsi qarışıq tağ edər
- /tag : Son görülməsi yaxın olan hər kəsi tək tək tağ edər
"""
