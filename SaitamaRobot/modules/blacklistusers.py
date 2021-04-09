# Module to blacklist users and prevent them from using commands by @TheRealPhoenix
import html
import SaitamaRobot.modules.sql.blacklistusers_sql as sql
from SaitamaRobot import (DEV_USERS, OWNER_ID, DRAGONS, DEMONS, TIGERS, WOLVES,
                          dispatcher)
from SaitamaRobot.modules.helper_funcs.chat_status import dev_plus
from SaitamaRobot.modules.helper_funcs.extraction import (extract_user,
                                                          extract_user_and_text)
from SaitamaRobot.modules.log_channel import gloggable
from telegram import ParseMode, Update
from telegram.error import BadRequest
from telegram.ext import CallbackContext, CommandHandler, run_async
from telegram.utils.helpers import mention_html

BLACKLISTWHITELIST = [OWNER_ID] + DEV_USERS + DRAGONS + WOLVES + DEMONS
BLABLEUSERS = [OWNER_ID] + DEV_USERS


@run_async
@dev_plus
@gloggable
def bl_user(update: Update, context: CallbackContext) -> str:
    message = update.effective_message
    user = update.effective_user
    bot, args = context.bot, context.args
    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("Bunun bir istifadəçi olduğuna şübhə ilə yanaşıram.")
        return ""

    if user_id == bot.id:
        message.reply_text(
            "Özümə məhəl qoymuramsa, işimi necə görməliyəm?")
        return ""

    if user_id in BLACKLISTWHITELIST:
        message.reply_text("Yox! Bu şəxsə bunu etməyəcəm.")
        return ""

    try:
        target_user = bot.get_chat(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("İstifadəçini tapa bilmədim.")
            return ""
        else:
            raise

    sql.blacklist_user(user_id, reason)
    message.reply_text("Artıq bu istifadəçinin varlığına məhəl qoymayacağam!")
    log_message = (
        f"#BLACKLIST\n"
        f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
        f"<b>User:</b> {mention_html(target_user.id, html.escape(target_user.first_name))}"
    )
    if reason:
        log_message += f"\n<b>Səbəb:</b> {reason}"

    return log_message


@run_async
@dev_plus
@gloggable
def unbl_user(update: Update, context: CallbackContext) -> str:
    message = update.effective_message
    user = update.effective_user
    bot, args = context.bot, context.args
    user_id = extract_user(message, args)

    if not user_id:
        message.reply_text("Bunun bir istifadəçi olduğuna şübhə ilə yanaşıram.")
        return ""

    if user_id == bot.id:
        message.reply_text("hmm deməli özümü blacklist-dən çıxardım. Nə vaxt blacklist-də oldumki?😐")
        return ""

    try:
        target_user = bot.get_chat(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("İstifadəçini tapa bilmədim.")
            return ""
        else:
            raise

    if sql.is_user_blacklisted(user_id):

        sql.unblacklist_user(user_id)
        message.reply_text("Yaxşı artıq məndən istifadə edə bilər😏")
        log_message = (
            f"#UNBLACKLIST\n"
            f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
            f"<b>User:</b> {mention_html(target_user.id, html.escape(target_user.first_name))}"
        )

        return log_message

    else:
        message.reply_text("Onsuzda onları heç görməzdən gəlmirəm!")
        return ""


@run_async
@dev_plus
def bl_users(update: Update, context: CallbackContext):
    users = []
    bot = context.bot
    for each_user in sql.BLACKLIST_USERS:
        user = bot.get_chat(each_user)
        reason = sql.get_reason(each_user)

        if reason:
            users.append(
                f"• {mention_html(user.id, html.escape(user.first_name))} :- {reason}"
            )
        else:
            users.append(
                f"• {mention_html(user.id, html.escape(user.first_name))}")

    message = "<b>Qara Siyahıdakı istifadəçilər</b>\n"
    if not users:
        message += "Qara Siyahıda heç kim yoxdur."
    else:
        message += '\n'.join(users)

    update.effective_message.reply_text(message, parse_mode=ParseMode.HTML)


def __user_info__(user_id):
    is_blacklisted = sql.is_user_blacklisted(user_id)

    text = "Qara Siyahıdadır: <b>{}</b>"
    if user_id in [777000, 1087968824]:
        return ""
    if user_id == dispatcher.bot.id:
        return ""
    if int(user_id) in DRAGONS + TIGERS + WOLVES:
        return ""
    if is_blacklisted:
        text = text.format("Yes")
        reason = sql.get_reason(user_id)
        if reason:
            text += f"\nSəbəb: <code>{reason}</code>"
    else:
        text = text.format("Yox")

    return text


BL_HANDLER = CommandHandler("ignore", bl_user)
UNBL_HANDLER = CommandHandler("notice", unbl_user)
BLUSERS_HANDLER = CommandHandler("ignoredlist", bl_users)

dispatcher.add_handler(BL_HANDLER)
dispatcher.add_handler(UNBL_HANDLER)
dispatcher.add_handler(BLUSERS_HANDLER)

__mod_name__ = "İstifadəçi Qara Siyahı"
__handlers__ = [BL_HANDLER, UNBL_HANDLER, BLUSERS_HANDLER]
