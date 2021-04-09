import time
import re

from telegram import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton, Update, Bot
from telegram.error import BadRequest, Unauthorized
from telegram.ext import CommandHandler, CallbackQueryHandler, run_async

import SaitamaRobot.modules.sql.connection_sql as sql
from SaitamaRobot import dispatcher, DRAGONS, DEV_USERS
from SaitamaRobot.modules.helper_funcs import chat_status
from SaitamaRobot.modules.helper_funcs.alternate import send_message, typing_action

user_admin = chat_status.user_admin


@user_admin
@run_async
@typing_action
def allow_connections(update, context) -> str:

    chat = update.effective_chat
    args = context.args

    if chat.type != chat.PRIVATE:
        if len(args) >= 1:
            var = args[0]
            if var == "no":
                sql.set_allow_connect_to_chat(chat.id, False)
                send_message(
                    update.effective_message,
                    "Bu qrup üçün əlaqələr deaktiv edilib",
                )
            elif var == "yes":
                sql.set_allow_connect_to_chat(chat.id, True)
                send_message(
                    update.effective_message,
                    "Bu qrup üçün əlaqələr aktiv edilib",
                )
            else:
                send_message(
                    update.effective_message,
                    "Zəhmət olmasa `yes` və ya `no` istifadə edin!",
                    parse_mode=ParseMode.MARKDOWN,
                )
        else:
            get_settings = sql.allow_connect_to_chat(chat.id)
            if get_settings:
                send_message(
                    update.effective_message,
                    "Bu qrupa qoşulma (Connection) üzvlər üçün *İcazə verilir*!",
                    parse_mode=ParseMode.MARKDOWN,
                )
            else:
                send_message(
                    update.effective_message,
                    "Bu qrupa qoşulma (Connection) üzvlər üçün *İcazə verilmir*!",
                    parse_mode=ParseMode.MARKDOWN,
                )
    else:
        send_message(update.effective_message,
                     "Bu əmr qrup üçündür!")


@run_async
@typing_action
def connection_chat(update, context):

    chat = update.effective_chat
    user = update.effective_user

    conn = connected(context.bot, update, chat, user.id, need_admin=True)

    if conn:
        chat = dispatcher.bot.getChat(conn)
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        if update.effective_message.chat.type != "private":
            return
        chat = update.effective_chat
        chat_name = update.effective_message.chat.title

    if conn:
        message = "Hazırki qrup bu qrupa qoşulub --> {}.\n".format(chat_name)
    else:
        message = "Bu qrup hazırda heç bir qrupa qoşulmayıb.\n"
    send_message(update.effective_message, message, parse_mode="markdown")


@run_async
@typing_action
def connect_chat(update, context):

    chat = update.effective_chat
    user = update.effective_user
    args = context.args

    if update.effective_chat.type == "private":
        if args and len(args) >= 1:
            try:
                connect_chat = int(args[0])
                getstatusadmin = context.bot.get_chat_member(
                    connect_chat, update.effective_message.from_user.id)
            except ValueError:
                try:
                    connect_chat = str(args[0])
                    get_chat = context.bot.getChat(connect_chat)
                    connect_chat = get_chat.id
                    getstatusadmin = context.bot.get_chat_member(
                        connect_chat, update.effective_message.from_user.id)
                except BadRequest:
                    send_message(update.effective_message, "Yanlış qrup ID!")
                    return
            except BadRequest:
                send_message(update.effective_message, "Yanlış qrup ID!")
                return

            isadmin = getstatusadmin.status in ("administrator", "creator")
            ismember = getstatusadmin.status in ("member")
            isallow = sql.allow_connect_to_chat(connect_chat)

            if (isadmin) or (isallow and ismember) or (user.id in DRAGONS):
                connection_status = sql.connect(
                    update.effective_message.from_user.id, connect_chat)
                if connection_status:
                    conn_chat = dispatcher.bot.getChat(
                        connected(
                            context.bot,
                            update,
                            chat,
                            user.id,
                            need_admin=False))
                    chat_name = conn_chat.title
                    send_message(
                        update.effective_message,
                        "Uğurla *{}* qrupuna qoşuldu. \n/helpconnect istifadə edərək mövcud əmrlərə baxa bilərsən."
                        .format(chat_name),
                        parse_mode=ParseMode.MARKDOWN,
                    )
                    sql.add_history_conn(user.id, str(conn_chat.id), chat_name)
                else:
                    send_message(update.effective_message, "Qoşulma uğursuz oldu!")
            else:
                send_message(update.effective_message,
                             "Bu qrupa qoşulmalar deaktiv edilib!")
        else:
            gethistory = sql.get_history_conn(user.id)
            if gethistory:
                buttons = [
                    InlineKeyboardButton(
                        text="❎ Bağla", callback_data="connect_close"),
                    InlineKeyboardButton(
                        text="🧹 Təmizlə", callback_data="connect_clear"),
                ]
            else:
                buttons = []
            conn = connected(
                context.bot, update, chat, user.id, need_admin=False)
            if conn:
                connectedchat = dispatcher.bot.getChat(conn)
                text = "Sən hal hazırda bu qrupla əlaqə qurmusan *{}* (`{}`)".format(
                    connectedchat.title, conn)
                buttons.append(
                    InlineKeyboardButton(
                        text="🔌 Əlaqəni kəs",
                        callback_data="connect_disconnect"))
            else:
                text = "Qoşulmaq üçün qrup ID və ya etiketi yazın!"
            if gethistory:
                text += "\n\n*Əlaqə tarixçəsi:*\n"
                text += "╒═══「 *Info* 」\n"
                text += "│  Çeşidləndi: `Ən Yeni`\n"
                text += "│\n"
                buttons = [buttons]
                for x in sorted(gethistory.keys(), reverse=True):
                    htime = time.strftime("%d/%m/%Y", time.localtime(x))
                    text += "╞═「 *{}* 」\n│   `{}`\n│   `{}`\n".format(
                        gethistory[x]["chat_name"], gethistory[x]["chat_id"],
                        htime)
                    text += "│\n"
                    buttons.append([
                        InlineKeyboardButton(
                            text=gethistory[x]["chat_name"],
                            callback_data="connect({})".format(
                                gethistory[x]["chat_id"]),
                        )
                    ])
                text += "╘══「 Ümumi {} qrup 」".format(
                    str(len(gethistory)) +
                    " (max)" if len(gethistory) == 5 else str(len(gethistory)))
                conn_hist = InlineKeyboardMarkup(buttons)
            elif buttons:
                conn_hist = InlineKeyboardMarkup([buttons])
            else:
                conn_hist = None
            send_message(
                update.effective_message,
                text,
                parse_mode="markdown",
                reply_markup=conn_hist,
            )

    else:
        getstatusadmin = context.bot.get_chat_member(
            chat.id, update.effective_message.from_user.id)
        isadmin = getstatusadmin.status in ("administrator", "creator")
        ismember = getstatusadmin.status in ("member")
        isallow = sql.allow_connect_to_chat(chat.id)
        if (isadmin) or (isallow and ismember) or (user.id in DRAGONS):
            connection_status = sql.connect(
                update.effective_message.from_user.id, chat.id)
            if connection_status:
                chat_name = dispatcher.bot.getChat(chat.id).title
                send_message(
                    update.effective_message,
                    "*{}* qrupu ilə əlaqə yaradıldı.".format(chat_name),
                    parse_mode=ParseMode.MARKDOWN,
                )
                try:
                    sql.add_history_conn(user.id, str(chat.id), chat_name)
                    context.bot.send_message(
                        update.effective_message.from_user.id,
                        "Sən hazırda *{}* qrupu ilə əlaqə yaratmısan. \n`/helpconnect` yazaraq mövcud əmrlərə baxa bilərsən."
                        .format(chat_name),
                        parse_mode="markdown",
                    )
                except BadRequest:
                    pass
                except Unauthorized:
                    pass
            else:
                send_message(update.effective_message, "Əlaqə uğursuz oldu!")
        else:
            send_message(update.effective_message,
                         "Bu qrup ilə əlaqələr deaktiv edilib!")


def disconnect_chat(update, context):

    if update.effective_chat.type == "private":
        disconnection_status = sql.disconnect(
            update.effective_message.from_user.id)
        if disconnection_status:
            sql.disconnected_chat = send_message(update.effective_message,
                                                 "Qrup ilə əlaqə uğurla kəsildi!")
        else:
            send_message(update.effective_message, "Sən qoşulmamısan!")
    else:
        send_message(update.effective_message,
                     "Bu əmr yalnız PM-də mövcuddur.")


def connected(bot: Bot, update: Update, chat, user_id, need_admin=True):
    user = update.effective_user

    if chat.type == chat.PRIVATE and sql.get_connected_chat(user_id):

        conn_id = sql.get_connected_chat(user_id).chat_id
        getstatusadmin = bot.get_chat_member(
            conn_id, update.effective_message.from_user.id)
        isadmin = getstatusadmin.status in ("administrator", "creator")
        ismember = getstatusadmin.status in ("member")
        isallow = sql.allow_connect_to_chat(conn_id)

        if ((isadmin) or (isallow and ismember) or (user.id in DRAGONS) or
            (user.id in DEV_USERS)):
            if need_admin is True:
                if (getstatusadmin.status in ("administrator", "creator") or
                        user_id in DRAGONS or user.id in DEV_USERS):
                    return conn_id
                else:
                    send_message(
                        update.effective_message,
                        "Sən qoşulmuş qrupda admin olmalısan!",
                    )
            else:
                return conn_id
        else:
            send_message(
                update.effective_message,
                "Qrup əlaqə hüquqlarını dəyişdirdi, və ya artıq admin deyilsən. \nSizlə əlaqəni kəsdim.",
            )
            disconnect_chat(update, bot)
    else:
        return False


CONN_HELP = """
 Əlaqə yaradılmış qruplarla mövcud əməliyyatlar:
 • Notları görmək və dəyişmək.
 • Filtrləri görmək və dəyişmək.
 • Qrupun dəvət linkini almaq.
 • AntiFlood ayarlarını dəyişmək.
 • Qara siyahı ayarlarını dəyişmək.
 • Qrupda kilidləmək/açmaq əməliyyatları.
 • Əmrləri aktiv/deaktiv etmək.
 """


@run_async
def help_connect_chat(update, context):

    args = context.args

    if update.effective_message.chat.type != "private":
        send_message(update.effective_message,
                     "Bu əmrlə birlikdə kömək üçün mənimlə PM-də əlaqəyə keç.")
        return
    else:
        send_message(update.effective_message, CONN_HELP, parse_mode="markdown")


@run_async
def connect_button(update, context):

    query = update.callback_query
    chat = update.effective_chat
    user = update.effective_user

    connect_match = re.match(r"connect\((.+?)\)", query.data)
    disconnect_match = query.data == "connect_disconnect"
    clear_match = query.data == "connect_clear"
    connect_close = query.data == "connect_close"

    if connect_match:
        target_chat = connect_match.group(1)
        getstatusadmin = context.bot.get_chat_member(target_chat,
                                                     query.from_user.id)
        isadmin = getstatusadmin.status in ("administrator", "creator")
        ismember = getstatusadmin.status in ("member")
        isallow = sql.allow_connect_to_chat(target_chat)

        if (isadmin) or (isallow and ismember) or (user.id in DRAGONS):
            connection_status = sql.connect(query.from_user.id, target_chat)

            if connection_status:
                conn_chat = dispatcher.bot.getChat(
                    connected(
                        context.bot, update, chat, user.id, need_admin=False))
                chat_name = conn_chat.title
                query.message.edit_text(
                    "*{}* qrupu ilə əlaqə uğurla yaradıldı. \n`/helpconnect` yazaraq mövcud əmrlərə baxa bilərsən."
                    .format(chat_name),
                    parse_mode=ParseMode.MARKDOWN,
                )
                sql.add_history_conn(user.id, str(conn_chat.id), chat_name)
            else:
                query.message.edit_text("Əlaqə uğursuz oldu!")
        else:
            context.bot.answer_callback_query(
                query.id,
                "Bu qrupa qoşulmalar deaktiv edilib!",
                show_alert=True)
    elif disconnect_match:
        disconnection_status = sql.disconnect(query.from_user.id)
        if disconnection_status:
            sql.disconnected_chat = query.message.edit_text(
                "Qrup ilə əlaqə kəsildi!")
        else:
            context.bot.answer_callback_query(
                query.id, "Sən qoşulmamısan!", show_alert=True)
    elif clear_match:
        sql.clear_history_conn(query.from_user.id)
        query.message.edit_text("Qoşulmalarla bağlı tarixçə silindi!")
    elif connect_close:
        query.message.edit_text("Bağlandı.\nYenidən qoşulmaq üçün /connect")
    else:
        connect_chat(update, context)


__mod_name__ = "Əlaqələr"

__help__ = """
Bəzən, yalnız bir qrup söhbətinə bəzi qeydlər və filtrlər əlavə etmək istəyirsən, amma hamının görməsini istəmirsən; Bağlantıların daxil olduğu yer budur ...
Bu, bir sohbet verilənlər bazasına qoşulmağa və ona əmrlər görünmədən bir şey əlavə etməyə imkan verir! Məlum səbəblərdən, şeylər əlavə etmək üçün admin olmağınız lazımdır; lakin qrupdakı hər hansı bir üzv məlumatlarınızı görə bilər

 • /connect: Qrup ilə əlaqə yaradır (Qrupda /connect yazaraq və ya /connect <qrup id> ilə PM-də yazmaq mümkündü)
 • /connection: Qoşulmuş qrupların siyahısı
 • /disconnect: Qrup ilə əlaqəni kəsir
 • /helpconnect: Mövcud əmrləri göstərir

*Sadəcə adminlər:*
 • /allowconnect <yes/no>: qoşulmaları aktiv/deaktiv edir
"""

CONNECT_CHAT_HANDLER = CommandHandler("connect", connect_chat, pass_args=True)
CONNECTION_CHAT_HANDLER = CommandHandler("connection", connection_chat)
DISCONNECT_CHAT_HANDLER = CommandHandler("disconnect", disconnect_chat)
ALLOW_CONNECTIONS_HANDLER = CommandHandler(
    "allowconnect", allow_connections, pass_args=True)
HELP_CONNECT_CHAT_HANDLER = CommandHandler("helpconnect", help_connect_chat)
CONNECT_BTN_HANDLER = CallbackQueryHandler(connect_button, pattern=r"connect")

dispatcher.add_handler(CONNECT_CHAT_HANDLER)
dispatcher.add_handler(CONNECTION_CHAT_HANDLER)
dispatcher.add_handler(DISCONNECT_CHAT_HANDLER)
dispatcher.add_handler(ALLOW_CONNECTIONS_HANDLER)
dispatcher.add_handler(HELP_CONNECT_CHAT_HANDLER)
dispatcher.add_handler(CONNECT_BTN_HANDLER)
