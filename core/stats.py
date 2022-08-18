import json
from datetime import datetime
import shutil

import psutil
from typing import List

try:
    from database import AccountEntry
except ImportError:
    from core.database import AccountEntry

try:
    from local_settings import Settings
except ImportError:
    try:
        from settings import Settings
    except ImportError:
        from core.settings import Settings


class Stats:

    class Hiding:

        def __init__(self, user, account, category, url, time_h, time_m, total_packs):
            self.user = user
            self.account = account
            self.category = category
            self.url = url
            self.time_h = time_h
            self.time_m = time_m
            self.packs_completed = 0
            self.total_packs = total_packs

            self.stop = False
            self.blocked = False

    class DelayHiding:

        def __init__(self, user, account: AccountEntry, category, dt: datetime):
            self.user = user
            self.account = account
            self.category = category
            self.dt = dt

    class RandomActivity:

        def __init__(self, account):
            self.account = account
            self.stories = 0
            self.likes = 0

    delay_hidings: List[DelayHiding] = list()

    random_activities = list()
    hidings_in_progress = list()
    hidings_completed = list()

    instruction_seen = dict()
    instruction_category_seen = dict()

    last_account_use = dict()
    hidings_count_by_id = dict()
    hidden_tags = dict()

    # Server
    cpu_percents = list()
    last_save = None
    last_update_bills = None

    @classmethod
    def report(cls, bot, admin_id=None):
        day = datetime.now(tz=Settings.TIMEZONE).day
        month = datetime.now(tz=Settings.TIMEZONE).month

        ids = Settings.ADMIN_IDS
        if admin_id is not None:
            ids = [admin_id]
        cpu_percents = cls.cpu_percents.copy()
        mem_percent = psutil.virtual_memory().percent
        total, used, free = shutil.disk_usage("/")

        date_former = lambda date: date.strftime("%Y-%m-%d %H:%M") if date is not None else ""
        for admin_id in ids:
            bot.send_message(
                chat_id=admin_id,
                text=f"<b>Текущее состояние:</b>\n\n"
                     f"Загрузка процессора - <b>{int(sum(cpu_percents) / len(cpu_percents))}%</b>\n"
                     f"Загрузка ОЗУ - <b>{mem_percent}%</b>\n"
                     f"Загрузка ПЗУ - <b>{int(used * 100 / total)}%</b>\n\n"
                     f"<b>Отчет за {str(day).zfill(2)}.{str(month).zfill(2)}:</b>\n\n"
                     f"Скрытий в работе - <b>{len(cls.hidings_in_progress)}/{Settings.WORKS_LIMIT}</b>\n"
                     f"Всего скрытий - <b>{len(cls.hidings_completed)}</b>\n\n"
                     f"<b>События:</b>\n\n"
                     f"Сейчас - <b>{date_former(datetime.now())}</b>\n"
                     f"Save - <b>{date_former(cls.last_save)}</b>\n"
                     f"Bills update - <b>{date_former(cls.last_update_bills)}</b>\n"
            )

    @classmethod
    def full_report(cls, bot, admin_id=None, username=None, user_id=None):
        day = datetime.now(tz=Settings.TIMEZONE).day
        month = datetime.now(tz=Settings.TIMEZONE).month

        ids = Settings.ADMIN_IDS
        if admin_id is not None:
            ids = [admin_id]

        texts = list()
        count = 0

        text = f"<b>Подробный отчет за {str(day).zfill(2)}.{str(month).zfill(2)}:</b>"
        for hiding in cls.hidings_completed:
            if (username is None and user_id is None) \
                    or username == hiding.account.username or user_id == hiding.user.chat_id:
                hiding_status = ''
                if hiding.stop:
                    hiding_status += '🔴'
                if hiding.blocked:
                    hiding_status += '❌'

                text += f"\n\n<b>{hiding.account.username}</b> ({hiding.user.chat_id}):\n" \
                        f"    <b>{hiding.url}</b>\n" \
                        f"    <b>{hiding.category.name}</b> ({str(hiding.time_h).zfill(2)}:{str(hiding.time_m).zfill(2)}) \n" \
                        f"    <b>{hiding.packs_completed}/{hiding.total_packs}</b> {hiding_status}"
                count += 1
                if count >= 20:
                    texts.append(text)
                    text = ""
                    count = 0
        if text != "":
            texts.append(text)

        for admin_id in ids:
            for text in texts:
                bot.send_message(
                    chat_id=admin_id,
                    text=text
                )

    @classmethod
    def full_progress(cls, bot, admin_id=None, username=None, user_id=None):
        ids = Settings.ADMIN_IDS
        if admin_id is not None:
            ids = [admin_id]

        texts = list()
        count = 0

        text = f"<b>В процессе:</b>"
        if admin_id is not None:
            text = f"<b>Скрытия:</b>"
        for hiding in cls.hidings_in_progress:
            if (username is None and user_id is None) \
                    or username == hiding.account.username or user_id == hiding.user.chat_id:
                text += f"\n\n<b>{hiding.account.username}</b> ({hiding.user.chat_id}):\n" \
                        f"    <b>{hiding.url}</b>\n" \
                        f"    <b>{hiding.category.name}</b> ({str(hiding.time_h).zfill(2)}:{str(hiding.time_m).zfill(2)}) \n" \
                        f"    <b>{hiding.packs_completed}/{hiding.total_packs}</b>"
                count += 1
                if count >= 20:
                    texts.append(text)
                    text = ""
                    count = 0

        if Settings.DELAYED_HIDINGS_ENABLED:
            text += "<b>\n\nОтложенные скрытия:</b>"
            count = 0
            for hiding in cls.delay_hidings:
                if (username is None and user_id is None) \
                        or username == hiding.account.username \
                        or user_id == hiding.user.chat_id:
                    text += f"\n\n<b>{hiding.account.username}</b> ({hiding.user.chat_id}):\n" \
                            f"    <b>{hiding.category.name}</b> ({hiding.dt.strftime('%H:%M %d.%m')})\n"
                    count += 1
                    if count >= 20:
                        texts.append(text)
                        text = ""
                        count = 0

        if text != "":
            texts.append(text)

        for admin_id in ids:
            for text in texts:
                bot.send_message(
                    chat_id=admin_id,
                    text=text
                )

    @classmethod
    def random_activities_report(cls, bot, admin_id=None, username=None):
        ids = Settings.ADMIN_IDS
        if admin_id is not None:
            ids = [admin_id]

        texts = list()
        count = 0

        text = f"<b>Случайные активности:</b>"
        for ra in cls.random_activities:
            if username is None or username == ra.account.username:
                text += f"<b>{ra.account.username}:</b> {ra.stories}/{ra.likes}\n"
                count += 1
                if count >= 25:
                    texts.append(text)
                    text = ""
                    count = 0
        if text != "":
            texts.append(text)

        for admin_id in ids:
            for text in texts:
                bot.send_message(
                    chat_id=admin_id,
                    text=text
                )

    @classmethod
    def reset(cls):
        cls.random_activities = list()
        cls.hidings_count_by_id = dict()

        cls.instruction_seen = dict()
        cls.instruction_category_seen = dict()

        cls.hidings_completed = list()
        cls.total_hidings = 0

    @classmethod
    def add_hidden_tags(cls, url, tags):
        if cls.hidden_tags.get(url) is None:
            cls.hidden_tags[url] = list()
        cls.hidden_tags[url] += tags
        cls.hidden_tags[url] = cls.hidden_tags[url][-Settings.BUFFER_URLS_SIZE:]

    @classmethod
    def get_date(cls):
        return datetime.now()
