from threading import Timer
import requests
import logging
import traceback

try:
    from local_settings import Settings
except ImportError:
    try:
        from settings import Settings
    except ImportError:
        from core.settings import Settings

try:
    from texts import Texts
except ImportError:
    from core.texts import Texts

try:
    from database import Database
except ImportError:
    from core.database import Database

from core.stats import Stats

class Bill:

    def __init__(self, amount, value, payment_url):
        self.amount = amount
        self.value = value
        self.payment_url = payment_url


class PaymentSystem:

    API_TOKEN = Settings.PAYMENT_API_TOKEN

    bot = None

    @classmethod
    def create_bill(cls, user, amount, value):
        if not Settings.PAYMENT_SYSTEM_ENABLED:
            return None

        response = requests.post(
            'https://cardlink.link/api/v1/bill/create',
            headers={'Authorization': f"Bearer {cls.API_TOKEN}"},
            params={'amount': amount}
        )
        response_json = response.json()
        if response_json['success']:
            Database.Bills.create_bill(response_json['bill_id'], user.chat_id, amount, value)
            return Bill(amount, value, response_json['link_page_url'])
        else:
            logging.error(f"success = False received in create_bill()\n{response_json}")
            return None

    @classmethod
    def update_bills(cls):
        if not Settings.PAYMENT_SYSTEM_ENABLED:
            return

        response_json = None
        bill_entries = Database.Bills.get_unpaid_bills()
        for bill_entry in bill_entries:
            try:
                response = requests.get(
                    'https://cardlink.link/api/v1/bill/status',
                    headers={'Authorization': f"Bearer {cls.API_TOKEN}"},
                    params={'id': bill_entry.bill_id}
                )
                response_json = response.json()
                if response_json['success']:
                    if response_json['status'] == 'SUCCESS':
                        Database.approve_bill(bill_entry)
                        try:
                            cls.bot.send_message(bill_entry.chat_id, Texts.SUCCESSFUL_PAYMENT_F.format(bill_entry.value))
                        except:
                            cls.__error_handler__("Successful payment notification error")
                else:
                    cls.__error_handler__(f"success = False received in update_bills()", response=response_json)
            except:
                cls.__error_handler__(f"Payment check error()", response=response_json)

        Stats.last_update_bills = Stats.get_date()

    @classmethod
    def updater_start(cls, bot):
        if not Settings.PAYMENT_SYSTEM_ENABLED:
            return

        cls.bot = bot
        cls.set_interval(20, cls.update_bills)

    @classmethod
    def set_interval(cls, timer, task, is_first_run=True):
        if not is_first_run:
            try:
                task()
            except:
                cls.__error_handler__("Error while set_interval")
        Timer(timer, cls.set_interval, [timer, task, False]).start()

    @classmethod
    def __error_handler__(cls, message=None, **kwargs):
        exc_str = None
        try:
            exc_str = traceback.format_exc().lstrip()
            exc_str = f"{message}\n\n" \
                      f"{kwargs}\n\n" \
                      + exc_str
            if cls.bot is not None:
                for chat_id in Settings.DEBUG_IDS:
                    cls.bot.send_message(
                        chat_id=chat_id,
                        text=exc_str
                    )
        except:
            logging.error(str(exc_str))
