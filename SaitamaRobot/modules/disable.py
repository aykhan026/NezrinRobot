import importlib
from typing import Union

from future.utils import string_types
from SaitamaRobot import dispatcher
from SaitamaRobot.modules.helper_funcs.handlers import (CMD_STARTERS,
                                                        SpamChecker)
from SaitamaRobot.modules.helper_funcs.misc import is_module_loaded
from telegram import ParseMode, Update
from telegram.ext import (CallbackContext, CommandHandler, Filters,
                          MessageHandler, RegexHandler)
from telegram.utils.helpers import escape_markdown

FILENAME = __name__.rsplit(".", 1)[-1]

# If module is due to be loaded, then setup all the magical handlers
if is_module_loaded(FILENAME):

    from SaitamaRobot.modules.helper_funcs.chat_status import (
        connection_status, is_user_admin, user_admin)
    from SaitamaRobot.modules.sql import disable_sql as sql
    from telegram.ext.dispatcher import run_async

    DISABLE_CMDS = []
    DISABLE_OTHER = []
    ADMIN_CMDS = []

    class DisableAbleCommandHandler(CommandHandler):

        def __init__(self, command, callback, admin_ok=False, **kwargs):
            super().__init__(command, callback, **kwargs)
            self.admin_ok = admin_ok
            if isinstance(command, string_types):
                DISABLE_CMDS.append(command)
                if admin_ok:
                    ADMIN_CMDS.append(command)
            else:
                DISABLE_CMDS.extend(command)
                if admin_ok:
                    ADMIN_CMDS.extend(command)

        def check_update(self, update):
            if isinstance(update, Update) and update.effective_message:
                message = update.effective_message

                if message.text and len(message.text) > 1:
                    fst_word = message.text.split(None, 1)[0]
                    if len(fst_word) > 1 and any(
                            fst_word.startswith(start)
                            for start in CMD_STARTERS):
                        args = message.text.split()[1:]
                        command = fst_word[1:].split("@")
                        command.append(message.bot.username)

                        if not (command[0].lower() in self.command and
                                command[1].lower()
                                == message.bot.username.lower()):
                            return None
                        chat = update.effective_chat
                        user = update.effective_user
                        if user.id == 1087968824:
                            user_id = chat.id
                        else:
                            user_id = user.id
                        if SpamChecker.check_user(user_id):
                            return None
                        filter_result = self.filters(update)
                        if filter_result:
                            # disabled, admincmd, user admin
                            if sql.is_command_disabled(chat.id,
                                                       command[0].lower()):
                                # check if command was disabled
                                is_disabled = command[
                                    0] in ADMIN_CMDS and is_user_admin(
                                        chat, user.id)
                                if not is_disabled:
                                    return None
                                else:
                                    return args, filter_result

                            return args, filter_result
                        else:
                            return False

    class DisableAbleMessageHandler(MessageHandler):

        def __init__(self, filters, callback, friendly, **kwargs):

            super().__init__(filters, callback, **kwargs)
            DISABLE_OTHER.append(friendly)
            self.friendly = friendly
            if filters:
                self.filters = Filters.update.messages & filters
            else:
                self.filters = Filters.update.messages

        def check_update(self, update):

            chat = update.effective_chat
            message = update.effective_message
            filter_result = self.filters(update)

            try:
                args = message.text.split()[1:]
            except:
                args = []

            if super().check_update(update):
                if sql.is_command_disabled(chat.id, self.friendly):
                    return False
                else:
                    return args, filter_result

    class DisableAbleRegexHandler(RegexHandler):

        def __init__(self,
                     pattern,
                     callback,
                     friendly="",
                     filters=None,
                     **kwargs):
            super().__init__(pattern, callback, filters, **kwargs)
            DISABLE_OTHER.append(friendly)
            self.friendly = friendly

        def check_update(self, update):
            chat = update.effective_chat
            if super().check_update(update):
                if sql.is_command_disabled(chat.id, self.friendly):
                    return False
                else:
                    return True

    @run_async
    @connection_status
    @user_admin
    def disable(update: Update, context: CallbackContext):
        args = context.args
        chat = update.effective_chat
        if len(args) >= 1:
            disable_cmd = args[0]
            if disable_cmd.startswith(CMD_STARTERS):
                disable_cmd = disable_cmd[1:]

            if disable_cmd in set(DISABLE_CMDS + DISABLE_OTHER):
                sql.disable_command(chat.id, str(disable_cmd).lower())
                update.effective_message.reply_text(
                    f"`{disable_cmd}` istifadəsi deaktiv edildi",
                    parse_mode=ParseMode.MARKDOWN)
            else:
                update.effective_message.reply_text(
                    "Bu əmr deaktiv edilə bilməz")

        else:
            update.effective_message.reply_text("Nəyi deaktiv etməliyəmki?")

    @run_async
    @connection_status
    @user_admin
    def disable_module(update: Update, context: CallbackContext):
        args = context.args
        chat = update.effective_chat
        if len(args) >= 1:
            disable_module = "SaitamaRobot.modules." + args[0].rsplit(".", 1)[0]

            try:
                module = importlib.import_module(disable_module)
            except:
                update.effective_message.reply_text(
                    "Belə bir əmr mövcud idi?")
                return

            try:
                command_list = module.__command_list__
            except:
                update.effective_message.reply_text(
                    "Modul içində command list yoxdur!")
                return

            disabled_cmds = []
            failed_disabled_cmds = []

            for disable_cmd in command_list:
                if disable_cmd.startswith(CMD_STARTERS):
                    disable_cmd = disable_cmd[1:]

                if disable_cmd in set(DISABLE_CMDS + DISABLE_OTHER):
                    sql.disable_command(chat.id, str(disable_cmd).lower())
                    disabled_cmds.append(disable_cmd)
                else:
                    failed_disabled_cmds.append(disable_cmd)

            if disabled_cmds:
                disabled_cmds_string = ", ".join(disabled_cmds)
                update.effective_message.reply_text(
                    f"`{disabled_cmds_string}` istifadəsi deaktiv edildi",
                    parse_mode=ParseMode.MARKDOWN)

            if failed_disabled_cmds:
                failed_disabled_cmds_string = ", ".join(failed_disabled_cmds)
                update.effective_message.reply_text(
                    f"`{failed_disabled_cmds_string}` deaktiv edilə bilməz",
                    parse_mode=ParseMode.MARKDOWN)

        else:
            update.effective_message.reply_text("Nəyi deaktiv etməliyəmki?")

    @run_async
    @connection_status
    @user_admin
    def enable(update: Update, context: CallbackContext):
        args = context.args
        chat = update.effective_chat
        if len(args) >= 1:
            enable_cmd = args[0]
            if enable_cmd.startswith(CMD_STARTERS):
                enable_cmd = enable_cmd[1:]

            if sql.enable_command(chat.id, enable_cmd):
                update.effective_message.reply_text(
                    f"`{enable_cmd}` aktiv edildi",
                    parse_mode=ParseMode.MARKDOWN)
            else:
                update.effective_message.reply_text("Bu deaktiv edilmişdiki?")

        else:
            update.effective_message.reply_text("Nəyi aktiv etməliyəm ki?")

    @run_async
    @connection_status
    @user_admin
    def enable_module(update: Update, context: CallbackContext):
        args = context.args
        chat = update.effective_chat

        if len(args) >= 1:
            enable_module = "SaitamaRobot.modules." + args[0].rsplit(".", 1)[0]

            try:
                module = importlib.import_module(enable_module)
            except:
                update.effective_message.reply_text(
                    "Belə bir əmr mövcud idi?")
                return

            try:
                command_list = module.__command_list__
            except:
                update.effective_message.reply_text(
                    "Modulun içində command list yoxdur!")
                return

            enabled_cmds = []
            failed_enabled_cmds = []

            for enable_cmd in command_list:
                if enable_cmd.startswith(CMD_STARTERS):
                    enable_cmd = enable_cmd[1:]

                if sql.enable_command(chat.id, enable_cmd):
                    enabled_cmds.append(enable_cmd)
                else:
                    failed_enabled_cmds.append(enable_cmd)

            if enabled_cmds:
                enabled_cmds_string = ", ".join(enabled_cmds)
                update.effective_message.reply_text(
                    f"`{enabled_cmds_string}` istifadəsi aktiv edildi",
                    parse_mode=ParseMode.MARKDOWN)

            if failed_enabled_cmds:
                failed_enabled_cmds_string = ", ".join(failed_enabled_cmds)
                update.effective_message.reply_text(
                    f"`{failed_enabled_cmds_string}` deaktiv edilmişdi ki?",
                    parse_mode=ParseMode.MARKDOWN)

        else:
            update.effective_message.reply_text("Nəyi altiv etməliyəm ki?")

    @run_async
    @connection_status
    @user_admin
    def list_cmds(update: Update, context: CallbackContext):
        if DISABLE_CMDS + DISABLE_OTHER:
            result = ""
            for cmd in set(DISABLE_CMDS + DISABLE_OTHER):
                result += f" - `{escape_markdown(cmd)}`\n"
            update.effective_message.reply_text(
                f"Aşağıdakı əmrlər dəyişdirilə bilər:\n{result}",
                parse_mode=ParseMode.MARKDOWN)
        else:
            update.effective_message.reply_text("Heç bir əmr deaktiv edilə bilməz.")

    # do not async
    def build_curr_disabled(chat_id: Union[str, int]) -> str:
        disabled = sql.get_all_disabled(chat_id)
        if not disabled:
            return "Heç bir əmr deaktiv edilməyib!"

        result = ""
        for cmd in disabled:
            result += " - `{}`\n".format(escape_markdown(cmd))
        return "Aşağıdakı əmrlər deaktiv edilib:\n{}".format(
            result)

    @run_async
    @connection_status
    def commands(update: Update, context: CallbackContext):
        chat = update.effective_chat
        update.effective_message.reply_text(
            build_curr_disabled(chat.id), parse_mode=ParseMode.MARKDOWN)

    def __stats__():
        return f"• {sql.num_disabled()} əmr deaktiv edilib, ümumi {sql.num_chats()} qrupda."

    def __migrate__(old_chat_id, new_chat_id):
        sql.migrate_chat(old_chat_id, new_chat_id)

    def __chat_settings__(chat_id, user_id):
        return build_curr_disabled(chat_id)

    DISABLE_HANDLER = CommandHandler("disable", disable)
    DISABLE_MODULE_HANDLER = CommandHandler("disablemodule", disable_module)
    ENABLE_HANDLER = CommandHandler("enable", enable)
    ENABLE_MODULE_HANDLER = CommandHandler("enablemodule", enable_module)
    COMMANDS_HANDLER = CommandHandler(["cmds", "disabled"], commands)
    TOGGLE_HANDLER = CommandHandler("listcmds", list_cmds)

    dispatcher.add_handler(DISABLE_HANDLER)
    dispatcher.add_handler(DISABLE_MODULE_HANDLER)
    dispatcher.add_handler(ENABLE_HANDLER)
    dispatcher.add_handler(ENABLE_MODULE_HANDLER)
    dispatcher.add_handler(COMMANDS_HANDLER)
    dispatcher.add_handler(TOGGLE_HANDLER)

    __help__ = """
    • `/cmds`*:* deaktiv edilmiş əmrləri göstərir

    *Sadəcə adminlər:*
    • `/enable <əmr>`*:* əmri aktiv edir
    • `/disable <əmr>`*:* əmri deaktiv edir
    • `/enablemodule <modul adı>`*:* moduldakı bütün əmrləri aktiv edir
    • `/disablemodule <module name>`*:* moduldakı bütün əmrləri deaktiv edir
    • `/listcmds`*:* dəyişdirlə bilən əmrləri göstərir
    """

    __mod_name__ = "Əmr deaktiv etmək"

else:
    DisableAbleCommandHandler = CommandHandler
    DisableAbleRegexHandler = RegexHandler
    DisableAbleMessageHandler = MessageHandler
