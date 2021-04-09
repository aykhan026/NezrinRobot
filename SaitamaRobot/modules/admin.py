import html

from telegram import ParseMode, Update
from telegram.error import BadRequest
from telegram.ext import CallbackContext, CommandHandler, Filters, run_async
from telegram.utils.helpers import mention_html

from SaitamaRobot import DRAGONS, dispatcher
from SaitamaRobot.modules.disable import DisableAbleCommandHandler
from SaitamaRobot.modules.helper_funcs.chat_status import (bot_admin, can_pin,
                                                           can_promote,
                                                           connection_status,
                                                           user_admin,
                                                           ADMIN_CACHE)

from SaitamaRobot.modules.helper_funcs.extraction import (extract_user,
                                                          extract_user_and_text)
from SaitamaRobot.modules.log_channel import loggable
from SaitamaRobot.modules.helper_funcs.alternate import send_message


@run_async
@connection_status
@bot_admin
@can_promote
@user_admin
@loggable
def promote(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args

    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    promoter = chat.get_member(user.id)

    if not (promoter.can_promote_members or
            promoter.status == "creator") and not user.id in DRAGONS:
        message.reply_text("Lazımi səlahiyyətlərin yoxdur!")
        return

    user_id = extract_user(message, args)

    if not user_id:
        message.reply_text(
            "Bir istifadəçiyə istinad etmirsiniz.."
        )
        return

    try:
        user_member = chat.get_member(user_id)
    except:
        return

    if user_member.status == 'administrator' or user_member.status == 'creator':
        message.reply_text(
            "Onsuz da admin olan birini necə admin edə bilərəmki?")
        return

    if user_id == bot.id:
        message.reply_text(
            "Özümü admin edə bilmərəm! Admin edəcəyim bir user ver.")
        return

    # set same perms as bot - bot can't assign higher perms than itself!
    bot_member = chat.get_member(bot.id)

    try:
        bot.promoteChatMember(
            chat.id,
            user_id,
            can_change_info=bot_member.can_change_info,
            can_post_messages=bot_member.can_post_messages,
            can_edit_messages=bot_member.can_edit_messages,
            can_delete_messages=bot_member.can_delete_messages,
            can_invite_users=bot_member.can_invite_users,
            # can_promote_members=bot_member.can_promote_members,
            can_restrict_members=bot_member.can_restrict_members,
            can_pin_messages=bot_member.can_pin_messages)
    except BadRequest as err:
        if err.message == "User_not_mutual_contact":
            message.reply_text(
                "Qrupda olmayan birini admin edə bilmərəm.")
        else:
            message.reply_text("Bir xəta yarandı.")
        return

    bot.sendMessage(
        chat.id,
        f"<b>{user_member.user.first_name or user_id}</b> Admin Edildi💛!",
        parse_mode=ParseMode.HTML)

    log_message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#PROMOTED\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>User:</b> {mention_html(user_member.user.id, user_member.user.first_name)}"
    )

    return log_message


@run_async
@connection_status
@bot_admin
@can_promote
@user_admin
@loggable
def demote(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args

    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text(
            "Bir istifadəçiyə istinad etmirsiniz.."
        )
        return

    try:
        user_member = chat.get_member(user_id)
    except:
        return

    if user_member.status == 'creator':
        message.reply_text(
            "Nə, Qrup yaradıcısının adminliyini almaq mümkün deyil?")
        return

    if not user_member.status == 'administrator':
        message.reply_text("Admin olmayan birinin adminliyini almaq mümkün deyil!")
        return

    if user_id == bot.id:
        message.reply_text(
            "Öz adminliyimi ala bilmərəm! Bunu başqa admin edə bilər.")
        return

    try:
        bot.promoteChatMember(
            chat.id,
            user_id,
            can_change_info=False,
            can_post_messages=False,
            can_edit_messages=False,
            can_delete_messages=False,
            can_invite_users=False,
            can_restrict_members=False,
            can_pin_messages=False,
            can_promote_members=False)

        bot.sendMessage(
            chat.id,
            f" <b>{user_member.user.first_name or user_id}</b> istifadəçisinin adminliyini aldım!",
            parse_mode=Parsemode.HTML)

        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#DEMOTED\n"
            f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
            f"<b>User:</b> {mention_html(user_member.user.id, user_member.user.first_name)}"
        )

        return log_message
    except BadRequest:
        message.reply_text(
            "Adminliyini almaq mümkün olmadı. Yəqin ki admin deyiləm, və ya adminliyini başqası verib."
            " Əməliyyat uğursuz oldu!")
        return


@run_async
@user_admin
def refresh_admin(update, _):
    try:
        ADMIN_CACHE.pop(update.effective_chat.id)
    except KeyError:
        pass

    update.effective_message.reply_text("Admin siyahısı yeniləndi!")


@run_async
@connection_status
@bot_admin
@can_promote
@user_admin
def set_title(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args

    chat = update.effective_chat
    message = update.effective_message

    user_id, title = extract_user_and_text(message, args)
    try:
        user_member = chat.get_member(user_id)
    except:
        return

    if not user_id:
        message.reply_text(
            "Bir istifadəçiyə istinad etmirsiniz.."
        )
        return

    if user_member.status == 'creator':
        message.reply_text(
             "Bu şəxs qrup yaradıcısıdır və mən onun adminlik başlığını dəyişə bilmərəm?")
        return

    if not user_member.status == 'administrator':
        message.reply_text(
            "Admin olmayanlara başlıq qoymaq mümkün deyil!\nİlk öncə onları admin edin!"
        )
        return

    if user_id == bot.id:
        message.reply_text(
            "Öz başlığımı dəyişə bilmərəm! Bunu mənim üçün başqası edə bilər."
        )
        return

    if not title:
        message.reply_text("Axı bir başlıq verməmisən!")
        return

    if len(title) > 16:
        message.reply_text(
            "Başlıq 16 simvoldan çox ola bilməz."
        )

    try:
        bot.setChatAdministratorCustomTitle(chat.id, user_id, title)
    except BadRequest:
        message.reply_text(
            "Mən sadəcə adminlik hüququnu özüm verdiyim şəxslərin başlığını dəyişə bilərəm!")
        return

    bot.sendMessage(
        chat.id,
        f"<code>{user_member.user.first_name or user_id}</code> adminin başlığı "
        f"<code>{html.escape(title[:16])}</code> olaraq ayarlandı!",
        parse_mode=ParseMode.HTML)


@run_async
@bot_admin
@can_pin
@user_admin
@loggable
def pin(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args

    user = update.effective_user
    chat = update.effective_chat

    is_group = chat.type != "private" and chat.type != "channel"
    prev_message = update.effective_message.reply_to_message

    is_silent = True
    if len(args) >= 1:
        is_silent = not (args[0].lower() == 'notify' or args[0].lower()
                         == 'loud' or args[0].lower() == 'violent')

    if prev_message and is_group:
        try:
            bot.pinChatMessage(
                chat.id,
                prev_message.message_id,
                disable_notification=is_silent)
        except BadRequest as excp:
            if excp.message == "Chat_not_modified":
                pass
            else:
                raise
        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#PINNED\n"
            f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}"
        )

        return log_message


@run_async
@bot_admin
@can_pin
@user_admin
@loggable
def unpin(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    chat = update.effective_chat
    user = update.effective_user

    try:
        bot.unpinChatMessage(chat.id)
    except BadRequest as excp:
        if excp.message == "Chat_not_modified":
            pass
        else:
            raise

    log_message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#UNPINNED\n"
        f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}")

    return log_message


@run_async
@bot_admin
@user_admin
@connection_status
def invite(update: Update, context: CallbackContext):
    bot = context.bot
    chat = update.effective_chat

    if chat.username:
        update.effective_message.reply_text(f"https://t.me/{chat.username}")
    elif chat.type == chat.SUPERGROUP or chat.type == chat.CHANNEL:
        bot_member = chat.get_member(bot.id)
        if bot_member.can_invite_users:
            invitelink = bot.exportChatInviteLink(chat.id)
            update.effective_message.reply_text(invitelink)
        else:
            update.effective_message.reply_text(
                "Dəvət linkini gətirə bilmədim! Səlahiyyətlərimi nəzərdən keçir."
            )
    else:
        update.effective_message.reply_text(
            "Mən sənə sadəcə superqrup və kanalların dəvət linkini verə bilərəm!"
        )


@run_async
@connection_status
def adminlist(update, context):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    args = context.args
    bot = context.bot

    if update.effective_message.chat.type == "private":
        send_message(update.effective_message,
                     "Bu əmr qruplarda işləyir.")
        return

    chat = update.effective_chat
    chat_id = update.effective_chat.id
    chat_name = update.effective_message.chat.title

    try:
        msg = update.effective_message.reply_text(
            'Admin siyahısı gətirilir...', parse_mode=ParseMode.HTML)
    except BadRequest:
        msg = update.effective_message.reply_text(
            'Admin siyahısı gətirilir...', quote=False, parse_mode=ParseMode.HTML)

    administrators = bot.getChatAdministrators(chat_id)
    text = "<b>{}</b> qrupundakı adminlər:".format(
        html.escape(update.effective_chat.title))

    bot_admin_list = []

    for admin in administrators:
        user = admin.user
        status = admin.status
        custom_title = admin.custom_title

        if user.first_name == '':
            name = "☠ Silinən Hesab"
        else:
            name = "{}".format(
                mention_html(
                    user.id,
                    html.escape(user.first_name + " " +
                                (user.last_name or ""))))

        if user.is_bot:
            bot_admin_list.append(name)
            administrators.remove(admin)
            continue

        #if user.username:
        #    name = escape_markdown("@" + user.username)
        if status == "creator":
            text += "\n 👑 Creator:"
            text += "\n<code> • </code>{}\n".format(name)

            if custom_title:
                text += f"<code> ┗━ {html.escape(custom_title)}</code>\n"

    text += "\n🔱 Adminlər:"

    custom_admin_list = {}
    normal_admin_list = []

    for admin in administrators:
        user = admin.user
        status = admin.status
        custom_title = admin.custom_title

        if user.first_name == '':
            name = "☠ Silinən Hesab"
        else:
            name = "{}".format(
                mention_html(
                    user.id,
                    html.escape(user.first_name + " " +
                                (user.last_name or ""))))
        #if user.username:
        #    name = escape_markdown("@" + user.username)
        if status == "administrator":
            if custom_title:
                try:
                    custom_admin_list[custom_title].append(name)
                except KeyError:
                    custom_admin_list.update({custom_title: [name]})
            else:
                normal_admin_list.append(name)

    for admin in normal_admin_list:
        text += "\n<code> • </code>{}".format(admin)

    for admin_group in custom_admin_list.copy():
        if len(custom_admin_list[admin_group]) == 1:
            text += "\n<code> • </code>{} | <code>{}</code>".format(
                custom_admin_list[admin_group][0], html.escape(admin_group))
            custom_admin_list.pop(admin_group)

    text += "\n"
    for admin_group in custom_admin_list:
        text += "\n🚨 <code>{}</code>".format(admin_group)
        for admin in custom_admin_list[admin_group]:
            text += "\n<code> • </code>{}".format(admin)
        text += "\n"

    text += "\n🤖 Botlar:"
    for each_bot in bot_admin_list:
        text += "\n<code> • </code>{}".format(each_bot)

    try:
        msg.edit_text(text, parse_mode=ParseMode.HTML)
    except BadRequest:  # if original message is deleted
        return


__help__ = """
 • `/admins`*:* qrupdakı adminlərin siyahısını verir

*Sadəcə adminlər:*
 • `/pin`*:* bir mesajı səssizcə sabitləyir - bildiriş göndərmək üçün `'loud'` və ya `'notify'` əlavə edin
 • `/unpin`*:* sabitli mesajın sabitini silir
 • `/invitelink`*:* qrupun dəvət linkini verir
 • `/promote`*:* istifadəçini admin edir
 • `/demote`*:* istifadəçinin adminliyini alır
 • `/title <başlıq>`*:* adminin adminlik tagını dəyişir
 • `/admincache`*:* admin siyahısını yeniləyir
"""

ADMINLIST_HANDLER = DisableAbleCommandHandler("admins", adminlist)

PIN_HANDLER = CommandHandler("pin", pin, filters=Filters.group)
UNPIN_HANDLER = CommandHandler("unpin", unpin, filters=Filters.group)

INVITE_HANDLER = DisableAbleCommandHandler("invitelink", invite)

PROMOTE_HANDLER = DisableAbleCommandHandler("promote", promote)
DEMOTE_HANDLER = DisableAbleCommandHandler("demote", demote)

SET_TITLE_HANDLER = CommandHandler("title", set_title)
ADMIN_REFRESH_HANDLER = CommandHandler(
    "admincache", refresh_admin, filters=Filters.group)

dispatcher.add_handler(ADMINLIST_HANDLER)
dispatcher.add_handler(PIN_HANDLER)
dispatcher.add_handler(UNPIN_HANDLER)
dispatcher.add_handler(INVITE_HANDLER)
dispatcher.add_handler(PROMOTE_HANDLER)
dispatcher.add_handler(DEMOTE_HANDLER)
dispatcher.add_handler(SET_TITLE_HANDLER)
dispatcher.add_handler(ADMIN_REFRESH_HANDLER)

__mod_name__ = "Admin"
__command_list__ = [
    "adminlist", "admins", "invitelink", "promote", "demote", "admincache"
]
__handlers__ = [
    ADMINLIST_HANDLER, PIN_HANDLER, UNPIN_HANDLER, INVITE_HANDLER,
    PROMOTE_HANDLER, DEMOTE_HANDLER, SET_TITLE_HANDLER, ADMIN_REFRESH_HANDLER
]
