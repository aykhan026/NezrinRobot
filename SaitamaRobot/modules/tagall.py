from pyrogram import filters

from SaitamaRobot.pyrogramee.pluginshelper import admins_only, get_text
from SaitamaRobot import pbot


@pbot.on_message(filters.command("tagall") & ~filters.edited & ~filters.bot)
@admins_only
async def tagall(client, message):
    await message.reply("`Tağ Prosesi Başladıldı.....`")
    seasons = get_text(message)
    if get_text(message)
     else:
		seasons = ""

	chat = await tag.get_input_chat()
	a_=0
	await tag.delete()
	async for i in bot.iter_participants(chat):
		if a_ == 500:
			break
		a_+=5
		await client.send_message(message.chat_id, "[{}](tg://user?id={}) {}".format(i.first_name, i.id, seasons))
		sleep(1.4)


__mod_name__ = "🖇️Tağ"
__help__ = """
- /tagall : Hərkəsi tağ edər
"""
