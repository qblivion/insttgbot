from datetime import timezone, timedelta
import os

from core.settings import Settings as CoreSettings

class Settings(CoreSettings):
    print("    settings initialized.")
    # Bot settings
    TOKEN = ''  # hide_hashtag_bot
    DB_NAME = "telegram_bot_instagram_otrabotka"

    DELAYED_HIDINGS_ENABLED = True
    RETURN_HIDING_ENABLED = True  # Return hiding to account balance
    RETURN_HIDING_PERCENT = 0.7  # Return hiding if complete less than
    HASHTAGS_COUNT_LIMIT = 50000
    # Notification settings
    ADMIN_IDS = (366785436, 1023204420)
    DEBUG_IDS = (366785436,)
    MODERATOR_IDS = (1023204420,)

    # Referral settings
    REFERRAL_SYSTEM_ENABLED = True
    REFERRAL_AWARD_VALUE = 3
    REFERRAL_AWARD_COEFFICIENT = 0.10
    REFERRER_AWARD_VALUE = 3

    # Payment settings
    PAYMENT_SYSTEM_ENABLED = False
    PAYMENT_API_TOKEN = ""
    HIDINGS_TO_BUY = (
        (5, 399),
        (10, 699),
        (25, 1599),
        (50, 2999),
        (100, 4999)
    )

    # Parser settings
    COMMENT_HIDING_INTERVAL = 135
    COMMENT_HIDING_BLOCK_SIZE = 25
    COMMENT_HIDING_BLOCK_INTERVAL = 15 * 60
    WORKS_LIMIT = 7
