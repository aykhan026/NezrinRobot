from SaitamaRobot.modules.helper_funcs.telethn.chatstatus import (
    can_delete_messages, user_is_admin)
from SaitamaRobot import telethn
import time
from telethon import events


@telethn.on(events.NewMessage(pattern="^[!/]purge$"))
async def purge_messages(event):
    start = time.perf_counter()
    if event.from_id is None:
        return

    if not await user_is_admin(
            user_id=event.sender_id, message=event) and event.from_id not in [
                1087968824
            ]:
        await event.reply("Yalnız adminlər bu əmri işlədə bilər")
        return

    if not await can_delete_messages(message=event):
        await event.reply("Mesajları silmək uğursuz oldu")
        return

    reply_msg = await event.get_reply_message()
    if not reply_msg:
        await event.reply(
            "Silməyə başlayacağım mesaja yanıt ver.")
        return
    messages = []
    message_id = reply_msg.id
    delete_to = event.message.id

    messages.append(event.reply_to_msg_id)
    for msg_id in range(message_id, delete_to + 1):
        messages.append(msg_id)
        if len(messages) == 100:
            await event.client.delete_messages(event.chat_id, messages)
            messages = []

    await event.client.delete_messages(event.chat_id, messages)
    time_ = time.perf_counter() - start
    text = f"Təmizləmə prosesi {time_:0.2f} saniyədə tamamlandı"
    await event.respond(text, parse_mode='markdown')


@telethn.on(events.NewMessage(pattern="^[!/]sil$"))
async def delete_messages(event):
    if event.from_id is None:
        return

    if not await user_is_admin(
            user_id=event.sender_id, message=event) and event.from_id not in [
                1087968824
            ]:
        await event.reply("Yalnız adminlər bu əmri işlədə bilər")
        return

    if not await can_delete_messages(message=event):
        await event.reply("Silmə prosesi uğursuz oldu")
        return

    message = await event.get_reply_message()
    if not message:
        await event.reply("Sən nəyi silmək istəyirsənki?")
        return
    chat = await event.get_input_chat()
    del_message = [message, event.message]
    await event.client.delete_messages(chat, del_message)


__help__ = """
*Sadəcə adminlər:*
 - /sil: yanıtlanan mesajı silir
 - /purge: yanıtlanan mesajdan aşağıdakı bütün mesajları silir.
 - /purge <x ədədi>: yanıtlanan mesajdan aşağıdakı x sayda mesajı silir.
"""

__mod_name__ = "Silmək"
