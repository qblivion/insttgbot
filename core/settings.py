from datetime import timezone, timedelta
import os

class Settings:
    print("    core.settings initialized.")

    # Bot settings
    TOKEN = '123123'  # alowator_test_bot

    # DB settings
    DB_NAME = "telegram_bot_instagram_otrabotka"
    DB_HOST = "localhost"
    DB_USER = "alowator"
    DB_PASSWORD = ""

    # Notification settings
    ADMIN_IDS = (366785436, )
    DEBUG_IDS = (366785436, )
    MODERATOR_IDS = ()

    # Referral settings
    REFERRAL_SYSTEM_ENABLED = True
    REFERRAL_AWARD_VALUE = 3
    REFERRAL_AWARD_COEFFICIENT = 0.10
    REFERRER_AWARD_VALUE = 3

    # Payment settings
    PAYMENT_SYSTEM_ENABLED = False
    PAYMENT_API_TOKEN = ""

    HIDINGS_TO_BUY = (
        (1, 15),
        (2, 699),
        (3, 1599),
        (4, 2999),
        (5, 4999)
    )
    BILLS_UPDATE_INTERVAL = 20
    BILLS_UPDATE_RESTART_WATCHDOG = 5 * 60

    # General settings
    DELAYED_HIDINGS_ENABLED = True
    RETURN_HIDING_ENABLED = False # Return hiding to account balance
    RETURN_HIDING_PERCENT = 0.7 # Return hiding if complete less than
    HASHTAGS_COUNT_LIMIT = 4000
    CATEGORIES_COUNT_LIMIT = 20
    ACCOUNTS_COUNT_LIMIT = 100
    MESSAGE_SIZE_LIMIT = 3200
    BUTTON_SIZE_LIMIT = 50

    # Parser settings
    DAY_HIDINGS_LIMIT = 20
    WORKER_ENABLED = True
    WORKS_LIMIT = 5
    SELENIUM_HEADLESS = False
    ACCOUNT_ACTIVITY_REFRESH_TIME = 10 * 60 * 60
    BUFFER_URLS_SIZE = 4000

    COMMENT_HIDING_PACK_SIZE = 28
    COMMENT_HIDING_INTERVAL = 120
    COMMENT_HIDING_BLOCK_SIZE = 25
    COMMENT_HIDING_BLOCK_INTERVAL = 15 * 60

    # System settings
    TIMEZONE = timezone(timedelta(hours=3), "MSK")
    BIN_PATH = f"{os.getcwd()}/core/bin"
    SAVE_PATH = f"{os.getcwd()}/save"
    BROWSER_PROFILES_PATH = f"{os.getcwd()}/profiles"
    REQUIRED_PATHES = (SAVE_PATH, BROWSER_PROFILES_PATH)

    COOKIES_SAVE_PATH = SAVE_PATH + '/cookies.txt'
    HIDDEN_TAGS_SAVE_PATH = SAVE_PATH + '/hidden_tags.txt'
    DELAYED_HIDINGS_SAVE_PATH = SAVE_PATH + '/delayed.txt'
    WEBDRIVER_LOCATION = BIN_PATH + '/chromedriver'
