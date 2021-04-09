import html
from typing import Optional, List

from telegram import Message, Chat, Update, User, ChatPermissions

from SaitamaRobot import TIGERS, WOLVES, dispatcher
from SaitamaRobot.modules.helper_funcs.chat_status import (bot_admin,
                                                           is_user_admin,
                                                           user_admin,
                                                           user_admin_no_reply)
from SaitamaRobot.modules.log_channel import loggable
from SaitamaRobot.modules.sql import antiflood_sql as sql
from telegram.error import BadRequest
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler, Filters, MessageHandler, run_async
from telegram.utils.helpers import mention_html, escape_markdown
from SaitamaRobot.modules.helper_funcs.string_handling import extract_time
from SaitamaRobot.modules.connection import connected
from SaitamaRobot.modules.helper_funcs.alternate import send_message
FLOOD_GROUP = 3


@run_async
@loggable
def check_flood(update, context) -> str:
    user = update.effective_user  # type: Optional[User]
    chat = update.effective_chat  # type: Optional[Chat]
    msg = update.effective_message  # type: Optional[Message]
    if not user:  # ignore channels
        return ""

    # ignore admins and whitelists
    if (is_user_admin(chat, user.id) or user.id in WOLVES or user.id in TIGERS):
        sql.update_flood(chat.id, None)
        return ""

    should_ban = sql.update_flood(chat.id, user.id)
    if not should_ban:
        return ""

    try:
        getmode, getvalue = sql.get_flood_setting(chat.id)
        if getmode == 1:
            chat.kick_member(user.id)
            execstrings = ("Banlandı")
            tag = "BANNED"
        elif getmode == 2:
            chat.kick_member(user.id)
            chat.unban_member(user.id)
            execstrings = ("Atıldı")
            tag = "KICKED"
        elif getmode == 3:
            context.bot.restrict_chat_member(
                chat.id,
                user.id,
                permissions=ChatPermissions(can_send_messages=False))
            execstrings = ("Susduruldu")
            tag = "MUTED"
        elif getmode == 4:
            bantime = extract_time(msg, getvalue)
            chat.kick_member(user.id, until_date=bantime)
            execstrings = ("{} müddətlik susduruldu".format(getvalue))
            tag = "TBAN"
        elif getmode == 5:
            mutetime = extract_time(msg, getvalue)
            context.bot.restrict_chat_member(
                chat.id,
                user.id,
                until_date=mutetime,
                permissions=ChatPermissions(can_send_messages=False))
            execstrings = ("{} müddətlik susduruldu".format(getvalue))
            tag = "TMUTE"
        send_message(update.effective_message,
                     "Beep Boop! Boop Beep!\n{}!".format(execstrings))

        return "<b>{}:</b>" \
               "\n#{}" \
               "\n<b>User:</b> {}" \
               "\nFlooded the group.".format(tag, html.escape(chat.title),
                                             mention_html(user.id, html.escape(user.first_name)))

    except BadRequest:
        msg.reply_text(
            "Mən burada insanları məhdudlaşdıra bilmirəm, mənə lazımi səlahiyyətləri ver!"
        )
        sql.set_flood(chat.id, 0)
        return "<b>{}:</b>" \
               "\n#INFO" \
               "\nDon't have enough permission to restrict users so automatically disabled anti-flood".format(chat.title)


@run_async
@user_admin_no_reply
@bot_admin
def flood_button(update: Update, context: CallbackContext):
    bot = context.bot
    query = update.callback_query
    user = update.effective_user
    match = re.match(r"unmute_flooder\((.+?)\)", query.data)
    if match:
        user_id = match.group(1)
        chat = update.effective_chat.id
        try:
            bot.restrict_chat_member(
                chat,
                int(user_id),
                permissions=ChatPermissions(
                    can_send_messages=True,
                    can_send_media_messages=True,
                    can_send_other_messages=True,
                    can_add_web_page_previews=True))
            update.effective_message.edit_text(
                f"{mention_html(user.id, html.escape(user.first_name))} tərəfindən susduruldu.",
                parse_mode="HTML")
        except:
            pass


@run_async
@user_admin
@loggable
def set_flood(update, context) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]
    args = context.args

    conn = connected(context.bot, update, chat, user.id, need_admin=True)
    if conn:
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        if update.effective_message.chat.type == "private":
            send_message(update.effective_message,
                         "Bu əmr qrupda işlədilə bilər PM-də yox")
            return ""
        chat_id = update.effective_chat.id
        chat_name = update.effective_message.chat.title

    if len(args) >= 1:
        val = args[0].lower()
        if val == "off" or val == "no" or val == "0":
            sql.set_flood(chat_id, 0)
            if conn:
                text = message.reply_text(
                    "{} qrupunda antiflood aktiv edildi.".format(chat_name))
            else:
                text = message.reply_text("Antiflood deaktiv edildi.")

        elif val.isdigit():
            amount = int(val)
            if amount <= 0:
                sql.set_flood(chat_id, 0)
                if conn:
                    text = message.reply_text(
                        "{} qrupunda antiflood deaktiv edildi.".format(chat_name))
                else:
                    text = message.reply_text("Antiflood deaktiv edildi.")
                return "<b>{}:</b>" \
                       "\n#SETFLOOD" \
                       "\n<b>Admin:</b> {}" \
                       "\nDisable antiflood.".format(html.escape(chat_name), mention_html(user.id, html.escape(user.first_name)))

            elif amount <= 3:
                send_message(
                    update.effective_message,
                    "Antiflood ya 0 (qeyri aktiv) ya da 3-dən böyük olmalıdır!"
                )
                return ""

            else:
                sql.set_flood(chat_id, amount)
                if conn:
                    text = message.reply_text(
                        "{} qrupunda antiflood ayarı {} edildi".format(
                            chat_name, amount))
                else:
                    text = message.reply_text(
                        "Antiflood ayarı {} edildi!".format(
                            amount))
                return "<b>{}:</b>" \
                       "\n#SETFLOOD" \
                       "\n<b>Admin:</b> {}" \
                       "\nSet antiflood to <code>{}</code>.".format(html.escape(chat_name),
                                                                    mention_html(user.id, html.escape(user.first_name)), amount)

        else:
            message.reply_text(
                "Yanlış arqument verildi. Yalnız ədədlər və ya 'off' 'no' istifadə edin")
    else:
        message.reply_text((
            "Antiflood aktiv etmək üçün `/setflood ədəd` istifadə edin.\nDeaktiv etmək üçün `/setflood off` istifadə edin!."
        ),
                           parse_mode="markdown")
    return ""


@run_async
def flood(update, context):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message

    conn = connected(context.bot, update, chat, user.id, need_admin=False)
    if conn:
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        if update.effective_message.chat.type == "private":
            send_message(update.effective_message,
                         "Əmri qrupda istifadə edin")
            return
        chat_id = update.effective_chat.id
        chat_name = update.effective_message.chat.title

    limit = sql.get_flood_limit(chat_id)
    if limit == 0:
        if conn:
            text = msg.reply_text(
                "{} qrupunda flood-a nəzarət etmirəm!".format(chat_name))
        else:
            text = msg.reply_text("Burada flood-a nəzarət etmirəm!")
    else:
        if conn:
            text = msg.reply_text(
                "{} qrupunda tez-tez {} mesaj yazanlara qarşı tədbir görürəm."
                .format(chat_name, limit))
        else:
            text = msg.reply_text(
                "Tez-tez {} mesaj yazanlara qarşı tədbir görürəm."
                .format(limit))


@run_async
@user_admin
def set_flood_mode(update, context):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]
    args = context.args

    conn = connected(context.bot, update, chat, user.id, need_admin=True)
    if conn:
        chat = dispatcher.bot.getChat(conn)
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        if update.effective_message.chat.type == "private":
            send_message(update.effective_message,
                         "Bu əmri qrupda istifadə edin")
            return ""
        chat = update.effective_chat
        chat_id = update.effective_chat.id
        chat_name = update.effective_message.chat.title

    if args:
        if args[0].lower() == 'ban':
            settypeflood = ('ban')
            sql.set_flood_strength(chat_id, 1, "0")
        elif args[0].lower() == 'kick':
            settypeflood = ('kick')
            sql.set_flood_strength(chat_id, 2, "0")
        elif args[0].lower() == 'mute':
            settypeflood = ('mute')
            sql.set_flood_strength(chat_id, 3, "0")
        elif args[0].lower() == 'tban':
            if len(args) == 1:
                teks = """Görünür ki bir zaman verməmisiniz; `/setfloodmode tban <zaman dəyəri>` istifadə edin.

Məsələn: 4m = 4 dəqiqə, 3h = 3 saat, 6d = 6 gün 5w = 5 həftə."""
                send_message(
                    update.effective_message, teks, parse_mode="markdown")
                return
            settypeflood = ("{} müddətlik banlandı".format(args[1]))
            sql.set_flood_strength(chat_id, 4, str(args[1]))
        elif args[0].lower() == 'tmute':
            if len(args) == 1:
                teks = update.effective_message, """Yanlış dəyər verdiniz; `/setfloodmode tmute <zaman dəyəri>` istifadə edin.

Məsələn: 4m = 4 dəqiqə, 3h = 3 saat, 6d = 6 gün, 5w = 5 həftə."""
                send_message(
                    update.effective_message, teks, parse_mode="markdown")
                return
            settypeflood = ("{} müddətlik susduruldu".format(args[1]))
            sql.set_flood_strength(chat_id, 5, str(args[1]))
        else:
            send_message(update.effective_message,
                         "Mən yalnız ban/kick/mute/tban/tmute başa düşürəm!")
            return
        if conn:
            text = msg.reply_text(
                "{} qrupunda flood limitinə çatanlar {} ilə cəzalandırılacaq!"
                .format(chat_name, settypeflood))
        else:
            text = msg.reply_text(
                "Flood limitinə çatanlar {} ilə cəzalandırılacaq!".format(
                    settypeflood))
        return "<b>{}:</b>\n" \
                "<b>Admin:</b> {}\n" \
                "Has changed antiflood mode. User will {}.".format(settypeflood, html.escape(chat.title),
                                                                            mention_html(user.id, html.escape(user.first_name)))
    else:
        getmode, getvalue = sql.get_flood_setting(chat.id)
        if getmode == 1:
            settypeflood = ('ban')
        elif getmode == 2:
            settypeflood = ('kick')
        elif getmode == 3:
            settypeflood = ('mute')
        elif getmode == 4:
            settypeflood = ('tban for {}'.format(getvalue))
        elif getmode == 5:
            settypeflood = ('tmute for {}'.format(getvalue))
        if conn:
            text = msg.reply_text(
                "{} qrupunda flood limitini keçənlər {} ilə cəzalandırılacaq."
                .format(chat_name, settypeflood))
        else:
            text = msg.reply_text(
                "Flood limitini keçənlər {} ilə cəzalandırılacaq."
                .format(settypeflood))
    return ""


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    limit = sql.get_flood_limit(chat_id)
    if limit == 0:
        return "Flood-a nəzarət etmirəm."
    else:
        return "Yeni antiflood limiti -->`{}`.".format(limit)


__help__ = """
Antiflood sayəsində qrupunuza flood edənlərə qarşl müəyyən tədbirlər görə bilərsiniz.

 Eyni vaxtda 10 dan çox mesaj göndərənlər susdurulacaq. Bunu dəyişə də bilərsiniz.
 • `/flood`*:* Hazırki flood ayarını göstərir

• *Sadəcə adminlər:*
 • `/setflood <int/'no'/'off'>`*:* flood-a nəzarəti aktiv/deaktiv edir
 *məsələn:* `/setflood 10`
 • `/setfloodmode <ban/kick/mute/tban/tmute> <dəyər>`*:* Flood limitini keçənlərə qarşı ediləcək tədbirlər. ban/kick/mute/tmute/tban

• *Not:*
 • tban və tmute üçün bir dəyər vermək məcburidir!!
 dəyərlər aşağıdakı kimi ola bilər:
 `5m` = 5 dəqiqə
 `6h` = 6 saat
 `3d` = 3 gün
 `1w` = 1 həftə
 """

__mod_name__ = "Anti-Flood"

FLOOD_BAN_HANDLER = MessageHandler(
    Filters.all & ~Filters.status_update & Filters.group, check_flood)
SET_FLOOD_HANDLER = CommandHandler("setflood", set_flood, filters=Filters.group)
SET_FLOOD_MODE_HANDLER = CommandHandler(
    "setfloodmode", set_flood_mode, pass_args=True)  #, filters=Filters.group)
FLOOD_QUERY_HANDLER = CallbackQueryHandler(
    flood_button, pattern=r"unmute_flooder")
FLOOD_HANDLER = CommandHandler("flood", flood, filters=Filters.group)

dispatcher.add_handler(FLOOD_BAN_HANDLER, FLOOD_GROUP)
dispatcher.add_handler(FLOOD_QUERY_HANDLER)
dispatcher.add_handler(SET_FLOOD_HANDLER)
dispatcher.add_handler(SET_FLOOD_MODE_HANDLER)
dispatcher.add_handler(FLOOD_HANDLER)

__handlers__ = [(FLOOD_BAN_HANDLER, FLOOD_GROUP), SET_FLOOD_HANDLER,
                FLOOD_HANDLER, SET_FLOOD_MODE_HANDLER]
