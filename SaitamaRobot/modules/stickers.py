import os
import math
import requests
import urllib.request as urllib
from PIL import Image
from html import escape
from bs4 import BeautifulSoup as bs

from telegram import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram import TelegramError, Update
from telegram.ext import run_async, CallbackContext
from telegram.utils.helpers import mention_html

from SaitamaRobot import dispatcher
from SaitamaRobot.modules.disable import DisableAbleCommandHandler

combot_stickers_url = "https://combot.org/telegram/stickers?q="


@run_async
def stickerid(update: Update, context: CallbackContext):
    msg = update.effective_message
    if msg.reply_to_message and msg.reply_to_message.sticker:
        update.effective_message.reply_text(
            "Salam " +
            f"{mention_html(msg.from_user.id, msg.from_user.first_name)}" +
            ", Yanıt verdiyin stikerin ID :\n <code>" +
            escape(msg.reply_to_message.sticker.file_id) + "</code>",
            parse_mode=ParseMode.HTML,
        )
    else:
        update.effective_message.reply_text(
            "Salam " +
            f"{mention_html(msg.from_user.id, msg.from_user.first_name)}" +
            ", Zəhmət olmasa bir stikerə yanıt ver",
            parse_mode=ParseMode.HTML,
        )


@run_async
def cb_sticker(update: Update, context: CallbackContext):
    msg = update.effective_message
    split = msg.text.split(' ', 1)
    if len(split) == 1:
        msg.reply_text('Axtarışa veriləcək bir ad deməlisən.')
        return
    text = requests.get(combot_stickers_url + split[1]).text
    soup = bs(text, 'lxml')
    results = soup.find_all("a", {'class': "sticker-pack__btn"})
    titles = soup.find_all("div", "sticker-pack__title")
    if not results:
        msg.reply_text('Heç bir nəticə tapılmadı :(.')
        return
    reply = f"*{split[1]}* stiker axtarışının nəticələri:"
    for result, title in zip(results, titles):
        link = result['href']
        reply += f"\n• [{title.get_text()}]({link})"
    msg.reply_text(reply, parse_mode=ParseMode.MARKDOWN)


def getsticker(update: Update, context: CallbackContext):
    bot = context.bot
    msg = update.effective_message
    chat_id = update.effective_chat.id
    if msg.reply_to_message and msg.reply_to_message.sticker:
        file_id = msg.reply_to_message.sticker.file_id
        new_file = bot.get_file(file_id)
        new_file.download("sticker.png")
        bot.send_document(chat_id, document=open("sticker.png", "rb"))
        os.remove("sticker.png")
    else:
        update.effective_message.reply_text(
            "Bir stikerə yanıt ver.")


@run_async
def kang(update: Update, context: CallbackContext):
    msg = update.effective_message
    user = update.effective_user
    args = context.args
    packnum = 0
    packname = "a" + str(user.id) + "_by_" + context.bot.username
    packname_found = 0
    max_stickers = 120
    while packname_found == 0:
        try:
            stickerset = context.bot.get_sticker_set(packname)
            if len(stickerset.stickers) >= max_stickers:
                packnum += 1
                packname = ("a" + str(packnum) + "_" + str(user.id) + "_by_" +
                            context.bot.username)
            else:
                packname_found = 1
        except TelegramError as e:
            if e.message == "Stickerset_invalid":
                packname_found = 1
    kangsticker = "kangsticker.png"
    is_animated = False
    file_id = ""

    if msg.reply_to_message:
        if msg.reply_to_message.sticker:
            if msg.reply_to_message.sticker.is_animated:
                is_animated = True
            file_id = msg.reply_to_message.sticker.file_id

        elif msg.reply_to_message.photo:
            file_id = msg.reply_to_message.photo[-1].file_id
        elif msg.reply_to_message.document:
            file_id = msg.reply_to_message.document.file_id
        else:
            msg.reply_text("Yox, bunu paketə əlavə edə bilmirəm.")

        kang_file = context.bot.get_file(file_id)
        if not is_animated:
            kang_file.download("kangsticker.png")
        else:
            kang_file.download("kangsticker.tgs")

        if args:
            sticker_emoji = str(args[0])
        elif msg.reply_to_message.sticker and msg.reply_to_message.sticker.emoji:
            sticker_emoji = msg.reply_to_message.sticker.emoji
        else:
            sticker_emoji = "😳"

        if not is_animated:
            try:
                im = Image.open(kangsticker)
                maxsize = (512, 512)
                if (im.width and im.height) < 512:
                    size1 = im.width
                    size2 = im.height
                    if im.width > im.height:
                        scale = 512 / size1
                        size1new = 512
                        size2new = size2 * scale
                    else:
                        scale = 512 / size2
                        size1new = size1 * scale
                        size2new = 512
                    size1new = math.floor(size1new)
                    size2new = math.floor(size2new)
                    sizenew = (size1new, size2new)
                    im = im.resize(sizenew)
                else:
                    im.thumbnail(maxsize)
                if not msg.reply_to_message.sticker:
                    im.save(kangsticker, "PNG")
                context.bot.add_sticker_to_set(
                    user_id=user.id,
                    name=packname,
                    png_sticker=open("kangsticker.png", "rb"),
                    emojis=sticker_emoji,
                )
                msg.reply_text(
                    f"Stiker paketə əlavə olundu. Paket [burada](t.me/addstickers/{packname}) tapıla bilər"
                    + f"\nEmoji: {sticker_emoji}",
                    parse_mode=ParseMode.MARKDOWN,
                )

            except OSError as e:
                msg.reply_text("Mən yalnız stiker və şəkilləri paketə əlavə edə bilərəm.")
                print(e)
                return

            except TelegramError as e:
                if e.message == "Stickerset_invalid":
                    makepack_internal(
                        update,
                        context,
                        msg,
                        user,
                        sticker_emoji,
                        packname,
                        packnum,
                        png_sticker=open("kangsticker.png", "rb"),
                    )
                elif e.message == "Sticker_png_dimensions":
                    im.save(kangsticker, "PNG")
                    context.bot.add_sticker_to_set(
                        user_id=user.id,
                        name=packname,
                        png_sticker=open("kangsticker.png", "rb"),
                        emojis=sticker_emoji,
                    )
                    msg.reply_text(
                        f"Stiker paketə əlavə olundu. Paket [burada](t.me/addstickers/{packname}) tapıla bilər"
                        + f"\nEmoji: {sticker_emoji}",
                        parse_mode=ParseMode.MARKDOWN,
                    )
                elif e.message == "Invalid sticker emojis":
                    msg.reply_text("Invalid emoji(s).")
                elif e.message == "Stickers_too_much":
                    msg.reply_text(
                        "Stiker limitinə çatıldı😔.")
                elif e.message == "Internal Server Error: sticker set not found (500)":
                    msg.reply_text(
                        "Stiker paketə əlavə olundu. Paket [burada](t.me/addstickers/%s) tapıla bilər"
                        % packname + "\n"
                        "Emoji:" + " " + sticker_emoji,
                        parse_mode=ParseMode.MARKDOWN,
                    )
                print(e)

        else:
            packname = "animated" + str(user.id) + "_by_" + context.bot.username
            packname_found = 0
            max_stickers = 50
            while packname_found == 0:
                try:
                    stickerset = context.bot.get_sticker_set(packname)
                    if len(stickerset.stickers) >= max_stickers:
                        packnum += 1
                        packname = ("animated" + str(packnum) + "_" +
                                    str(user.id) + "_by_" +
                                    context.bot.username)
                    else:
                        packname_found = 1
                except TelegramError as e:
                    if e.message == "Stickerset_invalid":
                        packname_found = 1
            try:
                context.bot.add_sticker_to_set(
                    user_id=user.id,
                    name=packname,
                    tgs_sticker=open("kangsticker.tgs", "rb"),
                    emojis=sticker_emoji,
                )
                msg.reply_text(
                    f"Stiker paketə əlavə olundu. Paket [burada](t.me/addstickers/{packname}) tapıla bilər"
                    + f"\nEmoji: {sticker_emoji}",
                    parse_mode=ParseMode.MARKDOWN,
                )
            except TelegramError as e:
                if e.message == "Stickerset_invalid":
                    makepack_internal(
                        update,
                        context,
                        msg,
                        user,
                        sticker_emoji,
                        packname,
                        packnum,
                        tgs_sticker=open("kangsticker.tgs", "rb"),
                    )
                elif e.message == "Invalid sticker emojis":
                    msg.reply_text("Xətalı emoji.")
                elif e.message == "Internal Server Error: sticker set not found (500)":
                    msg.reply_text(
                        "Stiker paketə əlavə olundu. Paket [burada](t.me/addstickers/%s) tapıla bilər"
                        % packname + "\n"
                        "Emoji:" + " " + sticker_emoji,
                        parse_mode=ParseMode.MARKDOWN,
                    )
                print(e)

    elif args:
        try:
            try:
                urlemoji = msg.text.split(" ")
                png_sticker = urlemoji[1]
                sticker_emoji = urlemoji[2]
            except IndexError:
                sticker_emoji = "😳"
            urllib.urlretrieve(png_sticker, kangsticker)
            im = Image.open(kangsticker)
            maxsize = (512, 512)
            if (im.width and im.height) < 512:
                size1 = im.width
                size2 = im.height
                if im.width > im.height:
                    scale = 512 / size1
                    size1new = 512
                    size2new = size2 * scale
                else:
                    scale = 512 / size2
                    size1new = size1 * scale
                    size2new = 512
                size1new = math.floor(size1new)
                size2new = math.floor(size2new)
                sizenew = (size1new, size2new)
                im = im.resize(sizenew)
            else:
                im.thumbnail(maxsize)
            im.save(kangsticker, "PNG")
            msg.reply_photo(photo=open("kangsticker.png", "rb"))
            context.bot.add_sticker_to_set(
                user_id=user.id,
                name=packname,
                png_sticker=open("kangsticker.png", "rb"),
                emojis=sticker_emoji,
            )
            msg.reply_text(
                f"Stiker paketə əlavə olundu. Paket [burada](t.me/addstickers/{packname}) tapıla bilər"
                + f"\nEmoji: {sticker_emoji}",
                parse_mode=ParseMode.MARKDOWN,
            )
        except OSError as e:
            msg.reply_text("Mən yalnız şəkil və stikerləri paketə əlavə edə bilərəm.")
            print(e)
            return
        except TelegramError as e:
            if e.message == "Stickerset_invalid":
                makepack_internal(
                    update,
                    context,
                    msg,
                    user,
                    sticker_emoji,
                    packname,
                    packnum,
                    png_sticker=open("kangsticker.png", "rb"),
                )
            elif e.message == "Sticker_png_dimensions":
                im.save(kangsticker, "PNG")
                context.bot.add_sticker_to_set(
                    user_id=user.id,
                    name=packname,
                    png_sticker=open("kangsticker.png", "rb"),
                    emojis=sticker_emoji,
                )
                msg.reply_text(
                    "Stiker paketə əlavə olundu. Paket [burada](t.me/addstickers/%s) tapıla bilər"
                    % packname + "\n" + "Emoji:" + " " + sticker_emoji,
                    parse_mode=ParseMode.MARKDOWN,
                )
            elif e.message == "Invalid sticker emojis":
                msg.reply_text("Xətalı emoji.")
            elif e.message == "Stickers_too_much":
                msg.reply_text("Stiker limitinə çatıldı.")
            elif e.message == "Internal Server Error: sticker set not found (500)":
                msg.reply_text(
                    "Stiker paketə əlavə olundu. Paket [burada](t.me/addstickers/%s) tapıla bilər"
                    % packname + "\n"
                    "Emoji:" + " " + sticker_emoji,
                    parse_mode=ParseMode.MARKDOWN,
                )
            print(e)
    else:
        packs = "Zəhmət olmasa bir şəkil və ya stikerə yanıt ver!\nOh yeri gəlmişkən aşağıdakılar sənin paketlərindir:\n"
        if packnum > 0:
            firstpackname = "a" + str(user.id) + "_by_" + context.bot.username
            for i in range(0, packnum + 1):
                if i == 0:
                    packs += f"[paket](t.me/addstickers/{firstpackname})\n"
                else:
                    packs += f"[paket{i}](t.me/addstickers/{packname})\n"
        else:
            packs += f"[paket](t.me/addstickers/{packname})"
        msg.reply_text(packs, parse_mode=ParseMode.MARKDOWN)
    if os.path.isfile("kangsticker.png"):
        os.remove("kangsticker.png")
    elif os.path.isfile("kangsticker.tgs"):
        os.remove("kangsticker.tgs")


def makepack_internal(
    update,
    context,
    msg,
    user,
    emoji,
    packname,
    packnum,
    png_sticker=None,
    tgs_sticker=None,
):
    name = user.first_name
    name = name[:50]
    try:
        extra_version = ""
        if packnum > 0:
            extra_version = " " + str(packnum)
        if png_sticker:
            success = context.bot.create_new_sticker_set(
                user.id,
                packname,
                f"{name}'s pack" + extra_version,
                png_sticker=png_sticker,
                emojis=emoji,
            )
        if tgs_sticker:
            success = context.bot.create_new_sticker_set(
                user.id,
                packname,
                f"{name}'s animated pack" + extra_version,
                tgs_sticker=tgs_sticker,
                emojis=emoji,
            )

    except TelegramError as e:
        print(e)
        if e.message == "Sticker set name is already occupied":
            msg.reply_text(
                "Paket [burada](t.me/addstickers/%s) tapıla bilər" % packname,
                parse_mode=ParseMode.MARKDOWN,
            )
        elif e.message in ("Peer_id_invalid", "bot was blocked by the user"):
            msg.reply_text(
                "İlk öncə mənimlə PM-də əlaqəyə keç.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(
                        text="Start", url=f"t.me/{context.bot.username}")
                ]]),
            )
        elif e.message == "Internal Server Error: created sticker set not found (500)":
            msg.reply_text(
                "Stiker paketi uğurla yaradıldı. Paket [burada](t.me/addstickers/%s) tapıla bilər"
                % packname,
                parse_mode=ParseMode.MARKDOWN,
            )
        return

    if success:
        msg.reply_text(
            "Stiker paketi uğurla yaradıldı. Paket [burada](t.me/addstickers/%s) tapıla bilər"
            % packname,
            parse_mode=ParseMode.MARKDOWN,
        )
    else:
        msg.reply_text(
            "Stiker paketi yaradıla bilmədi.")


__help__ = """
• `/stickerid`*:* yanıt verilən stikerin ID göstərir.
• `/getsticker`*:* yanıt verilən stikeri png formatında atır.
• `/stik`*:* yanıt verilən şəkil və ya stikeri paketə əlavə edir.
• `/stickers <paket_adı>`*:* stiker paketi axtarışı edir
"""

__mod_name__ = "Stickers"
STICKERID_HANDLER = DisableAbleCommandHandler("stickerid", stickerid)
GETSTICKER_HANDLER = DisableAbleCommandHandler("getsticker", getsticker)
KANG_HANDLER = DisableAbleCommandHandler("stik", kang, admin_ok=True)
STICKERS_HANDLER = DisableAbleCommandHandler("stickers", cb_sticker)

dispatcher.add_handler(STICKERS_HANDLER)
dispatcher.add_handler(STICKERID_HANDLER)
dispatcher.add_handler(GETSTICKER_HANDLER)
dispatcher.add_handler(KANG_HANDLER)
