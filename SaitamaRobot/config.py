# Create a new config.py or rename this to config.py file in same dir and import, then extend this class. okey.
import json
import os


sudos = 1801589805
devs = 1801589805
supports = 1801589805
whitelists = 1801589805
tigers = 1801589805
spammers = 1801589805


def get_user_list(config, key):
    with open('{}/SaitamaRobot/{}'.format(os.getcwd(), config),
              'r') as json_file:
        return json.load(json_file)[key]


# Create a new config.py or rename this to config.py file in same dir and import, then extend this class.
class Config(object):
    LOGGER = True
    # REQUIRED
    #Login to https://my.telegram.org and fill in these slots with the details given by it

    API_ID = 4856651  # integer value, dont use ""
    API_HASH = "b8327893a1645fc70085831bd0570b21"
    TOKEN = "1739742678:AAEmlbaghSKVMYX4NUrxPcK_mv7k1hFMbys"  #This var used to be API_KEY but it is now TOKEN, adjust accordingly.
    OWNER_ID = 1727079853  # If you dont know, run the bot and do /id in your private chat with it, also an integer
    OWNER_USERNAME = "aykhan_s"
    SUPPORT_CHAT = 'RoBotlarimTg'  #Your own group for support, do not add the @
    JOIN_LOGGER = -1001456155319  #Prints any new group the bot is added to, prints just the name and ID.
    EVENT_LOGS = -1001456155319  #Prints information like gbans, sudo promotes, AI enabled disable states that may help in debugging and shit

    #RECOMMENDED
    SQLALCHEMY_DATABASE_URI = 'postgres://xgwjridmfebpna:2c8caa89a016e11aacba85822213349c8db16a714cecf8c848f78e96cf4c2892@ec2-54-225-214-37.compute-1.amazonaws.com:5432/dvnfn04k9beug'  # needed for any database modules
    LOAD = []
    NO_LOAD = ['rss', 'cleaner', 'connection', 'math']
    WEBHOOK = False
    INFOPIC = True
    URL = None
    SPAMWATCH_API = ""  # go to support.spamwat.ch to get key
    SPAMWATCH_SUPPORT_CHAT = "@SpamWatchSupport"

    #OPTIONAL
    ##List of id's -  (not usernames) for users which have sudo access to the bot.
    DRAGONS = ('sudos')
    ##List of id's - (not usernames) for developers who will have the same perms as the owner
    DEV_USERS = ('devs')
    ##List of id's (not usernames) for users which are allowed to gban, but can also be banned.
    DEMONS = ('supports')
    #List of id's (not usernames) for users which WONT be banned/kicked by the bot.
    TIGERS = ('tigers')
    WOLVES = ('whitelists')
    DONATION_LINK = None  # EG, paypal
    CERT_PATH = None
    PORT = 5000
    DEL_CMDS = True  #Delete commands that users dont have access to, like delete /ban if a non admin uses it.
    STRICT_GBAN = True
    WORKERS = 8  # Number of subthreads to use. Set as number of threads your processor uses
    BAN_STICKER = 'CAACAgQAAx0CU_rCTAABAczQXyBOv1TsVK4EfwnkCUT1H0GCkPQAAtwAAwEgTQaYsMtAltpEwhoE'  # banhammer marie sticker id, the bot will send this sticker before banning or kicking a user in chat.
    ALLOW_EXCL = True  # Allow ! commands as well as / (Leave this to true so that blacklist can work)
    CASH_API_KEY = 'awoo'  # Get your API key from https://www.alphavantage.co/support/#api-key
    TIME_API_KEY = 'awoo'  # Get your API key from https://timezonedb.com/api
    WALL_API = 'awoo'  #For wallpapers, get one from https://wall.alphacoders.com/api.php
    AI_API_KEY = 'awoo'  #For chatbot, get one from https://coffeehouse.intellivoid.net/dashboard
    BL_CHATS = []  # List of groups that you want blacklisted.
    SPAMMERS = None


class Production(Config):
    LOGGER = True


class Development(Config):
    LOGGER = True
