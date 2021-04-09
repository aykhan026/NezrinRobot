import re, ast
from io import BytesIO
import random
from typing import Optional

import SaitamaRobot.modules.sql.notes_sql as sql
from SaitamaRobot import LOGGER, JOIN_LOGGER, SUPPORT_CHAT, dispatcher, DRAGONS
from SaitamaRobot.modules.disable import DisableAbleCommandHandler
from SaitamaRobot.modules.helper_funcs.handlers import MessageHandlerChecker
from SaitamaRobot.modules.helper_funcs.chat_status import user_admin, connection_status
from SaitamaRobot.modules.helper_funcs.misc import (build_keyboard,
                                                    revert_buttons)
from SaitamaRobot.modules.helper_funcs.msg_types import get_note_type
from SaitamaRobot.modules.helper_funcs.string_handling import escape_invalid_curly_brackets
from telegram import (MAX_MESSAGE_LENGTH, InlineKeyboardMarkup, Message,
                      ParseMode, Update, InlineKeyboardButton)
from telegram.error import BadRequest
from telegram.utils.helpers import escape_markdown, mention_markdown
from telegram.ext import (CallbackContext, CommandHandler, CallbackQueryHandler,
                          Filters, MessageHandler)
from telegram.ext.dispatcher import run_async

FILE_MATCHER = re.compile(r"^###file_id(!photo)?###:(.*?)(?:\s|$)")
STICKER_MATCHER = re.compile(r"^###sticker(!photo)?###:")
BUTTON_MATCHER = re.compile(r"^###button(!photo)?###:(.*?)(?:\s|$)")
MYFILE_MATCHER = re.compile(r"^###file(!photo)?###:")
MYPHOTO_MATCHER = re.compile(r"^###photo(!photo)?###:")
MYAUDIO_MATCHER = re.compile(r"^###audio(!photo)?###:")
MYVOICE_MATCHER = re.compile(r"^###voice(!photo)?###:")
MYVIDEO_MATCHER = re.compile(r"^###video(!photo)?###:")
MYVIDEONOTE_MATCHER = re.compile(r"^###video_note(!photo)?###:")

ENUM_FUNC_MAP = {
    sql.Types.TEXT.value: dispatcher.bot.send_message,
    sql.Types.BUTTON_TEXT.value: dispatcher.bot.send_message,
    sql.Types.STICKER.value: dispatcher.bot.send_sticker,
    sql.Types.DOCUMENT.value: dispatcher.bot.send_document,
    sql.Types.PHOTO.value: dispatcher.bot.send_photo,
    sql.Types.AUDIO.value: dispatcher.bot.send_audio,
    sql.Types.VOICE.value: dispatcher.bot.send_voice,
    sql.Types.VIDEO.value: dispatcher.bot.send_video
}


# Do not async
@connection_status
def get(update, context, notename, show_none=True, no_format=False):
    bot = context.bot
    chat_id = update.effective_chat.id
    note = sql.get_note(chat_id, notename)
    message = update.effective_message  # type: Optional[Message]

    if note:
        if MessageHandlerChecker.check_user(update.effective_user.id):
            return
        # If we're replying to a message, reply to that message (unless it's an error)
        if message.reply_to_message:
            reply_id = message.reply_to_message.message_id
        else:
            reply_id = message.message_id
        if note.is_reply:
            if JOIN_LOGGER:
                try:
                    bot.forward_message(
                        chat_id=chat_id,
                        from_chat_id=JOIN_LOGGER,
                        message_id=note.value)
                except BadRequest as excp:
                    if excp.message == "Message to forward not found":
                        message.reply_text(
                            "Bu mesaj itib - Bu notu "
                            "siyahıdan silirəm.")
                        sql.rm_note(chat_id, notename)
                    else:
                        raise
            else:
                try:
                    bot.forward_message(
                        chat_id=chat_id,
                        from_chat_id=chat_id,
                        message_id=note.value)
                except BadRequest as excp:
                    if excp.message == "Message to forward not found":
                        message.reply_text(
                            "Görünür bu notun əsas mesajı silinib. "
                            "Bu notu siyahıdan silirəm.")
                        sql.rm_note(chat_id, notename)
                    else:
                        raise
        else:
            VALID_NOTE_FORMATTERS = [
                'first', 'last', 'fullname', 'username', 'id', 'chatname',
                'mention'
            ]
            valid_format = escape_invalid_curly_brackets(
                note.value, VALID_NOTE_FORMATTERS)
            if valid_format:
                if not no_format:
                    if '%%%' in valid_format:
                        split = valid_format.split('%%%')
                        if all(split):
                            text = random.choice(split)
                        else:
                            text = valid_format
                    else:
                        text = valid_format
                else:
                    text = valid_format
                text = text.format(
                    first=escape_markdown(message.from_user.first_name),
                    last=escape_markdown(message.from_user.last_name or
                                         message.from_user.first_name),
                    fullname=escape_markdown(
                        " ".join([
                            message.from_user.first_name, message.from_user
                            .last_name
                        ] if message.from_user.last_name else
                                 [message.from_user.first_name])),
                    username="@" + message.from_user.username
                    if message.from_user.username else mention_markdown(
                        message.from_user.id, message.from_user.first_name),
                    mention=mention_markdown(message.from_user.id,
                                             message.from_user.first_name),
                    chatname=escape_markdown(
                        message.chat.title if message.chat.type != "private"
                        else message.from_user.first_name),
                    id=message.from_user.id)
            else:
                text = ""

            keyb = []
            parseMode = ParseMode.MARKDOWN
            buttons = sql.get_buttons(chat_id, notename)
            if no_format:
                parseMode = None
                text += revert_buttons(buttons)
            else:
                keyb = build_keyboard(buttons)

            keyboard = InlineKeyboardMarkup(keyb)

            try:
                if note.msgtype in (sql.Types.BUTTON_TEXT, sql.Types.TEXT):
                    bot.send_message(
                        chat_id,
                        text,
                        reply_to_message_id=reply_id,
                        parse_mode=parseMode,
                        disable_web_page_preview=True,
                        reply_markup=keyboard)
                else:
                    ENUM_FUNC_MAP[note.msgtype](
                        chat_id,
                        note.file,
                        caption=text,
                        reply_to_message_id=reply_id,
                        parse_mode=parseMode,
                        disable_web_page_preview=True,
                        reply_markup=keyboard)

            except BadRequest as excp:
                if excp.message == "Entity_mention_user_invalid":
                    message.reply_text(
                        "Görünür ki sən mənim heç vaxt görmədiyim birini tag etməyə çalışırsan! Onun bir mesajını yönləndirsən bunu edə bilərəm.")
                elif FILE_MATCHER.match(note.value):
                    message.reply_text(
                        "Bu not başqa bir botdan səhvən gətirilmiş bir fayldır - Mən onu "
                        "istifadə edə bilmərəm. Mən bunu notlar siyahısından siləcəm.")
                    sql.rm_note(chat_id, notename)
                else:
                    message.reply_text(
                        "Bu not səhv formatlandığından yadda saxlanıla bilmədi.Problem davam edərsə "
                        f"@{SUPPORT_CHAT} qrupundan kömək istəyin!")
                    LOGGER.exception("Could not parse message #%s in chat %s",
                                     notename, str(chat_id))
                    LOGGER.warning("Message was: %s", str(note.value))
        return
    elif show_none:
        message.reply_text("Bu not mövcud deyil")


@run_async
@connection_status
def cmd_get(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    if len(args) >= 2 and args[1].lower() == "noformat":
        get(update, context, args[0].lower(), show_none=True, no_format=True)
    elif len(args) >= 1:
        get(update, context, args[0].lower(), show_none=True)
    else:
        update.effective_message.reply_text("Zibili çıxdı")


@run_async
@connection_status
def hash_get(update: Update, context: CallbackContext):
    message = update.effective_message.text
    fst_word = message.split()[0]
    no_hash = fst_word[1:].lower()
    get(update, context, no_hash, show_none=False)


@run_async
@connection_status
def slash_get(update: Update, context: CallbackContext):
    message, chat_id = update.effective_message.text, update.effective_chat.id
    no_slash = message[1:]
    note_list = sql.get_all_chat_notes(chat_id)

    try:
        noteid = note_list[int(no_slash) - 1]
        note_name = str(noteid).strip(">").split()[1]
        get(update, context, note_name, show_none=False)
    except IndexError:
        update.effective_message.reply_text("Xətalı not ID 😾")


@run_async
@user_admin
@connection_status
def save(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    msg = update.effective_message  # type: Optional[Message]

    note_name, text, data_type, content, buttons = get_note_type(msg)
    note_name = note_name.lower()
    if data_type is None:
        msg.reply_text("Qağaş, heç bir not yoxdur")
        return

    sql.add_note_to_db(
        chat_id, note_name, text, data_type, buttons=buttons, file=content)

    msg.reply_text(
        f"`{note_name}` notunu əlavə elədim.\n/get `{note_name}`, və ya `#{note_name}` ilə çağıra bilərsiniz",
        parse_mode=ParseMode.MARKDOWN)

    if msg.reply_to_message and msg.reply_to_message.from_user.is_bot:
        if text:
            msg.reply_text(
                "Bir mesajı botdan saxlamağa çalışdığınıza bənzəyir. Təəssüf ki, botlar bot mesajlarını ötürə bilmir, ona görə də dəqiq mesajı saxlaya bilmirəm, bacardığım bütün mətni saxlayacağam, amma daha çoxunu istəyirsinizsə, mesajı özünüz ötürməlisiniz, sonra da saxlamalısınız.")
        else:
            msg.reply_text(
                "Botlar telegramla əlil olur və botların digər botlarla qarşılıqlı əlaqəsini çətinləşdirir, ona görə də bu mesajı adət etdiyim kimi saxlaya bilmirəm - göndərməyiniz və sonra yeni mesajı yadda saxlamağınız varmı? Təşəkkürlər!")
        return


@run_async
@user_admin
@connection_status
def clear(update: Update, context: CallbackContext):
    args = context.args
    chat_id = update.effective_chat.id
    if len(args) >= 1:
        notename = args[0].lower()

        if sql.rm_note(chat_id, notename):
            update.effective_message.reply_text("Not uğurla silindi.")
        else:
            update.effective_message.reply_text(
                "Belə bir not mövcud deyil!")


@run_async
def clearall(update: Update, context: CallbackContext):
    chat = update.effective_chat
    user = update.effective_user
    member = chat.get_member(user.id)
    if member.status != "creator" and user.id not in DRAGONS:
        update.effective_message.reply_text(
            "Yalnız qrup sahibi bütün notları silə bilər.")
    else:
        buttons = InlineKeyboardMarkup([[
            InlineKeyboardButton(
                text="Bütün notları sil", callback_data="notes_rmall")
        ], [InlineKeyboardButton(text="Ləğv et", callback_data="notes_cancel")]])
        update.effective_message.reply_text(
            f"{chat.title} qrupundakı bütün notları silmək istədiyindən əminsən? Bu proses geri qaytarıla bilməz.",
            reply_markup=buttons,
            parse_mode=ParseMode.MARKDOWN)


@run_async
def clearall_btn(update: Update, context: CallbackContext):
    query = update.callback_query
    chat = update.effective_chat
    message = update.effective_message
    member = chat.get_member(query.from_user.id)
    if query.data == 'notes_rmall':
        if member.status == "creator" or query.from_user.id in DRAGONS:
            note_list = sql.get_all_chat_notes(chat.id)
            try:
                for notename in note_list:
                    note = notename.name.lower()
                    sql.rm_note(chat.id, note)
                message.edit_text("Bütün notlar silindi.")
            except BadRequest:
                return

        if member.status == "administrator":
            query.answer("Bunu yalnız qrup sahibi edə bilər.")

        if member.status == "member":
            query.answer("Əvvəlcə qrupda admin olmalısan.")
    elif query.data == 'notes_cancel':
        if member.status == "creator" or query.from_user.id in DRAGONS:
            message.edit_text("Bütün notların silinməsi ləğv olundu.")
            return
        if member.status == "administrator":
            query.answer("Bunu yalnız qrup sahibi edə bilər.")
        if member.status == "member":
            query.answer("Əvvəlcə qrupda admin olmalısan.")


@run_async
@connection_status
def list_notes(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    note_list = sql.get_all_chat_notes(chat_id)
    notes = len(note_list) + 1
    msg = "Notları `/notsayi` və ya `#notadi` çağıra bilərsiniz \n\n  *ID*    *Note* \n"
    for note_id, note in zip(range(1, notes), note_list):
        if note_id < 10:
            note_name = f"`{note_id:2}.`  `#{(note.name.lower())}`\n"
        else:
            note_name = f"`{note_id}.`  `#{(note.name.lower())}`\n"
        if len(msg) + len(note_name) > MAX_MESSAGE_LENGTH:
            update.effective_message.reply_text(
                msg, parse_mode=ParseMode.MARKDOWN)
            msg = ""
        msg += note_name

    if not note_list:
        update.effective_message.reply_text("Bu qrupda not yoxdur!")

    elif len(msg) != 0:
        update.effective_message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)


def __import_data__(chat_id, data):
    failures = []
    for notename, notedata in data.get("extra", {}).items():
        match = FILE_MATCHER.match(notedata)
        matchsticker = STICKER_MATCHER.match(notedata)
        matchbtn = BUTTON_MATCHER.match(notedata)
        matchfile = MYFILE_MATCHER.match(notedata)
        matchphoto = MYPHOTO_MATCHER.match(notedata)
        matchaudio = MYAUDIO_MATCHER.match(notedata)
        matchvoice = MYVOICE_MATCHER.match(notedata)
        matchvideo = MYVIDEO_MATCHER.match(notedata)
        matchvn = MYVIDEONOTE_MATCHER.match(notedata)

        if match:
            failures.append(notename)
            notedata = notedata[match.end():].strip()
            if notedata:
                sql.add_note_to_db(chat_id, notename[1:], notedata,
                                   sql.Types.TEXT)
        elif matchsticker:
            content = notedata[matchsticker.end():].strip()
            if content:
                sql.add_note_to_db(
                    chat_id,
                    notename[1:],
                    notedata,
                    sql.Types.STICKER,
                    file=content)
        elif matchbtn:
            parse = notedata[matchbtn.end():].strip()
            notedata = parse.split("<###button###>")[0]
            buttons = parse.split("<###button###>")[1]
            buttons = ast.literal_eval(buttons)
            if buttons:
                sql.add_note_to_db(
                    chat_id,
                    notename[1:],
                    notedata,
                    sql.Types.BUTTON_TEXT,
                    buttons=buttons,
                )
        elif matchfile:
            file = notedata[matchfile.end():].strip()
            file = file.split("<###TYPESPLIT###>")
            notedata = file[1]
            content = file[0]
            if content:
                sql.add_note_to_db(
                    chat_id,
                    notename[1:],
                    notedata,
                    sql.Types.DOCUMENT,
                    file=content)
        elif matchphoto:
            photo = notedata[matchphoto.end():].strip()
            photo = photo.split("<###TYPESPLIT###>")
            notedata = photo[1]
            content = photo[0]
            if content:
                sql.add_note_to_db(
                    chat_id,
                    notename[1:],
                    notedata,
                    sql.Types.PHOTO,
                    file=content)
        elif matchaudio:
            audio = notedata[matchaudio.end():].strip()
            audio = audio.split("<###TYPESPLIT###>")
            notedata = audio[1]
            content = audio[0]
            if content:
                sql.add_note_to_db(
                    chat_id,
                    notename[1:],
                    notedata,
                    sql.Types.AUDIO,
                    file=content)
        elif matchvoice:
            voice = notedata[matchvoice.end():].strip()
            voice = voice.split("<###TYPESPLIT###>")
            notedata = voice[1]
            content = voice[0]
            if content:
                sql.add_note_to_db(
                    chat_id,
                    notename[1:],
                    notedata,
                    sql.Types.VOICE,
                    file=content)
        elif matchvideo:
            video = notedata[matchvideo.end():].strip()
            video = video.split("<###TYPESPLIT###>")
            notedata = video[1]
            content = video[0]
            if content:
                sql.add_note_to_db(
                    chat_id,
                    notename[1:],
                    notedata,
                    sql.Types.VIDEO,
                    file=content)
        elif matchvn:
            video_note = notedata[matchvn.end():].strip()
            video_note = video_note.split("<###TYPESPLIT###>")
            notedata = video_note[1]
            content = video_note[0]
            if content:
                sql.add_note_to_db(
                    chat_id,
                    notename[1:],
                    notedata,
                    sql.Types.VIDEO_NOTE,
                    file=content)
        else:
            sql.add_note_to_db(chat_id, notename[1:], notedata, sql.Types.TEXT)

    if failures:
        with BytesIO(str.encode("\n".join(failures))) as output:
            output.name = "failed_imports.txt"
            dispatcher.bot.send_document(
                chat_id,
                document=output,
                filename="failed_imports.txt",
                caption="Bu fayllar/.əkillər başqa bir botdan qaynaqlandığına görə idxal edilmədi. Bu telegram API məhdudlaşdırmasıdır və qarşısını almaq mümkün deyil. Narahatlığa görə üzr istəyirik!",
            )


def __stats__():
    return f"• {sql.num_notes()} not, ümumi {sql.num_chats()} qrupda."


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    notes = sql.get_all_chat_notes(chat_id)
    return f"Bu qrupda `{len(notes)}` not var."


__help__ = """
 • `/get <notadı>`*:* notu çağırır
 • `#<notename>`*:* notu çağırır
 • `/notes` və ya `/saved`*:* qrupdakı notları göstərir
 • `/eded` *:* saylı notu çağırır
Əgər notu formtlanmamış vəziyyətdə almaq istəyirsinizsə `/get <notadı> noformat` yazın. 

*Sadəcə adminlər:*
 • `/save <not adı> <not>`*:* notu yadda saxlayır
Buton əlavə etmək üçün isə \
`[yazı](buttonurl:sayt.com)`. Daha çoxu üçün `/markdownhelp` yazın
 • `/save <notadı>`*:* yanıtlanan mesajı not olaraq qeyd edir
 Nota random cavablar üçün `%%%` teması
 *Nümunə:* 
 `/save notadı
 1-ci cavab
 %%%
 2-ci cavab
 %%%
 3-ci cavab`
 • `/clear <notadı>`*:* notu silir
 • `/removeallnotes`*:* bütün notları silir

"""

__mod_name__ = "Notlar"

GET_HANDLER = CommandHandler("get", cmd_get)
HASH_GET_HANDLER = MessageHandler(Filters.regex(r"^#[^\s]+"), hash_get)
SLASH_GET_HANDLER = MessageHandler(Filters.regex(r"^/\d+$"), slash_get)
SAVE_HANDLER = CommandHandler("save", save)
DELETE_HANDLER = CommandHandler("clear", clear)

LIST_HANDLER = DisableAbleCommandHandler(["notes", "saved"],
                                         list_notes,
                                         admin_ok=True)

CLEARALL = DisableAbleCommandHandler("removeallnotes", clearall)
CLEARALL_BTN = CallbackQueryHandler(clearall_btn, pattern=r"notes_.*")

dispatcher.add_handler(GET_HANDLER)
dispatcher.add_handler(SAVE_HANDLER)
dispatcher.add_handler(LIST_HANDLER)
dispatcher.add_handler(DELETE_HANDLER)
dispatcher.add_handler(HASH_GET_HANDLER)
dispatcher.add_handler(SLASH_GET_HANDLER)
dispatcher.add_handler(CLEARALL)
dispatcher.add_handler(CLEARALL_BTN)
