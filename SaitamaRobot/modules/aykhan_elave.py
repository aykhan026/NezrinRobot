import html
import random
import time

from typing import Optional
from telegram import ParseMode, Update, ChatPermissions
from telegram.ext import CallbackContext, run_async
from tswift import Song
from telegram.error import BadRequest

import MashaRoBot.modules.fun_strings as fun_strings
from MashaRoBot import dispatcher
from MashaRoBot.modules.disable import DisableAbleCommandHandler
from MashaRoBot.modules.helper_funcs.alternate import send_message, typing_action
from MashaRoBot.modules.helper_funcs.chat_status import (is_user_admin)
from MashaRoBot.modules.helper_funcs.extraction import extract_user

@run_async
def toss(update: Update, context: CallbackContext):
    update.message.reply_text(random.choice(fun_strings.TOSS))


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
