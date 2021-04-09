import html
import time
from datetime import datetime
from io import BytesIO
from SaitamaRobot.modules.sql.users_sql import get_user_com_chats
import SaitamaRobot.modules.sql.global_bans_sql as sql
from SaitamaRobot import (DEV_USERS, EVENT_LOGS, OWNER_ID, STRICT_GBAN, DRAGONS,
                          SUPPORT_CHAT, SPAMWATCH_SUPPORT_CHAT, DEMONS, TIGERS,
                          WOLVES, sw, dispatcher)
from SaitamaRobot.modules.helper_funcs.chat_status import (is_user_admin,
                                                           support_plus,
                                                           user_admin)
from SaitamaRobot.modules.helper_funcs.extraction import (extract_user,
                                                          extract_user_and_text)
from SaitamaRobot.modules.helper_funcs.misc import send_to_list
from telegram import ParseMode, Update
from telegram.error import BadRequest, TelegramError
from telegram.ext import (CallbackContext, CommandHandler, Filters,
                          MessageHandler, run_async)
from telegram.utils.helpers import mention_html

GBAN_ENFORCE_GROUP = 6

GBAN_ERRORS = {
    "User is an administrator of the chat",
    "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant",
    "Peer_id_invalid",
    "Group chat was deactivated",
    "Need to be inviter of a user to kick it from a basic group",
    "Chat_admin_required",
    "Only the creator of a basic group can kick group administrators",
    "Channel_private",
    "Not in the chat",
    "Can't remove chat owner",
}

UNGBAN_ERRORS = {
    "User is an administrator of the chat",
    "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant",
    "Method is available for supergroup and channel chats only",
    "Not in the chat",
    "Channel_private",
    "Chat_admin_required",
    "Peer_id_invalid",
    "User not found",
}


@run_async
@support_plus
def gban(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    log_message = ""

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text(
            "Bir istifadəçiyə istinad etmirsiniz.."
        )
        return

    if int(user_id) in DEV_USERS:
        message.reply_text(
            "Bu istifadəçi PakizəTeam-in bir parçasıdır\nOna qarşı bunu edə bilmərəm."
        )
        return

    if int(user_id) in DRAGONS:
        message.reply_text(
            "Mən balaca gözlərim ilə ağlayıram... sudo istifadəçi müharibəsi! Siz niyə bir birinizə bunu edirsiniz?"
        )
        return

    if int(user_id) in DEMONS:
        message.reply_text(
            "OOOH kimsə şeytan istifadəçimizi gban etməyə çalışır! *əlinə popkorn alaraq*")
        return

    if int(user_id) in TIGERS:
        message.reply_text("O pələngdir! Banlana bilməz!")
        return

    if int(user_id) in WOLVES:
        message.reply_text("yox, o bir Canavardır! Banlana bilmirlər!")
        return

    if user_id == bot.id:
        message.reply_text("hə hə gözlə özümü gban edim?")
        return

    if user_id in [777000, 1087968824]:
        message.reply_text("Axmaq! Telegrama hücum çəkməyə çalışır!")
        return

    try:
        user_chat = bot.get_chat(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("İstifadəçi tapılmadı.")
            return ""
        else:
            return

    if user_chat.type != 'private':
        message.reply_text("Bu bir istifadəçi deyil!")
        return

    if sql.is_user_gbanned(user_id):

        if not reason:
            message.reply_text(
                "Bu istifadəçi onsuz da gban edilib; Səbəbi dəyişərdim amma bir səbəb verməmisən..."
            )
            return

        old_reason = sql.update_gban_reason(
            user_id, user_chat.username or user_chat.first_name, reason)
        if old_reason:
            message.reply_text(
                "Bu istifadəçi onsuz da gban edilib, köhnə səbəb:\n"
                "<code>{}</code>\n"
                "Mən köhnə səbəbi yenisi ilə əvəz etdim!".format(
                    html.escape(old_reason)),
                parse_mode=ParseMode.HTML)

        else:
            message.reply_text(
                "Bu istifadəçi onsuz da gban edilib, amma bir səbəb verilməmişdi; Artıq bir səbəb var!"
            )

        return

    message.reply_text("za!")

    start_time = time.time()
    datetime_fmt = "%Y-%m-%dT%H:%M"
    current_time = datetime.utcnow().strftime(datetime_fmt)

    if chat.type != 'private':
        chat_origin = "<b>{} ({})</b>\n".format(
            html.escape(chat.title), chat.id)
    else:
        chat_origin = "<b>{}</b>\n".format(chat.id)

    log_message = (
        f"#GBANNED\n"
        f"<b>Originated from:</b> <code>{chat_origin}</code>\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>Banned User:</b> {mention_html(user_chat.id, user_chat.first_name)}\n"
        f"<b>Banned User ID:</b> <code>{user_chat.id}</code>\n"
        f"<b>Event Stamp:</b> <code>{current_time}</code>")

    if reason:
        if chat.type == chat.SUPERGROUP and chat.username:
            log_message += f"\n<b>Səbəb:</b> <a href=\"https://telegram.me/{chat.username}/{message.message_id}\">{reason}</a>"
        else:
            log_message += f"\n<b>Səbəb:</b> <code>{reason}</code>"

    if EVENT_LOGS:
        try:
            log = bot.send_message(
                EVENT_LOGS, log_message, parse_mode=ParseMode.HTML)
        except BadRequest as excp:
            log = bot.send_message(
                EVENT_LOGS, log_message +
                "\n\nXəta baş verdi.")

    else:
        send_to_list(bot, DRAGONS + DEMONS, log_message, html=True)

    sql.gban_user(user_id, user_chat.username or user_chat.first_name, reason)

    chats = get_user_com_chats(user_id)
    gbanned_chats = 0

    for chat in chats:
        chat_id = int(chat)

        # Check if this group has disabled gbans
        if not sql.does_chat_gban(chat_id):
            continue

        try:
            bot.kick_chat_member(chat_id, user_id)
            gbanned_chats += 1

        except BadRequest as excp:
            if excp.message in GBAN_ERRORS:
                pass
            else:
                message.reply_text(f"Gban etmək mümkün olmadı. Xəta: {excp.message}")
                if EVENT_LOGS:
                    bot.send_message(
                        EVENT_LOGS,
                        f"Gban etmək mümkün olmadı. Xəta: {excp.message}",
                        parse_mode=ParseMode.HTML)
                else:
                    send_to_list(bot, DRAGONS + DEMONS,
                                 f"Gban etmək olmadı. Xəta: {excp.message}")
                sql.ungban_user(user_id)
                return
        except TelegramError:
            pass

    if EVENT_LOGS:
        log.edit_text(
            log_message +
            f"\n<b>Banlandığı qruplar:</b> <code>{gbanned_chats}</code>",
            parse_mode=ParseMode.HTML)
    else:
        send_to_list(
            bot,
            DRAGONS + DEMONS,
            f"Gban tamamlandı! (İstifadəçi <code>{gbanned_chats}</code> qrupdan banlandı)",
            html=True)

    end_time = time.time()
    gban_time = round((end_time - start_time), 2)

    if gban_time > 60:
        gban_time = round((gban_time / 60), 2)
        message.reply_text("Hazır! Gban edildi.", parse_mode=ParseMode.HTML)
    else:
        message.reply_text("Hazır! Gban edildi.", parse_mode=ParseMode.HTML)

    try:
        bot.send_message(
            user_id, "#EVENT"
            "You have been marked as Malicious and as such have been banned from any future groups we manage."
            f"\n<b>Reason:</b> <code>{html.escape(user.reason)}</code>"
            f"</b>Appeal Chat:</b> @{SUPPORT_CHAT}",
            parse_mode=ParseMode.HTML)
    except:
        pass  # bot probably blocked by user


@run_async
@support_plus
def ungban(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    log_message = ""

    user_id = extract_user(message, args)

    if not user_id:
        message.reply_text(
            "Bir istifadəçiyə istinad etmirsiniz.."
        )
        return

    user_chat = bot.get_chat(user_id)
    if user_chat.type != 'private':
        message.reply_text("Bu bir istifadəçi deyil!")
        return

    if not sql.is_user_gbanned(user_id):
        message.reply_text("Bu istifadəçi gban edilməyib!")
        return

    message.reply_text(
        f"Mən {user_chat.first_name} istifadəçisinə qlobal olaraq 2-ci şans verirəm.")

    start_time = time.time()
    datetime_fmt = "%Y-%m-%dT%H:%M"
    current_time = datetime.utcnow().strftime(datetime_fmt)

    if chat.type != 'private':
        chat_origin = f"<b>{html.escape(chat.title)} ({chat.id})</b>\n"
    else:
        chat_origin = f"<b>{chat.id}</b>\n"

    log_message = (
        f"#UNGBANNED\n"
        f"<b>Originated from:</b> <code>{chat_origin}</code>\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>Unbanned User:</b> {mention_html(user_chat.id, user_chat.first_name)}\n"
        f"<b>Unbanned User ID:</b> <code>{user_chat.id}</code>\n"
        f"<b>Event Stamp:</b> <code>{current_time}</code>")

    if EVENT_LOGS:
        try:
            log = bot.send_message(
                EVENT_LOGS, log_message, parse_mode=ParseMode.HTML)
        except BadRequest as excp:
            log = bot.send_message(
                EVENT_LOGS, log_message +
                "\n\nXəta baş verdi.")
    else:
        send_to_list(bot, DRAGONS + DEMONS, log_message, html=True)

    chats = get_user_com_chats(user_id)
    ungbanned_chats = 0

    for chat in chats:
        chat_id = int(chat)

        # Check if this group has disabled gbans
        if not sql.does_chat_gban(chat_id):
            continue

        try:
            member = bot.get_chat_member(chat_id, user_id)
            if member.status == 'kicked':
                bot.unban_chat_member(chat_id, user_id)
                ungbanned_chats += 1

        except BadRequest as excp:
            if excp.message in UNGBAN_ERRORS:
                pass
            else:
                message.reply_text(f"Gbanı silmək uğursuz oldu. Xəta: {excp.message}")
                if EVENT_LOGS:
                    bot.send_message(
                        EVENT_LOGS,
                        f"Gbanı silmək uğursuz oldu. Xəta: {excp.message}",
                        parse_mode=ParseMode.HTML)
                else:
                    bot.send_message(
                        OWNER_ID, f"Gbanı silmək uğursuz oldu. Xəta: {excp.message}")
                return
        except TelegramError:
            pass

    sql.ungban_user(user_id)

    if EVENT_LOGS:
        log.edit_text(
            log_message + f"\n<b>Gbanın silindiyi qruplar:</b> {ungbanned_chats}",
            parse_mode=ParseMode.HTML)
    else:
        send_to_list(bot, DRAGONS + DEMONS, "Gbanı silmək tamamlandı!")

    end_time = time.time()
    ungban_time = round((end_time - start_time), 2)

    if ungban_time > 60:
        ungban_time = round((ungban_time / 60), 2)
        message.reply_text(
            f"Gban silindi. Silinmə prosesi {ungban_time} çəkdi")
    else:
        message.reply_text(
            f"Person has been un-gbanned. Took {ungban_time} sec")


@run_async
@support_plus
def gbanlist(update: Update, context: CallbackContext):
    banned_users = sql.get_gban_list()

    if not banned_users:
        update.effective_message.reply_text(
            "Gban almış istifadəçi yoxdur...")
        return

    banfile = 'Aşağıdakılar ilə vidalaşın.\n'
    for user in banned_users:
        banfile += f"[x] {user['name']} - {user['user_id']}\n"
        if user["reason"]:
            banfile += f"Səbəb: {user['reason']}\n"

    with BytesIO(str.encode(banfile)) as output:
        output.name = "gbanlist.txt"
        update.effective_message.reply_document(
            document=output,
            filename="gbanlist.txt",
            caption="Gban almış istifadəçilərin siyahısı.")


def check_and_ban(update, user_id, should_message=True):

    chat = update.effective_chat  # type: Optional[Chat]
    try:
        sw_ban = sw.get_ban(int(user_id))
    except AttributeError:
        sw_ban = None

    if sw_ban:
        update.effective_chat.kick_member(user_id)
        if should_message:
            update.effective_message.reply_text(
                f"<b>Diqqət</b>: Bu istifadəçi qlobal olaraq banlandı.\n"
                f"<code>*onu buradan banlayıram*</code>.\n"
                f"<b>Appeal chat</b>: {SPAMWATCH_SUPPORT_CHAT}\n"
                f"<b>ID</b>: <code>{sw_ban.id}</code>\n"
                f"<b>Səbəb</b>: <code>{html.escape(sw_ban.reason)}</code>",
                parse_mode=ParseMode.HTML)
        return

    if sql.is_user_gbanned(user_id):
        update.effective_chat.kick_member(user_id)
        if should_message:
            text = f"<b>Diqqət</b>: Bu istifadəçi qlobal olaraq banlandı.\n" \
                   f"<code>*onu buradan banlayıram*</code>.\n" \
                   f"<b>Appeal chat</b>: @{SUPPORT_CHAT}\n" \
                   f"<b>ID</b>: <code>{user_id}</code>"
            user = sql.get_gbanned_user(user_id)
            if user.reason:
                text += f"\n<b>Səbəb:</b> <code>{html.escape(user.reason)}</code>"
            update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)


@run_async
def enforce_gban(update: Update, context: CallbackContext):
    # Not using @restrict handler to avoid spamming - just ignore if cant gban.
    bot = context.bot
    if sql.does_chat_gban(
            update.effective_chat.id) and update.effective_chat.get_member(
                bot.id).can_restrict_members:
        user = update.effective_user
        chat = update.effective_chat
        msg = update.effective_message

        if user and not is_user_admin(chat, user.id):
            check_and_ban(update, user.id)
            return

        if msg.new_chat_members:
            new_members = update.effective_message.new_chat_members
            for mem in new_members:
                check_and_ban(update, mem.id)

        if msg.reply_to_message:
            user = msg.reply_to_message.from_user
            if user and not is_user_admin(chat, user.id):
                check_and_ban(update, user.id, should_message=False)


@run_async
@user_admin
def gbanstat(update: Update, context: CallbackContext):
    args = context.args
    if len(args) > 0:
        if args[0].lower() in ["on", "yes"]:
            sql.enable_gbans(update.effective_chat.id)
            update.effective_message.reply_text(
                "Antispam aktivdir ✅")
        elif args[0].lower() in ["off", "no"]:
            sql.disable_gbans(update.effective_chat.id)
            update.effective_message.reply_text("Antispam deaktivdir ❌")
    else:
        update.effective_message.reply_text(
            "Mənə bir arqument verməlisən! on/off, yes/no!\n\n"
            "Hazırki ayar: {}\n"
            "Aktiv olduqda gban bu bu qrupa təsir edəcək. Əks halda yox.".format(sql.does_chat_gban(update.effective_chat.id)))


def __stats__():
    return f"• {sql.num_gbanned_users()} gban edilmiş istifadəçi."


def __user_info__(user_id):
    is_gbanned = sql.is_user_gbanned(user_id)
    text = "Zərərlidirmi: <b>{}</b>"
    if user_id in [777000, 1087968824]:
        return ""
    if user_id == dispatcher.bot.id:
        return ""
    if int(user_id) in DRAGONS + TIGERS + WOLVES:
        return ""
    if is_gbanned:
        text = text.format("Hə")
        user = sql.get_gbanned_user(user_id)
        if user.reason:
            text += f"\n<b>Səbəb:</b> <code>{html.escape(user.reason)}</code>"
        text += f"\n<b>Müraciət:</b> @{SUPPORT_CHAT}"
    else:
        text = text.format("???")
    return text


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    return f"Gban bu qrupa təsir edirmi: `{sql.does_chat_gban(chat_id)}`."


__help__ = f"""
*Sadəcə adminlər:*
 • `/antispam <on/off/yes/no>`*:* antispam aktiv/deaktiv edər.

Bütün qruplar arasında spam göndərmələri qadağan etmək üçün bot devləri tərəfindən \
istifadə edilən Anti-Spam. Bu, spam daşqınlarını mümkün qədər tez silməklə sizi və qruplarınızı qorumağa kömək edir.
*Qeyd:* @{SUPPORT_CHAT} qrupunda belə istifadəçiləri şikayət edə bilərsiniz

Bu, spam göndəriciləri söhbət otağınızdan mümkün qədər çox çıxarmaq üçün @Spamwatch API-ni də birləşdirir!
*SpamWatch nədir?*
SpamWatch spam botlar, trollar, bitkoin spamerləri və xoşagəlməz simvolların daima yenilənən böyük bir siyahısını saxlayır.[.](https://telegra.ph/file/f584b643c6f4be0b1de53.jpg)
Daim avtomatik olaraq qrupunuzdan spam göndərməyin qadağan olunmasına kömək edir. Beləliklə, spammerlərin qrupunuza hücum etməsindən narahat olmayacaqsınız..
*Qeyd:* İstifadəçilər spam izləmə qadağalarına @SpamwatchSupport ünvanından müraciət edə bilərlər
"""

GBAN_HANDLER = CommandHandler("gban", gban)
UNGBAN_HANDLER = CommandHandler("ungban", ungban)
GBAN_LIST = CommandHandler("gbanlist", gbanlist)

GBAN_STATUS = CommandHandler("antispam", gbanstat, filters=Filters.group)

GBAN_ENFORCER = MessageHandler(Filters.all & Filters.group, enforce_gban)

dispatcher.add_handler(GBAN_HANDLER)
dispatcher.add_handler(UNGBAN_HANDLER)
dispatcher.add_handler(GBAN_LIST)
dispatcher.add_handler(GBAN_STATUS)

__mod_name__ = "Anti-Spam"
__handlers__ = [GBAN_HANDLER, UNGBAN_HANDLER, GBAN_LIST, GBAN_STATUS]

if STRICT_GBAN:  # enforce GBANS if this is set
    dispatcher.add_handler(GBAN_ENFORCER, GBAN_ENFORCE_GROUP)
    __handlers__.append((GBAN_ENFORCER, GBAN_ENFORCE_GROUP))
