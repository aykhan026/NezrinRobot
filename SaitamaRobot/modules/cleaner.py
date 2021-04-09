import html

from SaitamaRobot import ALLOW_EXCL, CustomCommandHandler, dispatcher
from SaitamaRobot.modules.disable import DisableAbleCommandHandler
from SaitamaRobot.modules.helper_funcs.chat_status import (bot_can_delete,
                                                           connection_status,
                                                           dev_plus, user_admin)
from SaitamaRobot.modules.sql import cleaner_sql as sql
from telegram import ParseMode, Update
from telegram.ext import (CallbackContext, CommandHandler, Filters,
                          MessageHandler, run_async)

if ALLOW_EXCL:
    CMD_STARTERS = ('/', '!')
else:
    CMD_STARTERS = ('/')

BLUE_TEXT_CLEAN_GROUP = 13
CommandHandlerList = (CommandHandler, CustomCommandHandler,
                      DisableAbleCommandHandler)
command_list = [
    "cleanblue", "ignoreblue", "unignoreblue", "listblue", "ungignoreblue",
    "gignoreblue"
    "start", "help", "settings", "donate", "stalk", "aka", "leaderboard"
]

for handler_list in dispatcher.handlers:
    for handler in dispatcher.handlers[handler_list]:
        if any(
                isinstance(handler, cmd_handler)
                for cmd_handler in CommandHandlerList):
            command_list += handler.command


@run_async
def clean_blue_text_must_click(update: Update, context: CallbackContext):
    bot = context.bot
    chat = update.effective_chat
    message = update.effective_message
    if chat.get_member(bot.id).can_delete_messages:
        if sql.is_enabled(chat.id):
            fst_word = message.text.strip().split(None, 1)[0]

            if len(fst_word) > 1 and any(
                    fst_word.startswith(start) for start in CMD_STARTERS):

                command = fst_word[1:].split('@')
                chat = update.effective_chat

                ignored = sql.is_command_ignored(chat.id, command[0])
                if ignored:
                    return

                if command[0] not in command_list:
                    message.delete()


@run_async
@connection_status
@bot_can_delete
@user_admin
def set_blue_text_must_click(update: Update, context: CallbackContext):
    chat = update.effective_chat
    message = update.effective_message
    bot, args = context.bot, context.args
    if len(args) >= 1:
        val = args[0].lower()
        if val in ('off', 'no'):
            sql.set_cleanbt(chat.id, False)
            reply = "Bluetext silinməsi <b>{}</b> qrupunda deaktiv edildi".format(
                html.escape(chat.title))
            message.reply_text(reply, parse_mode=ParseMode.HTML)

        elif val in ('yes', 'on'):
            sql.set_cleanbt(chat.id, True)
            reply = "Bluetext silinməsi <b>{}</b> qrupunda aktiv edildi".format(
                html.escape(chat.title))
            message.reply_text(reply, parse_mode=ParseMode.HTML)

        else:
            reply = "Yanlış arqument. Doğru arqumentlər --> 'yes', 'on', 'no', 'off'"
            message.reply_text(reply)
    else:
        clean_status = sql.is_enabled(chat.id)
        if clean_status:
            clean_status = "Enabled"
        else:
            clean_status = "Disabled"
        reply = "<b>{}</b> qrupunda Bluetext silinməsi: <b>{}</b>".format(
            html.escape(chat.title), clean_status)
        message.reply_text(reply, parse_mode=ParseMode.HTML)


@run_async
@user_admin
def add_bluetext_ignore(update: Update, context: CallbackContext):
    message = update.effective_message
    chat = update.effective_chat
    args = context.args
    if len(args) >= 1:
        val = args[0].lower()
        added = sql.chat_ignore_command(chat.id, val)
        if added:
            reply = "<b>{}</b> əmri Bluetext təmizləyici siyahınsına əlavə edildi.".format(
                args[0])
        else:
            reply = "Komanda onsuz da nəzərə alınmır."
        message.reply_text(reply, parse_mode=ParseMode.HTML)

    else:
        reply = "Nəzərə alınmayan heç bir əmr yoxdur."
        message.reply_text(reply)


@run_async
@user_admin
def remove_bluetext_ignore(update: Update, context: CallbackContext):
    message = update.effective_message
    chat = update.effective_chat
    args = context.args
    if len(args) >= 1:
        val = args[0].lower()
        removed = sql.chat_unignore_command(chat.id, val)
        if removed:
            reply = "<b>{}</b> əmri Bluetext təmizləyici siyahınsından silindi.".format(
                args[0])
        else:
            reply = "Bu əmr hazırda nəzərə alınmır."
        message.reply_text(reply, parse_mode=ParseMode.HTML)

    else:
        reply = "Nəzərə alınacaq bir əmr verməmisən."
        message.reply_text(reply)


@run_async
@user_admin
def add_bluetext_ignore_global(update: Update, context: CallbackContext):
    message = update.effective_message
    args = context.args
    if len(args) >= 1:
        val = args[0].lower()
        added = sql.global_ignore_command(val)
        if added:
            reply = "<b>{}</b> əmri qlobal olaraq Bluetext təmizləyici siyahınsına əlavə olundu.".format(
                args[0])
        else:
            reply = "Bu əmr onsuz da nəzərə alınmır."
        message.reply_text(reply, parse_mode=ParseMode.HTML)

    else:
        reply = "Nəzərə alınmayacaq bir əmr verməmisən."
        message.reply_text(reply)


@run_async
@dev_plus
def remove_bluetext_ignore_global(update: Update, context: CallbackContext):
    message = update.effective_message
    args = context.args
    if len(args) >= 1:
        val = args[0].lower()
        removed = sql.global_unignore_command(val)
        if removed:
            reply = "<b>{}</b> əmri qlobal olaraq Bluetext təmizləyici siyahınsından silindi.".format(
                args[0])
        else:
            reply = "Bu əmr hazırda nəzərə alınır. Mənə başqa bir əmr ver."
        message.reply_text(reply, parse_mode=ParseMode.HTML)

    else:
        reply = "Nəzərə alınacaq bir əmr verməmisən."
        message.reply_text(reply)


@run_async
@dev_plus
def bluetext_ignore_list(update: Update, context: CallbackContext):

    message = update.effective_message
    chat = update.effective_chat

    global_ignored_list, local_ignore_list = sql.get_all_ignored(chat.id)
    text = ""

    if global_ignored_list:
        text = "Aşağıdakı əmrlər qlobal olaraq nəzərə alınmır :\n"

        for x in global_ignored_list:
            text += f" - <code>{x}</code>\n"

    if local_ignore_list:
        text += "\nAşağıdakı əmrlər local olaraq nəzərə alınmır :\n"

        for x in local_ignore_list:
            text += f" - <code>{x}</code>\n"

    if text == "":
        text = "Hazırda nəzərə alınmayacaq bir əmr yoxdur."
        message.reply_text(text)
        return

    message.reply_text(text, parse_mode=ParseMode.HTML)
    return


__help__ = """
Blue text təmizləyicisi aktiv olduqda / ilə başlayan əmrlər silinəcəy.
 • `/cleanblue <on/off/yes/no>`*:* əmr silməni aktiv edir
 • `/ignoreblue <söz>`*:* bu əmrin avtomatik silinməsi deaktiv olur
 • `/unignoreblue <söz>`*:* yuxarıdakının əksi
 • `/listblue`*:* blue text təmizləyici aktiv olan əmrlər
 
 *Aşağıdakı əmrləri sadəcə bot adminləri işlədə bilər qrup adminləri yox:*
 • `/gignoreblue <söz>`*:* qlobal olaraq bluetext temasını aktiv edir.
 • `/ungignoreblue <söz>`*:* yuxarıdakını əksi. Yəni deaktiv edir
"""

SET_CLEAN_BLUE_TEXT_HANDLER = CommandHandler("cleanblue",
                                             set_blue_text_must_click)
ADD_CLEAN_BLUE_TEXT_HANDLER = CommandHandler("ignoreblue", add_bluetext_ignore)
REMOVE_CLEAN_BLUE_TEXT_HANDLER = CommandHandler("unignoreblue",
                                                remove_bluetext_ignore)
ADD_CLEAN_BLUE_TEXT_GLOBAL_HANDLER = CommandHandler("gignoreblue",
                                                    add_bluetext_ignore_global)
REMOVE_CLEAN_BLUE_TEXT_GLOBAL_HANDLER = CommandHandler(
    "ungignoreblue", remove_bluetext_ignore_global)
LIST_CLEAN_BLUE_TEXT_HANDLER = CommandHandler("listblue", bluetext_ignore_list)
CLEAN_BLUE_TEXT_HANDLER = MessageHandler(Filters.command & Filters.group,
                                         clean_blue_text_must_click)

dispatcher.add_handler(SET_CLEAN_BLUE_TEXT_HANDLER)
dispatcher.add_handler(ADD_CLEAN_BLUE_TEXT_HANDLER)
dispatcher.add_handler(REMOVE_CLEAN_BLUE_TEXT_HANDLER)
dispatcher.add_handler(ADD_CLEAN_BLUE_TEXT_GLOBAL_HANDLER)
dispatcher.add_handler(REMOVE_CLEAN_BLUE_TEXT_GLOBAL_HANDLER)
dispatcher.add_handler(LIST_CLEAN_BLUE_TEXT_HANDLER)
dispatcher.add_handler(CLEAN_BLUE_TEXT_HANDLER, BLUE_TEXT_CLEAN_GROUP)

__mod_name__ = "🚯Bluetext Təmizləyici"
__handlers__ = [
    SET_CLEAN_BLUE_TEXT_HANDLER, ADD_CLEAN_BLUE_TEXT_HANDLER,
    REMOVE_CLEAN_BLUE_TEXT_HANDLER, ADD_CLEAN_BLUE_TEXT_GLOBAL_HANDLER,
    REMOVE_CLEAN_BLUE_TEXT_GLOBAL_HANDLER, LIST_CLEAN_BLUE_TEXT_HANDLER,
    (CLEAN_BLUE_TEXT_HANDLER, BLUE_TEXT_CLEAN_GROUP)
]
