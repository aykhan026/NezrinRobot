from emoji import UNICODE_EMOJI
from google_trans_new import LANGUAGES, google_translator
from telegram import ParseMode, Update
from telegram.ext import CallbackContext, run_async

from SaitamaRobot import dispatcher
from SaitamaRobot.modules.disable import DisableAbleCommandHandler


@run_async
def totranslate(update: Update, context: CallbackContext):
    message = update.effective_message
    problem_lang_code = []
    for key in LANGUAGES:
        if "-" in key:
            problem_lang_code.append(key)

    try:
        if message.reply_to_message:
            args = update.effective_message.text.split(None, 1)
            if message.reply_to_message.text:
                text = message.reply_to_message.text
            elif message.reply_to_message.caption:
                text = message.reply_to_message.caption

            try:
                source_lang = args[1].split(None, 1)[0]
            except (IndexError, AttributeError):
                source_lang = "az"

        else:
            args = update.effective_message.text.split(None, 2)
            text = args[2]
            source_lang = args[1]

        if source_lang.count('-') == 2:
            for lang in problem_lang_code:
                if lang in source_lang:
                    if source_lang.startswith(lang):
                        dest_lang = source_lang.rsplit("-", 1)[1]
                        source_lang = source_lang.rsplit("-", 1)[0]
                    else:
                        dest_lang = source_lang.split("-", 1)[1]
                        source_lang = source_lang.split("-", 1)[0]
        elif source_lang.count('-') == 1:
            for lang in problem_lang_code:
                if lang in source_lang:
                    dest_lang = source_lang
                    source_lang = None
                    break
            if dest_lang is None:
                dest_lang = source_lang.split("-")[1]
                source_lang = source_lang.split("-")[0]
        else:
            dest_lang = source_lang
            source_lang = None

        exclude_list = UNICODE_EMOJI.keys()
        for emoji in exclude_list:
            if emoji in text:
                text = text.replace(emoji, '')

        trl = google_translator()
        if source_lang is None:
            detection = trl.detect(text)
            trans_str = trl.translate(text, lang_tgt=dest_lang)
            return message.reply_text(
                f"`{detection[0]}` dilindən `{dest_lang}` dilinə tərcümə edildi:\n`{trans_str}`",
                parse_mode=ParseMode.MARKDOWN)
        else:
            trans_str = trl.translate(
                text, lang_tgt=dest_lang, lang_src=source_lang)
            message.reply_text(
                f"`{source_lang}` dilindən `{dest_lang}` dilinə tərcümə edildi:\n`{trans_str}`",
                parse_mode=ParseMode.MARKDOWN)

    except IndexError:
        update.effective_message.reply_text(
            "Tərcümə ediləcək mətnə yanıt ver.\n\n"
            "Məsələn: `/tr en-ru` İngilis dilindən Rus dilinə tərcümə edir\n"
            "Və ya: `/tr en` İstənilən mətni İngilis dilinə tərcümə edir.\n"
            "[Dil kodları](t.me/OnePunchSupport/12823)",
            parse_mode="markdown",
            disable_web_page_preview=True)
    except ValueError:
        update.effective_message.reply_text(
            "Dil tapılmadı!")
    else:
        return


__help__ = """
• `/tr` və ya `/tl` (dil kodu) yanıt verilən mesajı tərcümə edir
*Nümunə:* 
  `/tr en`*:* İngilis dilinə tərcümə edir
  `/tr en-ru`*:* İngilis dilindən Rus dilinə tərcümə edir
"""

TRANSLATE_HANDLER = DisableAbleCommandHandler(["tr", "tl"], totranslate)

dispatcher.add_handler(TRANSLATE_HANDLER)

__mod_name__ = "Translator"
__command_list__ = ["tr", "tl"]
__handlers__ = [TRANSLATE_HANDLER]
