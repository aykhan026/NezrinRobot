import html

from telegram import ParseMode, Update
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


@run_async
@connection_status
@bot_admin
@can_restrict
@user_admin
@user_can_ban
@loggable
def ban(update: Update, context: CallbackContext) -> str:
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    log_message = ""
    bot = context.bot
    args = context.args
    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("Bunun bir user olduğuna şübhə ilə yanaşıram.")
        return log_message

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("Bu şəxsi tapa bilmədim.")
            return log_message
        else:
            raise

    if user_id == bot.id:
        message.reply_text("Oh yeah, özümü banlayım, axmaq!")
        return log_message

    if is_user_ban_protected(chat, user_id, member) and user not in DEV_USERS:
        if user_id == OWNER_ID:
            message.reply_text(
                "Nə? Sən mənim sahibimi banlamağa çalışırsan?mal")
            return log_message
        elif user_id in DEV_USERS:
            message.reply_text("Bu şəxsə bunu etməyəcəm.")
            return log_message
        elif user_id in DRAGONS:
            message.reply_text(
                "Mən əjdaha userimi banlamayacam.")
            return log_message
        elif user_id in DEMONS:
            message.reply_text(
                "ooooo kimsə şeytan useri banlamağa çalışır."
            )
            return log_message
        elif user_id in TIGERS:
            message.reply_text(
                "Və pələng userimizi banlmağa çalışan bir mal."
            )
            return log_message
        elif user_id in WOLVES:
            message.reply_text("Canavar userlərimiz banlana bilmir! Çünki onlar canavardı🐺")
            return log_message
        else:
            message.reply_text("Bu istifadəçinin banlanmağa qarşı güclü müqaviməti var.")
            return log_message

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#BANNED\n"
        f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
        f"<b>User:</b> {mention_html(member.user.id, html.escape(member.user.first_name))}"
    )
    if reason:
        log += "\n<b>Səbəb:</b> {}".format(reason)

    try:
        chat.kick_member(user_id)
        # bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        reply = (
            f"<code>❕</code><b>Ban</b>\n"
            f"<code> </code><b>•  User:</b> {mention_html(member.user.id, html.escape(member.user.first_name))}"
        )
        if reason:
            reply += f"\n<code> </code><b>•  Səbəb:</b> \n{html.escape(reason)}"
        bot.sendMessage(chat.id, reply, parse_mode=ParseMode.HTML, quote=False)
        return log

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text('Banlandı!', quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR banning user %s in chat %s (%s) due to %s",
                             user_id, chat.title, chat.id, excp.message)
            message.reply_text("Uhm...nədənsə bu işləmədi...")

    return log_message


@run_async
@connection_status
@bot_admin
@can_restrict
@user_admin
@user_can_ban
@loggable
def temp_ban(update: Update, context: CallbackContext) -> str:
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    log_message = ""
    bot, args = context.bot, context.args
    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("Bunun bir istifadəçi olduğuna şübhə ilə yanaşıram.")
        return log_message

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("Bu istifadəçini taba bilmədim.")
            return log_message
        else:
            raise

    if user_id == bot.id:
        message.reply_text("Nə? Sən dəlisən?, mən özümü banlamıyacam!")
        return log_message

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("Bunu edə bilmərsən.")
        return log_message

    if not reason:
        message.reply_text("Bu istifadəçini banlamaq üçün bir zaman vermədiniz!")
        return log_message

    split_reason = reason.split(None, 1)

    time_val = split_reason[0].lower()
    if len(split_reason) > 1:
        reason = split_reason[1]
    else:
        reason = ""

    bantime = extract_time(message, time_val)

    if not bantime:
        return log_message

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        "#TEMP BANNED\n"
        f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
        f"<b>User:</b> {mention_html(member.user.id, html.escape(member.user.first_name))}\n"
        f"<b>Time:</b> {time_val}")
    if reason:
        log += "\n<b>Səbəb:</b> {}".format(reason)

    try:
        chat.kick_member(user_id, until_date=bantime)
        bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        bot.sendMessage(
            chat.id,
            f"Banlandı! {mention_html(member.user.id, html.escape(member.user.first_name))} "
            f"{time_val} müddətlik banlandı.",
            parse_mode=ParseMode.HTML)
        return log

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text(
                f"Banlandı! İstifadəçi {time_val} müddətlik banlandı.", quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR banning user %s in chat %s (%s) due to %s",
                             user_id, chat.title, chat.id, excp.message)
            message.reply_text("pf. Bu istifadəçini banlaya bilmirəm.")

    return log_message


@run_async
@connection_status
@bot_admin
@can_restrict
@user_admin
@user_can_ban
@loggable
def punch(update: Update, context: CallbackContext) -> str:
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    log_message = ""
    bot, args = context.bot, context.args
    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("Bunun bir istifadəçi olduğuna şübhə ilə yanaşıram.")
        return log_message

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("İstifadəçini tapa bilmədim.")
            return log_message
        else:
            raise

    if user_id == bot.id:
        message.reply_text("Yeahhh mən özümə bunu etməyəcəm.")
        return log_message

    if is_user_ban_protected(chat, user_id):
        message.reply_text("ehh bu istifadəçini atmaq istəyərdim amma indi ata bilmirəm....")
        return log_message

    res = chat.unban_member(user_id)  # unban on current user = kick
    if res:
        # bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        bot.sendMessage(
            chat.id,
            f"{mention_html(member.user.id, html.escape(member.user.first_name))} qrupdan atıldı.",
            parse_mode=ParseMode.HTML)
        log = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#KICKED\n"
            f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
            f"<b>User:</b> {mention_html(member.user.id, html.escape(member.user.first_name))}"
        )
        if reason:
            log += f"\n<b>Səbəb:</b> {reason}"

        return log

    else:
        message.reply_text("pf bu istifadəçini ata bilmirəm.")

    return log_message


@run_async
@bot_admin
@can_restrict
def punchme(update: Update, context: CallbackContext):
    user_id = update.effective_message.from_user.id
    if is_user_admin(update.effective_chat, user_id):
        update.effective_message.reply_text(
            "Nə? Sən bir adminsən və mən səni qrupdan atmayacam.")
        return

    res = update.effective_chat.unban_member(
        user_id)  # unban on current user = kick
    if res:
        update.effective_message.reply_text("*təbriklər, qrupdan atılırsan*")
    else:
        update.effective_message.reply_text("Huh? bunu bacarmıram :/")


@run_async
@connection_status
@bot_admin
@can_restrict
@user_admin
@user_can_ban
@loggable
def unban(update: Update, context: CallbackContext) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    log_message = ""
    bot, args = context.bot, context.args
    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("Bunun bir istifadəçi olduğuna şübhə ilə yanaşıram.")
        return log_message

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("Bu istifadəçini tapa bilmədim.")
            return log_message
        else:
            raise

    if user_id == bot.id:
        message.reply_text("Mən öz banımı aça bilmərəm çünki mən burdayam və banlı deyiləm...?")
        return log_message

    if is_user_in_chat(chat, user_id):
        message.reply_text("Bu istifadəçinin burada olduğundan əminsən??")
        return log_message

    chat.unban_member(user_id)
    message.reply_text("Yep, istifadəçi artıq qoşula bilər!")

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#UNBANNED\n"
        f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
        f"<b>User:</b> {mention_html(member.user.id, html.escape(member.user.first_name))}"
    )
    if reason:
        log += f"\n<b>Səbəb:</b> {reason}"

    return log


@run_async
@connection_status
@bot_admin
@can_restrict
@gloggable
def selfunban(context: CallbackContext, update: Update) -> str:
    message = update.effective_message
    user = update.effective_user
    bot, args = context.bot, context.args
    if user.id not in DRAGONS or user.id not in TIGERS:
        return

    try:
        chat_id = int(args[0])
    except:
        message.reply_text("Mənə düzgün qrup ID-si ver.")
        return

    chat = bot.getChat(chat_id)

    try:
        member = chat.get_member(user.id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("Bu istifadəçini tapa bilmədim.")
            return
        else:
            raise

    if is_user_in_chat(chat, user.id):
        message.reply_text("Sən dəqiq həmin qrupda varsan??")
        return

    chat.unban_member(user.id)
    message.reply_text("Yep, Sənin banıvı açdım.")

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#UNBANNED\n"
        f"<b>User:</b> {mention_html(member.user.id, html.escape(member.user.first_name))}"
    )

    return log


__help__ = """
 • `/kickme`*:* bu əmri işlədən istifadəçini qrupdan atır

*Sadəcə adminlər:*
 • `/ban <istifadəçi>`*:* istifadəçini banlayır.
 • `/tban <istifadəçi> x(m/h/d)`*:* istifadəçini `x` müddətlik banlayır. `m` = `dəqiqə`, `h` = `saat`, `d` = `gün`.
 • `/unban <istifadəçi>`*:* istifadəçinin banını açır.
 • `/kick <istifadəçi>`*:* istifadəçini qrupdan atır.
"""

BAN_HANDLER = CommandHandler("ban", ban)
TEMPBAN_HANDLER = CommandHandler(["tban"], temp_ban)
PUNCH_HANDLER = CommandHandler("kick", punch)
UNBAN_HANDLER = CommandHandler("unban", unban)
ROAR_HANDLER = CommandHandler("roar", selfunban)
PUNCHME_HANDLER = DisableAbleCommandHandler(
    "kickme", punchme, filters=Filters.group)

dispatcher.add_handler(BAN_HANDLER)
dispatcher.add_handler(TEMPBAN_HANDLER)
dispatcher.add_handler(PUNCH_HANDLER)
dispatcher.add_handler(UNBAN_HANDLER)
dispatcher.add_handler(ROAR_HANDLER)
dispatcher.add_handler(PUNCHME_HANDLER)

__mod_name__ = "Ban"
__handlers__ = [
    BAN_HANDLER, TEMPBAN_HANDLER, PUNCH_HANDLER, UNBAN_HANDLER, ROAR_HANDLER,
    PUNCHME_HANDLER
]
