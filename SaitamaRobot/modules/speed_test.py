import speedtest
from SaitamaRobot import DEV_USERS, dispatcher
from SaitamaRobot.modules.disable import DisableAbleCommandHandler
from SaitamaRobot.modules.helper_funcs.chat_status import dev_plus
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, ParseMode,
                      Update)
from telegram.ext import CallbackContext, CallbackQueryHandler, run_async


def convert(speed):
    return round(int(speed) / 1048576, 2)


@dev_plus
@run_async
def speedtestxyz(update: Update, context: CallbackContext):
    buttons = [[
        InlineKeyboardButton("Şəkilli", callback_data="speedtest_image"),
        InlineKeyboardButton("Yazılı", callback_data="speedtest_text")
    ]]
    update.effective_message.reply_text(
        "SpeedTest üçün bir mod seçin", reply_markup=InlineKeyboardMarkup(buttons))


@run_async
def speedtestxyz_callback(update: Update, context: CallbackContext):
    query = update.callback_query

    if query.from_user.id in DEV_USERS:
        msg = update.effective_message.edit_text('SpeedTest edilir....')
        speed = speedtest.Speedtest()
        speed.get_best_server()
        speed.download()
        speed.upload()
        replymsg = 'SpeedTest nəticəsi:'

        if query.data == 'speedtest_image':
            speedtest_image = speed.results.share()
            update.effective_message.reply_photo(
                photo=speedtest_image, caption=replymsg)
            msg.delete()

        elif query.data == 'speedtest_text':
            result = speed.results.dict()
            replymsg += f"\nDownload: `{convert(result['download'])}Mb/s`\nUpload: `{convert(result['upload'])}Mb/s`\nPing: `{result['ping']}`"
            update.effective_message.edit_text(
                replymsg, parse_mode=ParseMode.MARKDOWN)
    else:
        query.answer(
            "Bu əmri işlətmək üçün qəhrəmanlar assosasiyasına qoşulmalısan :D.")


SPEED_TEST_HANDLER = DisableAbleCommandHandler("speedtest", speedtestxyz)
SPEED_TEST_CALLBACKHANDLER = CallbackQueryHandler(
    speedtestxyz_callback, pattern='speedtest_.*')

dispatcher.add_handler(SPEED_TEST_HANDLER)
dispatcher.add_handler(SPEED_TEST_CALLBACKHANDLER)

__mod_name__ = "SpeedTest"
__command_list__ = ["speedtest"]
__handlers__ = [SPEED_TEST_HANDLER, SPEED_TEST_CALLBACKHANDLER]
