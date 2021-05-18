import html
import random
import time

from typing import Optional
from telegram import ParseMode, Update, ChatPermissions
from telegram.ext import CallbackContext, run_async
from telegram.error import BadRequest

import SaitamaRobot.modules.aykhan as aykhan



@run_async
def toss(update: Update, context: CallbackContext):
    update.message.reply_text(random.choice(aykhan.TOSS))

@run_async
def toss(update: Update, context: CallbackContext):
    update.message.reply_text(random.choice(aykhan.TOSSS))


__help__ = """
 • `/tosss`*:* Randomly answers yes/no/maybe
 • `/toss`*:* Tosses A coin
"""

TOSSS_HANDLER = DisableAbleCommandHandler("tosss", tosss)
TOSS_HANDLER = DisableAbleCommandHandler("toss", toss)


dispatcher.add_handler(TOSSS_HANDLER)
dispatcher.add_handler(TOSS_HANDLER)

__mod_name__ = "FUN"
__command_list__ = [
    "toss", "tosss",
]
__handlers__ = [
    TOSSS_HANDLER, TOSS_HANDLER
]
