import html
import re
from typing import Optional

import telegram
from SaitamaRobot import TIGERS, WOLVES, dispatcher
from SaitamaRobot.modules.disable import DisableAbleCommandHandler
from SaitamaRobot.modules.helper_funcs.chat_status import (bot_admin,
                                                           can_restrict,
                                                           is_user_admin,
                                                           user_admin,
                                                           user_admin_no_reply)
from SaitamaRobot.modules.helper_funcs.extraction import (extract_text,
                                                          extract_user,
                                                          extract_user_and_text)
from SaitamaRobot.modules.helper_funcs.filters import CustomFilters
from SaitamaRobot.modules.helper_funcs.misc import split_message
from SaitamaRobot.modules.helper_funcs.string_handling import split_quotes
from SaitamaRobot.modules.log_channel import loggable
from SaitamaRobot.modules.sql import warns_sql as sql
from telegram import (CallbackQuery, Chat, InlineKeyboardButton,
                      InlineKeyboardMarkup, Message, ParseMode, Update, User)
from telegram.error import BadRequest
from telegram.ext import (CallbackContext, CallbackQueryHandler, CommandHandler,
                          DispatcherHandlerStop, Filters, MessageHandler,
                          run_async)
from telegram.utils.helpers import mention_html

WARN_HANDLER_GROUP = 9
CURRENT_WARNING_FILTER_STRING = "<b>Current warning filters in this chat:</b>\n"


# Not async
def warn(user: User,
         chat: Chat,
         reason: str,
         message: Message,
         warner: User = None) -> str:
    if is_user_admin(chat, user.id):
        # message.reply_text("Damn admins, They are too far to be One Punched!")
        return

    if user.id in TIGERS:
        if warner:
            message.reply_text("Pələng istifadəçilər bilməz.")
        else:
            message.reply_text(
                "Pələng istifadəçilərə xəbərdarlıq verə bilmərəm!"
            )
        return

    if user.id in WOLVES:
        if warner:
            message.reply_text("Canavar istifadəçilərin xəbərdarlığa qarşı immuniteti var.")
        else:
            message.reply_text(
                "Canavar istifadəçilərin xəbərdarlığa qarşı immuniteti var."
            )
        return

    if warner:
        warner_tag = mention_html(warner.id, warner.first_name)
    else:
        warner_tag = "Xəbərdarlıq filtri."

    limit, soft_warn = sql.get_warn_setting(chat.id)
    num_warns, reasons = sql.warn_user(user.id, chat.id, reason)
    if num_warns >= limit:
        sql.reset_warns(user.id, chat.id)
        if soft_warn:  # punch
            chat.unban_member(user.id)
            reply = (
                f"<code>❕</code><b>Qrupdan atıldı</b>\n"
                f"<code> </code><b>•  İstifadəçi:</b> {mention_html(user.id, user.first_name)}\n"
                f"<code> </code><b>•  Limit:</b> {limit}")

        else:  # ban
            chat.kick_member(user.id)
            reply = (
                f"<code>❕</code><b>Banlandı</b>\n"
                f"<code> </code><b>•  İstifadəçi:</b> {mention_html(user.id, user.first_name)}\n"
                f"<code> </code><b>•  Limit:</b> {limit}")

        for warn_reason in reasons:
            reply += f"\n - {html.escape(warn_reason)}"

        message.bot.send_sticker(chat.id, BAN_STICKER)  # Saitama's sticker
        keyboard = None
        log_reason = (f"<b>{html.escape(chat.title)}:</b>\n"
                      f"#WARN_BAN\n"
                      f"<b>Admin:</b> {warner_tag}\n"
                      f"<b>User:</b> {mention_html(user.id, user.first_name)}\n"
                      f"<b>Reason:</b> {reason}\n"
                      f"<b>Counts:</b> <code>{num_warns}/{limit}</code>")

    else:
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton(
                "🔘 Xəbərdarlığı sil", callback_data="rm_warn({})".format(user.id))
        ]])

        reply = (
            f"<code>❕</code><b>Xəbərdarlıq</b>\n"
            f"<code> </code><b>•  İstifadəçi:</b> {mention_html(user.id, user.first_name)}\n"
            f"<code> </code><b>•  Say/limit:</b> {num_warns}/{limit}")
        if reason:
            reply += f"\n<code> </code><b>•  Səbəb:</b> {html.escape(reason)}"

        log_reason = (f"<b>{html.escape(chat.title)}:</b>\n"
                      f"#WARN\n"
                      f"<b>Admin:</b> {warner_tag}\n"
                      f"<b>User:</b> {mention_html(user.id, user.first_name)}\n"
                      f"<b>Reason:</b> {reason}\n"
                      f"<b>Counts:</b> <code>{num_warns}/{limit}</code>")

    try:
        message.reply_text(
            reply, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text(
                reply,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML,
                quote=False)
        else:
            raise
    return log_reason


@run_async
@user_admin_no_reply
@bot_admin
@loggable
def button(update: Update, context: CallbackContext) -> str:
    query: Optional[CallbackQuery] = update.callback_query
    user: Optional[User] = update.effective_user
    match = re.match(r"rm_warn\((.+?)\)", query.data)
    if match:
        user_id = match.group(1)
        chat: Optional[Chat] = update.effective_chat
        res = sql.remove_warn(user_id, chat.id)
        if res:
            update.effective_message.edit_text(
                "Xəbərdarlıq {} tərəfindən silindi.".format(
                    mention_html(user.id, user.first_name)),
                parse_mode=ParseMode.HTML)
            user_member = chat.get_member(user_id)
            return (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#UNWARN\n"
                f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
                f"<b>User:</b> {mention_html(user_member.user.id, user_member.user.first_name)}"
            )
        else:
            update.effective_message.edit_text(
                "Bu istifadəçinin xəbərdarlığı yoxdur.", parse_mode=ParseMode.HTML)

    return ""


@run_async
@user_admin
@can_restrict
@loggable
def warn_user(update: Update, context: CallbackContext) -> str:
    args = context.args
    message: Optional[Message] = update.effective_message
    chat: Optional[Chat] = update.effective_chat
    warner: Optional[User] = update.effective_user

    user_id, reason = extract_user_and_text(message, args)

    if user_id:
        if message.reply_to_message and message.reply_to_message.from_user.id == user_id:
            return warn(message.reply_to_message.from_user, chat, reason,
                        message.reply_to_message, warner)
        else:
            return warn(
                chat.get_member(user_id).user, chat, reason, message, warner)
    else:
        message.reply_text("Görünür ki yanlış istifadəçi ID-sidir.")
    return ""


@run_async
@user_admin
@bot_admin
@loggable
def reset_warns(update: Update, context: CallbackContext) -> str:
    args = context.args
    message: Optional[Message] = update.effective_message
    chat: Optional[Chat] = update.effective_chat
    user: Optional[User] = update.effective_user

    user_id = extract_user(message, args)

    if user_id:
        sql.reset_warns(user_id, chat.id)
        message.reply_text("Warns have been reset!")
        warned = chat.get_member(user_id).user
        return (f"<b>{html.escape(chat.title)}:</b>\n"
                f"#RESETWARNS\n"
                f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
                f"<b>User:</b> {mention_html(warned.id, warned.first_name)}")
    else:
        message.reply_text("Heç bir istifadəçi təyin edilməyib!")
    return ""


@run_async
def warns(update: Update, context: CallbackContext):
    args = context.args
    message: Optional[Message] = update.effective_message
    chat: Optional[Chat] = update.effective_chat
    user_id = extract_user(message, args) or update.effective_user.id
    result = sql.get_warns(user_id, chat.id)

    if result and result[0] != 0:
        num_warns, reasons = result
        limit, soft_warn = sql.get_warn_setting(chat.id)

        if reasons:
            text = f"Bu istifadəçinin {num_warns}/{limit} xəbərdarlığı var, səbəblər aşağıdadır:"
            for reason in reasons:
                text += f"\n • {reason}"

            msgs = split_message(text)
            for msg in msgs:
                update.effective_message.reply_text(msg)
        else:
            update.effective_message.reply_text(
                f"Bu istifadəçinin {num_warns}/{limit} xbərdarlığı var, amma bir səbəb verilməyib."
            )
    else:
        update.effective_message.reply_text("Bu istifadəçinin xəbərdarlığı yoxdur!")


# Dispatcher handler stop - do not async
@user_admin
def add_warn_filter(update: Update, context: CallbackContext):
    chat: Optional[Chat] = update.effective_chat
    msg: Optional[Message] = update.effective_message

    args = msg.text.split(
        None,
        1)  # use python's maxsplit to separate Cmd, keyword, and reply_text

    if len(args) < 2:
        return

    extracted = split_quotes(args[1])

    if len(extracted) >= 2:
        # set trigger -> lower, so as to avoid adding duplicate filters with different cases
        keyword = extracted[0].lower()
        content = extracted[1]

    else:
        return

    # Note: perhaps handlers can be removed somehow using sql.get_chat_filters
    for handler in dispatcher.handlers.get(WARN_HANDLER_GROUP, []):
        if handler.filters == (keyword, chat.id):
            dispatcher.remove_handler(handler, WARN_HANDLER_GROUP)

    sql.add_warn_filter(chat.id, keyword, content)

    update.effective_message.reply_text(f"Xəbərdarlıq filtri əlavə olundu. '{keyword}'!")
    raise DispatcherHandlerStop


@user_admin
def remove_warn_filter(update: Update, context: CallbackContext):
    chat: Optional[Chat] = update.effective_chat
    msg: Optional[Message] = update.effective_message

    args = msg.text.split(
        None,
        1)  # use python's maxsplit to separate Cmd, keyword, and reply_text

    if len(args) < 2:
        return

    extracted = split_quotes(args[1])

    if len(extracted) < 1:
        return

    to_remove = extracted[0]

    chat_filters = sql.get_chat_warn_triggers(chat.id)

    if not chat_filters:
        msg.reply_text("Burada aktiv xəbərdarlıq filtri yoxdur!")
        return

    for filt in chat_filters:
        if filt == to_remove:
            sql.remove_warn_filter(chat.id, to_remove)
            msg.reply_text("Okay, I'll stop warning people for that.")
            raise DispatcherHandlerStop

    msg.reply_text(
        "Belə bir xəbərdarlıq filtri yoxdur - /warnlist yazaraq aktiv xəbərdarlıq filtrlərinə baxa bilərsiniz."
    )


@run_async
def list_warn_filters(update: Update, context: CallbackContext):
    chat: Optional[Chat] = update.effective_chat
    all_handlers = sql.get_chat_warn_triggers(chat.id)

    if not all_handlers:
        update.effective_message.reply_text(
            "Burada aktiv xəbərdarlıq filtri yoxdur!")
        return

    filter_list = CURRENT_WARNING_FILTER_STRING
    for keyword in all_handlers:
        entry = f" - {html.escape(keyword)}\n"
        if len(entry) + len(filter_list) > telegram.MAX_MESSAGE_LENGTH:
            update.effective_message.reply_text(
                filter_list, parse_mode=ParseMode.HTML)
            filter_list = entry
        else:
            filter_list += entry

    if filter_list != CURRENT_WARNING_FILTER_STRING:
        update.effective_message.reply_text(
            filter_list, parse_mode=ParseMode.HTML)


@run_async
@loggable
def reply_filter(update: Update, context: CallbackContext) -> str:
    chat: Optional[Chat] = update.effective_chat
    message: Optional[Message] = update.effective_message
    user: Optional[User] = update.effective_user

    if not user:  #Ignore channel
        return

    if user.id == 777000:
        return

    chat_warn_filters = sql.get_chat_warn_triggers(chat.id)
    to_match = extract_text(message)
    if not to_match:
        return ""

    for keyword in chat_warn_filters:
        pattern = r"( |^|[^\w])" + re.escape(keyword) + r"( |$|[^\w])"
        if re.search(pattern, to_match, flags=re.IGNORECASE):
            user: Optional[User] = update.effective_user
            warn_filter = sql.get_warn_filter(chat.id, keyword)
            return warn(user, chat, warn_filter.reply, message)
    return ""


@run_async
@user_admin
@loggable
def set_warn_limit(update: Update, context: CallbackContext) -> str:
    args = context.args
    chat: Optional[Chat] = update.effective_chat
    user: Optional[User] = update.effective_user
    msg: Optional[Message] = update.effective_message

    if args:
        if args[0].isdigit():
            if int(args[0]) < 3:
                msg.reply_text("Minimum xəbərdarlıq limiti 3-dür!")
            else:
                sql.set_warn_limit(chat.id, int(args[0]))
                msg.reply_text("Yeni xəbərdarlıq limiti: {}".format(args[0]))
                return (
                    f"<b>{html.escape(chat.title)}:</b>\n"
                    f"#SET_WARN_LIMIT\n"
                    f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
                    f"Set the warn limit to <code>{args[0]}</code>")
        else:
            msg.reply_text("Mənə bir rəqəm ver!")
    else:
        limit, soft_warn = sql.get_warn_setting(chat.id)

        msg.reply_text("Hazırki xəbərdarlıq limiti {}".format(limit))
    return ""


@run_async
@user_admin
def set_warn_strength(update: Update, context: CallbackContext):
    args = context.args
    chat: Optional[Chat] = update.effective_chat
    user: Optional[User] = update.effective_user
    msg: Optional[Message] = update.effective_message

    if args:
        if args[0].lower() in ("on", "yes"):
            sql.set_warn_strength(chat.id, False)
            msg.reply_text("Xəbərdarlıq limitinə çatanlar banlanacaq!")
            return (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
                f"Has enabled strong warns. Users will be seriously punched.(banned)"
            )

        elif args[0].lower() in ("off", "no"):
            sql.set_warn_strength(chat.id, True)
            msg.reply_text(
                "Xəbərdarlıq limitinə çatanlar qrupdan atılacaq."
            )
            return (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
                f"Has disabled strong punches. I will use normal punch on users."
            )

        else:
            msg.reply_text("Mən yalnız on/yes/no/off başa düşürəm!")
    else:
        limit, soft_warn = sql.get_warn_setting(chat.id)
        if soft_warn:
            msg.reply_text(
                "Xəbərdarlıq limitinə çatanlar qrupdan atılacaq.",
                parse_mode=ParseMode.MARKDOWN)
        else:
            msg.reply_text(
                "Xəbərdarlıq limitinə çatanlar banlanacaq.",
                parse_mode=ParseMode.MARKDOWN)
    return ""


def __stats__():
    return (
        f"• {sql.num_warns()} ədəd xəbərdarlıq mövcuddur, ümumi {sql.num_warn_chats()} qrupda.\n"
        f"• {sql.num_warn_filters()} ədəd xəbərdarlıq filtri mövcuddur, ümumi {sql.num_warn_filter_chats()} qrupda."
    )


def __import_data__(chat_id, data):
    for user_id, count in data.get('warns', {}).items():
        for x in range(int(count)):
            sql.warn_user(user_id, chat_id)


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    num_warn_filters = sql.num_warn_chat_filters(chat_id)
    limit, soft_warn = sql.get_warn_setting(chat_id)
    return (
        f"Bu qrupda `{num_warn_filters}` ədəd xəbərdarlıq filtri var. "
        f"Xəbərdarlıq limiti: `{limit}` limitə çatanlar *{'qrupdan atılacaq' if soft_warn else 'banlanacaq'}*."
    )


__help__ = """
 • `/warns <istifadəçi>`*:* istifadəçinin xəbərdarlıqlarını göstərir.
 • `/warnlist`*:* xəbərdarlıq filtrlərini göstərir

*Sadəcə adminlər:*
 • `/warn <istifadəçi>`*:* istifadəçiyə xəbərdarlıq verir. 3 xəbərdarlıqdan sonra banlanır.
 • `/resetwarn <istifadəçi>`*:* istifadəçinin xəbərdarlıqlarını sıfırlayır.
 • `/addwarn <söz> <cavab>`*:* xəbərdarlıq filtri əlavə edir. Söz yerinə cümlə yazmaq üçün dırnaqlardan istifadə edin \
məsələn: `/addwarn "axmaq adminlər" Adminlərlə düzgün danış`. 
 • `/nowarn <söz>`*:* xəbərdarlıq filtrini dayandırır
 • `/warnlimit <ədəd>`*:* xəbərdarlıq limiti təyin edir
 • `/strongwarn <on/yes/off/no>`*:* Aktiv olduqda limitə çatanlar banlanır. Deaktiv olduqda limitə çatanlar qrupdan atılır.
"""

__mod_name__ = "Xəbərdarlıqlar"

WARN_HANDLER = CommandHandler("warn", warn_user, filters=Filters.group)
RESET_WARN_HANDLER = CommandHandler(["resetwarn", "resetwarns"],
                                    reset_warns,
                                    filters=Filters.group)
CALLBACK_QUERY_HANDLER = CallbackQueryHandler(button, pattern=r"rm_warn")
MYWARNS_HANDLER = DisableAbleCommandHandler(
    "warns", warns, filters=Filters.group)
ADD_WARN_HANDLER = CommandHandler(
    "addwarn", add_warn_filter, filters=Filters.group)
RM_WARN_HANDLER = CommandHandler(["nowarn", "stopwarn"],
                                 remove_warn_filter,
                                 filters=Filters.group)
LIST_WARN_HANDLER = DisableAbleCommandHandler(["warnlist", "warnfilters"],
                                              list_warn_filters,
                                              filters=Filters.group,
                                              admin_ok=True)
WARN_FILTER_HANDLER = MessageHandler(CustomFilters.has_text & Filters.group,
                                     reply_filter)
WARN_LIMIT_HANDLER = CommandHandler(
    "warnlimit", set_warn_limit, filters=Filters.group)
WARN_STRENGTH_HANDLER = CommandHandler(
    "strongwarn", set_warn_strength, filters=Filters.group)

dispatcher.add_handler(WARN_HANDLER)
dispatcher.add_handler(CALLBACK_QUERY_HANDLER)
dispatcher.add_handler(RESET_WARN_HANDLER)
dispatcher.add_handler(MYWARNS_HANDLER)
dispatcher.add_handler(ADD_WARN_HANDLER)
dispatcher.add_handler(RM_WARN_HANDLER)
dispatcher.add_handler(LIST_WARN_HANDLER)
dispatcher.add_handler(WARN_LIMIT_HANDLER)
dispatcher.add_handler(WARN_STRENGTH_HANDLER)
dispatcher.add_handler(WARN_FILTER_HANDLER, WARN_HANDLER_GROUP)
