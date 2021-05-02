from telegram.ext import CommandHandler, run_async
from bot import dispatcher, updater, botStartTime
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.message_utils import *
from .helper.telegram_helper.filters import CustomFilters
from .modules import authorize, list

@run_async
def start(update, context):
    LOGGER.info('UID: {} - UN: {} - MSG: {}'.format(update.message.chat.id,update.message.chat.username,update.message.text))
    if update.message.chat.type == "private" :
        sendMessage(f"<b>Hɪ👋</b> <b>{update.message.chat.first_name}</b>. 
<b> I Can Search For Files In DEV CLOUD Database & Return A List Of Matching Files With Google Drive & Index Links.

- Just Send Me The File Name.

I Am Also Usable In Groups Just Add Me In Any Group & Send The Below Format 👇

/search File Name..    </b>", context.bot, update)
    else :
        sendMessage("<b>➼ I'ᴍ Aʟɪᴠᴇ🤭 :)</b>", context.bot, update)

@run_async
def log(update, context):
    sendLogFile(context.bot, update)

def main():

    start_handler = CommandHandler(BotCommands.StartCommand, start, filters=CustomFilters.authorized_chat | CustomFilters.authorized_user)
    log_handler = CommandHandler(BotCommands.LogCommand, log, filters=CustomFilters.owner_filter)

    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(log_handler)

    updater.start_polling()
    LOGGER.info("Yeah I'm running!")
    updater.idle()

main()
