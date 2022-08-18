# -*- coding: utf-8 -*-
import html
import json
import sys
import logging
import os
import traceback
from datetime import datetime, timedelta
from threading import Thread

from telegram import (Update, ParseMode)
from telegram.ext import (Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext,
                          Defaults)

from payment_core.payment_system import PaymentSystem

try:
    from local_settings import Settings
except ImportError:
    try:
        from settings import Settings
    except ImportError:
        from core.settings import Settings

try:
    from keyboard import Keyboard, Menu, Buttons
except ImportError:
    from core.keyboard import Keyboard, Menu, Buttons


try:
    from texts import Texts
except ImportError:
    from core.texts import Texts

try:
    from database import Database, CategoryEntry
except ImportError:
    from core.database import Database, CategoryEntry

try:
    from users import Users, Mode, User
except ImportError:
    from core.users import Users, Mode, User

try:
    from worker import Worker, Selenium, Utils
except ImportError:
    from core.worker import Worker, Selenium, Utils

from core.stats import Stats

class AdminHandler:

    @staticmethod
    def info(update: Update, context: CallbackContext):
        chat_id = update.effective_user.id
        if chat_id not in Settings.ADMIN_IDS:
            return

        context.bot.send_message(
            chat_id=chat_id,
            text=f"<b>Admin panel info:</b>\n"
                 f"<b>/ra</b> - случайные активности\n"
                 f"<b>/message (текст)</b> - сообщение всем пользователям\n"
                 f"<b>/users</b> - id пользователей и уровени доступа\n"
                 f"<b>/accounts</b> - все аккаунты\n"
                 f"<b>/proxy</b> - прокси\n"
                 f"<b>/add_proxy (ip) (port) (login) (pass) (дней осталось)</b> - добавить прокси\n"
                 f"<b>/set_proxy (id аккаунта) (id proxy, 0 для удаления прокси)</b> - поставить прокси на аккаунт\n"
                 f"<b>/set_access (id пользователя) (кол-во скрытий)</b> - управление досупом\n"
                 f"<b>/test_bill</b> - тестовая покупка отработок\n"
        )

    @staticmethod
    def report(update: Update, context: CallbackContext):
        chat_id = update.effective_user.id
        if chat_id not in Settings.ADMIN_IDS:
            return

        Stats.report(bot=context.bot, admin_id=chat_id)

    @staticmethod
    def full_report(update: Update, context: CallbackContext):
        chat_id = update.effective_user.id
        if chat_id not in Settings.ADMIN_IDS:
            return

        username = None
        user_id = None
        if context.args is not None and len(context.args) == 1:
            if context.args[0].isnumeric():
                user_id = int(context.args[0])
            else:
                username = context.args[0]

        Stats.full_report(bot=context.bot, admin_id=chat_id, username=username, user_id=user_id)

    @staticmethod
    def full_progress(update: Update, context: CallbackContext):
        chat_id = update.effective_user.id
        if chat_id not in Settings.ADMIN_IDS:
            return

        username = None
        user_id = None
        if context.args is not None and len(context.args) == 1:
            if context.args[0].isnumeric():
                user_id = int(context.args[0])
            else:
                username = context.args[0]

        Stats.full_progress(bot=context.bot, admin_id=chat_id, username=username, user_id=user_id)

    @staticmethod
    def random_activities(update: Update, context: CallbackContext):
        chat_id = update.effective_user.id
        if chat_id not in Settings.ADMIN_IDS:
            return

        username = None
        if len(context.args) == 1:
            username = context.args[0]

        Stats.random_activities_report(bot=context.bot, admin_id=chat_id, username=username)

    @staticmethod
    def users(update: Update, context: CallbackContext):
        chat_id = update.effective_user.id
        if chat_id not in Settings.ADMIN_IDS:
            return

        users = Database.Users.get_users()
        context.bot.send_message(
            chat_id=chat_id,
            text='\n'.join([f"<b>{user.chat_id}</b>: {user.access}" for user in users])
        )

    @staticmethod
    def message(update: Update, context: CallbackContext):
        chat_id = update.effective_user.id
        if chat_id not in Settings.ADMIN_IDS:
            return

        if len(context.args) < 2:
            return

        message_text = ' '.join(context.args)

        print("Sending massages...")
        user_entries = Database.Users.get_users()
        for user_entry in user_entries:
            try:
                context.bot.send_message(
                    chat_id=user_entry.chat_id,
                    text=message_text
                )

            except Exception as exc:
                print(f"    {user_entry.chat_id}: " + str(exc))
        print("Messages sent.")

    @staticmethod
    def set_access(update: Update, context: CallbackContext):
        chat_id = update.effective_user.id
        if chat_id not in Settings.ADMIN_IDS:
            return

        if len(context.args) < 2:
            return

        user_id = int(context.args[0])
        access_level = int(context.args[1])

        Database.Users.set_access(user_id, access_level)
        context.bot.send_message(
            chat_id=chat_id,
            text=f"<b>{user_id}</b> получил уровень доступа <b>{access_level}</b>"
        )

    @staticmethod
    def test_bill(update: Update, context: CallbackContext):
        chat_id = update.effective_user.id
        if chat_id not in Settings.ADMIN_IDS:
            return

        user = Users.get_user(chat_id)
        bill = PaymentSystem.create_bill(user, 20, 10)
        if bill is not None:
            context.bot.send_message(chat_id, bill.payment_url)
        else:
            context.bot.send_message(chat_id, Texts.BILL_CREATE_ERROR)

    @staticmethod
    def update_keyboard(update: Update, context: CallbackContext):
        chat_id = update.effective_user.id
        if chat_id not in Settings.ADMIN_IDS:
            return

        errors = 0
        user_entries = Database.Users.get_users()

        print("Keyboard updating...")
        for user_entry in user_entries:
            try:
                context.bot.send_message(
                    chat_id=user_entry.chat_id,
                    text=f"Обновление клавиатуры",
                    reply_markup=Keyboard.main_menu(
                        is_admin=True if user_entry.chat_id in Settings.ADMIN_IDS else False
                    )
                )
            except Exception as exc:
                errors += 1
                print(f"    {user_entry.chat_id}: " + str(exc))

        context.bot.send_message(
            chat_id=chat_id,
            text=f"Клавиатура обновлена, ошибок - {errors}"
        )
        print("Keyboard updated.")

    @staticmethod
    def add_proxy(update: Update, context: CallbackContext):
        chat_id = update.effective_user.id
        if chat_id not in Settings.ADMIN_IDS:
            return

        try:
            ip = context.args[0]
            port = context.args[1]
            login = context.args[2]
            password = context.args[3]
            days_left = int(context.args[4])
        except:
            update.effective_user.send_message("Некорректные аргументы, см. /info")
            return

        Database.Proxy.add(ip, port, login, password, days_left)

    @staticmethod
    def set_proxy(update: Update, context: CallbackContext):
        chat_id = update.effective_user.id
        if chat_id not in Settings.ADMIN_IDS:
            return

        try:
            account_id = context.args[0]
            proxy_id = context.args[1]
        except:
            update.effective_user.send_message("Некорректные аргументы, см. /info")
            return

        if proxy_id == '0':
            Database.Accounts.set_proxy(account_id, None)
        else:
            Database.Accounts.set_proxy(account_id, proxy_id)

        update.effective_user.send_message("Прокси установлен")

    @staticmethod
    def accounts(update: Update, context: CallbackContext):
        chat_id = update.effective_user.id
        if chat_id not in Settings.ADMIN_IDS:
            return

        accounts = Database.Accounts.get_all()
        accounts.sort(key=lambda x: x.chat_id)

        prev_chat_id = -1
        text = ''
        for account in accounts:
            if account.chat_id != prev_chat_id:
                text += f"\n<b>{account.chat_id}:</b>\n"
            text += f"    <b>{account.account_id}</b> {account.username}\n"

            prev_chat_id = account.chat_id

        if text == '':
            update.effective_user.send_message("Аккаунты отсутствуют")
        else:
            update.effective_user.send_message(text)

    @staticmethod
    def proxy(update: Update, context: CallbackContext):
        chat_id = update.effective_user.id
        if chat_id not in Settings.ADMIN_IDS:
            return

        accounts = Database.Accounts.get_all()
        proxies = Database.Proxy.get_all()

        text = ''
        for proxy in proxies:
            text += f"\n<b>{proxy.id}:</b> {proxy.ip}:{proxy.port} до {proxy.date_end.strftime('%d.%m.%Y')}\n"
            for account in accounts:
                if account.proxy_id == proxy.id:
                    text += f"    <b>{account.account_id}</b> {account.username} ({account.chat_id})\n"

        if text == '':
            update.effective_user.send_message("Прокси отсутствуют")
        else:
            update.effective_user.send_message(text)

    @staticmethod
    def get_browser(update: Update, context: CallbackContext):
        chat_id = update.effective_user.id
        if chat_id not in Settings.ADMIN_IDS:
            return

        try:
            username = context.args[0]
        except:
            update.effective_user.send_message("Некорректные аргументы")
            return

        accounts = Database.Accounts.get_all()
        for account in accounts:
            if account.username.lower() in username.lower():
                Selenium.get_browser(account.username, account.proxy())

    @staticmethod
    def eval(update: Update, context: CallbackContext):
        chat_id = update.effective_user.id
        if chat_id not in Settings.ADMIN_IDS:
            return

        if len(context.args) == 0:
            return

        res = ' '.join(context.args)
        eval(res)

        context.bot.send_message(
            chat_id=chat_id,
            text=f"Evaluated:\n{res}"
        )

    @staticmethod
    def exec(update: Update, context: CallbackContext):
        chat_id = update.effective_user.id
        if chat_id not in Settings.ADMIN_IDS:
            return

        if len(context.args) == 0:
            return

        res = ' '.join(context.args)
        exec(res)

        context.bot.send_message(
            chat_id=chat_id,
            text=f"Executed:\n{res}"
        )


class UserHandler:

    @staticmethod
    def start(update: Update, context: CallbackContext):
        chat_id = update.effective_user.id
        Database.Users.register_user(chat_id)

        context.bot.send_message(
            chat_id=chat_id,
            text=Texts.WELCOME_TEXT,
            reply_markup=Keyboard.main_menu(
                is_admin=True if chat_id in Settings.ADMIN_IDS else False
            )
        )
        if Settings.REFERRAL_SYSTEM_ENABLED:
            context.bot.send_message(
                chat_id=chat_id,
                text=Texts.REFERRAL_WELCOME,
            )

    @staticmethod
    def referral(update: Update, context: CallbackContext):
        if not Settings.REFERRAL_SYSTEM_ENABLED:
            return

        chat_id = update.effective_user.id
        try:
            referral_id = int(context.args[0])
        except:
            return

        is_referral_set = Database.Users.set_referral(chat_id, referral_id)
        if is_referral_set:
            update.effective_user.send_message(text=Texts.REFERRAL_ADDED)
        else:
            update.effective_user.send_message(text=Texts.REFERRAL_NOT_ADDED)

    @staticmethod
    def category_add_dispatcher(bot, user, reply=None, query=None, reset=False):
        if reset:
            user.set_mode(Mode.CATEGORY_ADD, User.CONFIRM)
            query.edit_message_text(text=Texts.CATEGORY_ADD_INSTRUCTION, reply_markup=Keyboard.ok())

        elif user.mode != Mode.CATEGORY_ADD:
            Worker.__error_handler__(message='category_add_dispatcher() called w/o reset')

        elif user.waiting == User.CONFIRM:
            if query is not None and query.data == Buttons.ok.callback:
                query.edit_message_text(text=Texts.ENTER_CAT_NAME)
                user.waiting = User.CAT_NAME

        elif user.waiting == User.CAT_NAME:
            if len(reply) > Settings.BUTTON_SIZE_LIMIT:
                bot.send_message(
                    chat_id=user.chat_id,
                    text=Texts.MESSAGE_TOO_LARGE + '\n' + Texts.ENTER_CAT_NAME,
                )
                return
            user.category = CategoryEntry(chat_id=user.chat_id, name=reply)
            user.waiting = User.VERIFICATION_TAG
            bot.send_message(
                chat_id=user.chat_id,
                text=Texts.ENTER_VERIFICATION_TAG,
                reply_markup=Keyboard.not_use()
            )

        elif user.waiting == User.VERIFICATION_TAG:
            if reply != Buttons.not_use.callback:
                reply = Utils.tag_corrector(reply.replace(' ', ''))
                if Utils.is_correct_tag(reply):
                    user.category.verification_tag = reply
                    Database.Categories.add_category(user.category)
                    user.waiting = User.CAT_HASHTAGS
                    bot.send_message(chat_id=user.chat_id, text=Texts.ENTER_CAT_HASHTAGS)
                else:
                    bot.send_message(
                        chat_id=user.chat_id,
                        text=Texts.UNAVAILABLE_TAGS + '\n' + reply
                    )
                    bot.send_message(
                        chat_id=user.chat_id,
                        text=Texts.ENTER_VERIFICATION_TAG,
                        reply_markup=Keyboard.not_use()
                    )

            else:
                Database.Categories.add_category(user.category)
                query.edit_message_text(text=Texts.ENTER_CAT_HASHTAGS)
                user.waiting = User.CAT_HASHTAGS

        elif user.waiting == User.CAT_HASHTAGS and query is None:
            tags, bad_tags = Utils.extract_tags(reply)
            user.category.add_tags(tags)
            Database.Categories.update_category(user.category)

            if len(bad_tags) > 0:
                bot.send_message(
                    chat_id=user.chat_id,
                    text=Texts.UNAVAILABLE_TAGS + '\n' + ' '.join(bad_tags)
                )
            if len(user.category.tags) >= Settings.HASHTAGS_COUNT_LIMIT:
                bot.send_message(
                    chat_id=user.chat_id,
                    text=Texts.TOO_MANY_TAGS_F.format(Settings.HASHTAGS_COUNT_LIMIT)
                )
                user.clear_mode()
            else:
                bot.send_message(
                    chat_id=user.chat_id,
                    text=Texts.ENTER_CAT_HASHTAGS,
                    reply_markup=Keyboard.category_adding_menu()
                )

        elif user.waiting == User.CAT_HASHTAGS and query.data == Buttons.save_category.callback:
            user.clear_mode()
            query.edit_message_text(text=Texts.CATEGORY_ADDED)

    @staticmethod
    def add_tags_dispatcher(bot, user, reply=None, query=None, reset=False):
        if reset:
            user.set_mode(Mode.ADD_PACKS, User.CATEGORY)
            categories = Database.Categories.get_categories(user.chat_id)
            query.edit_message_text(
                text=Texts.CATEGORIES,
                reply_markup=Keyboard.list([(cat.name, cat.id) for cat in categories])
            )

        elif user.mode != Mode.ADD_PACKS:
            Worker.__error_handler__(message='add_tags_dispatcher() called w/o reset')

        elif user.waiting == User.CATEGORY and query is not None:
            user.category = Database.Categories.get_category(reply)
            user.waiting = User.CAT_HASHTAGS
            query.edit_message_text(text=Texts.ENTER_CAT_HASHTAGS)

        elif user.waiting == User.CAT_HASHTAGS and query is None:
            tags, bad_tags = Utils.extract_tags(reply)
            user.category.add_tags(tags)

            Database.Categories.update_category(user.category)

            if len(bad_tags) > 0:
                bot.send_message(
                    chat_id=user.chat_id,
                    text=Texts.UNAVAILABLE_TAGS + '\n' + ' '.join(bad_tags)
                )
            if len(user.category.tags) >= Settings.HASHTAGS_COUNT_LIMIT:
                bot.send_message(
                    chat_id=user.chat_id,
                    text=Texts.TOO_MANY_TAGS_F.format(Settings.HASHTAGS_COUNT_LIMIT)
                )
                user.clear_mode()
            else:
                bot.send_message(
                    chat_id=user.chat_id,
                    text=Texts.ENTER_CAT_HASHTAGS,
                    reply_markup=Keyboard.category_adding_menu()
                )

        elif user.waiting == User.CAT_HASHTAGS and query.data == Buttons.save_category.callback:
            user.clear_mode()
            query.edit_message_text(text=Texts.TAGS_ADDED)

    @staticmethod
    def remove_tags_dispatcher(bot, user, reply=None, query=None, reset=False):
        if reset:
            user.set_mode(Mode.REMOVE_PACKS, User.CATEGORY)
            categories = Database.Categories.get_categories(user.chat_id)
            query.edit_message_text(
                text=Texts.CATEGORIES,
                reply_markup=Keyboard.list([(cat.name, cat.id) for cat in categories])
            )

        elif user.mode != Mode.REMOVE_PACKS:
            Worker.__error_handler__(message='remove_tags_dispatcher() called w/o reset')


        elif user.waiting == User.CATEGORY and query is not None:
            user.category = Database.Categories.get_category(reply)
            user.waiting = User.CAT_HASHTAGS
            query.edit_message_text(text=Texts.ENTER_CAT_HASHTAGS)

        elif user.waiting == User.CAT_HASHTAGS and query is None:
            tag_corrector = lambda tag: tag if tag.startswith('#') else '#' + tag
            tags = [tag_corrector(x) for x in reply.replace('\n', ' ').replace('#', ' ').split(' ') if x != '']
            user.category.remove_tags(tags)

            Database.Categories.update_category(user.category)

            bot.send_message(
                chat_id=user.chat_id,
                text=Texts.ENTER_CAT_HASHTAGS,
                reply_markup=Keyboard.category_adding_menu()
            )

        elif user.waiting == User.CAT_HASHTAGS and query.data == Buttons.save_category.callback:
            user.clear_mode()
            query.edit_message_text(text=Texts.TAGS_REMOVED)

    @staticmethod
    def category_remove_dispatcher(bot, user, reply=None, query=None, reset=False):
        if reset:
            user.set_mode(Mode.CATEGORY_REMOVE, User.CATEGORY)
            categories = Database.Categories.get_categories(user.chat_id)
            if len(categories) == 0:
                query.edit_message_text(text=Texts.CATEGORIES_EMPTY)
            else:
                query.edit_message_text(
                    text=Texts.REMOVE_CATEGORY,
                    reply_markup=Keyboard.list([(cat.name, cat.id) for cat in categories])
                )

        elif user.mode != Mode.CATEGORY_REMOVE:
            Worker.__error_handler__(message='category_remove_dispatcher() called w/o reset')

        elif user.waiting == User.CATEGORY and query is not None:
            Database.Categories.remove_category(Database.Categories.get_category(reply))
            user.clear_mode()
            query.edit_message_text(text=Texts.CATEGORY_REMOVED)

    @staticmethod
    def category_show_dispatcher(bot, user, reply=None, query=None, reset=False):
        if reset:
            user.set_mode(Mode.CATEGORY_SHOW, User.CATEGORY)
            categories = Database.Categories.get_categories(user.chat_id)
            if len(categories) == 0:
                query.edit_message_text(text=Texts.CATEGORIES_EMPTY)
            else:
                query.edit_message_text(
                    text=Texts.CATEGORIES,
                    reply_markup=Keyboard.list([(cat.name, cat.id) for cat in categories])
                )

        elif user.mode != Mode.CATEGORY_SHOW:
            Worker.__error_handler__(message='category_show_dispatcher() called w/o reset')

        elif user.waiting == User.CATEGORY and query is not None:
            category = Database.Categories.get_category(reply)

            text = str()
            if category.verification_tag is None:
                query.edit_message_text(text=f"<b>{category.name}:</b>")
            else:
                query.edit_message_text(text=f"<b>{category.name}: ({category.verification_tag})</b>")
            number = 1
            for tags in category.packs:
                        if len(text + f"{tags}\n") > Settings.MESSAGE_SIZE_LIMIT:
                            bot.send_message(
                                chat_id=user.chat_id,
                                text=text
                            )
                            text = str()
                        text += f"{number}: {tags}\n"
                        number += 1

            if len(text) > 0:
                bot.send_message(
                    chat_id=user.chat_id,
                    text=text
                )

            user.clear_mode()

    @staticmethod
    def account_add_dispatcher(bot, user, reply=None, query=None, reset=False):
        if reset:
            query.edit_message_text(text=Texts.ACCOUNT_ADD_RULES)
            if Database.Users.get_access(user.chat_id) <= 0:
                bot.send_message(chat_id=user.chat_id, text=Texts.ACCESS_NOT_PROVIDED_F.format(user.chat_id))
            else:
                user.set_mode(Mode.ACCOUNT_ADD, User.ACC_NAME)
                bot.send_message(user.chat_id, Texts.ENTER_ACC_NAME)
        elif user.mode != Mode.ACCOUNT_ADD:
            Worker.__error_handler__(message='account_add_dispatcher() called w/o reset')
        elif user.waiting == User.ACC_NAME:
            if len(reply) > Settings.BUTTON_SIZE_LIMIT:
                bot.send_message(
                    chat_id=user.chat_id,
                    text=Texts.MESSAGE_TOO_LARGE + '\n' + Texts.ENTER_ACC_NAME,
                )
                return
            user.acc_name = reply
            user.waiting = User.ACC_PASS
            bot.send_message(
                chat_id=user.chat_id,
                text=Texts.ENTER_ACC_PASS
            )

        elif user.waiting == User.ACC_PASS:
            user.acc_pass = reply
            Worker.confirm_account(user, user.acc_name, user.acc_pass)

        elif user.waiting == User.CODE:
            reply = reply.replace(' ', '').replace('-', '')
            user.code = reply

    @staticmethod
    def account_remove_dispatcher(bot, user, reply=None, query=None, reset=False):
        if reset:
            user.set_mode(Mode.ACCOUNT_REMOVE, User.ACC_NAME)
            accounts = Database.Accounts.get_accounts(user.chat_id)
            if len(accounts) == 0:
                query.edit_message_text(text=Texts.ACCOUNTS_EMPTY)
            else:
                query.edit_message_text(
                    text=Texts.REMOVE_ACCOUNT,
                    reply_markup=Keyboard.list([acc.username for acc in accounts])
                )
        elif user.mode != Mode.ACCOUNT_REMOVE:
            Worker.__error_handler__(message='account_remove_dispatcher() called w/o reset')

        elif user.waiting == User.ACC_NAME:
            user.acc_name = reply
            Database.Accounts.remove_account(user.chat_id, user.acc_name)
            user.clear_mode()
            query.edit_message_text(text=Texts.ACCOUNT_REMOVED)

    @staticmethod
    def hiding_setup_dispatcher(bot, user, reply=None, query=None, reset=False):
        if reset:
            accounts = Database.Accounts.get_accounts(user.chat_id)
            if Database.Users.get_access(user.chat_id) <= 0:
                bot.send_message(chat_id=user.chat_id, text=Texts.ACCESS_NOT_PROVIDED_F.format(user.chat_id))
            elif len(accounts) == 0:
                bot.send_message(chat_id=user.chat_id, text=Texts.ACCOUNTS_EMPTY)
            else:
                user.set_mode(Mode.HIDING_SETUP, User.ACC_NAME)
                if Stats.instruction_seen.get(user.chat_id) != True:
                    bot.send_message(
                        chat_id=user.chat_id,
                        text=Texts.INSTRUCTION
                    )
                    Stats.instruction_seen[user.chat_id] = True
                bot.send_message(
                    chat_id=user.chat_id,
                    text=Texts.SELECT_ACCOUNT,
                    reply_markup=Keyboard.list([acc.username for acc in accounts])
                )

        elif user.mode != Mode.HIDING_SETUP:
            Worker.__error_handler__(message='hiding_setup_dispatcher() called w/o reset')

        elif query is not None and query.data == Buttons.end_hiding.callback:
            for hiding in Stats.hidings_in_progress:
                if hiding.user == user and hiding.account.account_id == user.account.account_id:
                    hiding.stop = True
                    query.edit_message_text(Texts.HIDING_ENDING)
            user.clear_mode()

        elif user.waiting == User.ACC_NAME and query is not None:
            user.acc_name = reply
            accounts = Database.Accounts.get_accounts(user.chat_id)
            account = None
            for acc in accounts:
                if acc.username == user.acc_name:
                    account = acc

            user.account = account

            if user.is_account_in_use(account.username):
                query.edit_message_text(
                    text=Texts.ACCOUNT_IN_USE_F.format(account.username),
                    reply_markup=Keyboard.end_hiding()
                )
            else:
                categories = Database.Categories.get_categories(user.chat_id)
                if len(categories) == 0:
                    query.edit_message_text(text=Texts.CATEGORIES_EMPTY)
                else:
                    query.edit_message_text(
                        text=Texts.SELECT_CATEGORY,
                        reply_markup=Keyboard.list([(cat.name, cat.id) for cat in categories])
                    )
                    user.waiting = User.CATEGORY

        elif user.waiting == User.CATEGORY:
            user.category = Database.Categories.get_category(reply)
            user.waiting = User.URL
            if Settings.DELAYED_HIDINGS_ENABLED:
                query.edit_message_text(text=Texts.DELAYED_HIDING_INFO)
                bot.send_message(chat_id=user.chat_id, text=Texts.ENTER_URL)
            else:
                query.edit_message_text(text=Texts.ENTER_URL)

        elif user.waiting == User.URL:
            if 'instagram' in reply:
                user.url = reply
                user.clear_mode()
                Worker.start_hiding(user, user.account, user.category, user.url)
            else:
                parts = reply.split('\n')
                dt_str = ''.join([x for x in parts[0] if x.isdigit()])

                dt = None
                try:
                    dt = datetime.strptime(dt_str, '%H%M%d%m')
                except:
                    try:
                        dt = datetime.strptime(dt_str, '%H%M')
                        dt = datetime(
                            hour=dt.hour,
                            minute=dt.minute,
                            second=datetime.now().second,
                            day=datetime.now().day,
                            month=datetime.now().month,
                            year=datetime.now().year
                        )
                        if dt < datetime.now():
                            dt += timedelta(days=1)
                    except:
                        bot.send_message(chat_id=user.chat_id, text=Texts.INCORRECT_DATE)

                tags = list()
                if len(parts) > 1:
                    tags1, tags2 = Utils.extract_tags(parts[1])
                    tags = tags1 + tags2

                user.clear_mode()
                Worker.delay_hiding(user, user.account, user.category, tags, dt)


    @staticmethod
    def message_handler(update: Update, context: CallbackContext):
        chat_id = update.effective_user.id
        message_text = update.message.text

        user = Users.get_user(chat_id)

        if message_text == Menu.TITLE_HIDING_START:
            UserHandler.hiding_setup_dispatcher(context.bot, user, message_text, reset=True)

        elif message_text == Menu.TITLE_HIDING_PROGRESS:
            Stats.full_progress(bot=context.bot, admin_id=chat_id, user_id=chat_id)

        elif message_text == Menu.TITLE_CATEGORIES:
            if Texts.CATEGORY_GENERAL_INSTRUCTION is not None:
                if Stats.instruction_category_seen.get(user.chat_id) != True:
                    context.bot.send_message(
                        chat_id=user.chat_id,
                        text=Texts.CATEGORY_GENERAL_INSTRUCTION
                    )
                    Stats.instruction_category_seen[user.chat_id] = True

            categories = Database.Categories.get_categories(user.chat_id)
            text = str()
            for cat in categories:
                text += f"<b>{cat.name}:</b> {' '.join(cat.tags[:10])[:20]}... <b>({len(cat.tags)})</b>\n"

            has_categories = True
            if len(categories) == 0:
                text = Texts.CATEGORIES_EMPTY
                has_categories = False

            context.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=Keyboard.categories_menu(has_categories=has_categories)
            )

        elif message_text == Menu.TITLE_ACCOUNTS:
            accounts = Database.Accounts.get_accounts(user.chat_id)
            text = str()
            for acc in accounts:
                text += f"<b>{acc.username}:</b> {acc.password}\n"

            if len(accounts) == 0:
                text = Texts.ACCOUNTS_EMPTY

            context.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=Keyboard.accounts_menu()
            )

        elif message_text == Menu.TITLE_BUY_ACCESS:
            access_level = Database.Users.get_access(user.chat_id)
            if not Settings.REFERRAL_SYSTEM_ENABLED:
                update.effective_user.send_message(
                    Texts.HIDINGS_LEFT_F.format(access_level),
                    reply_markup=Keyboard.payment_menu()
                )
            else:
                referral_amount = Database.Users.get_referral_amount(chat_id)
                update.effective_user.send_message(
                    Texts.HIDINGS_LEFT_F.format(access_level) + '\n' +
                    Texts.REFERRAL_AMOUNT_F.format(referral_amount) + '\n' +
                    Texts.REFERRAL_ID_F.format(chat_id),
                    reply_markup=Keyboard.payment_menu()
                )

        elif message_text == Menu.ADMIN_TITLE_REPORT:
            AdminHandler.report(update, context)

        elif message_text == Menu.ADMIN_TITLE_FULL_REPORT:
            AdminHandler.full_report(update, context)

        elif message_text == Menu.ADMIN_TITLE_PROGRESS:
            AdminHandler.full_progress(update, context)

        elif message_text == Menu.TITLE_SUPPORT:
            update.effective_user.send_message(Texts.SUPPORT)

        else:
            if user.mode == Mode.CATEGORY_ADD:
                UserHandler.category_add_dispatcher(context.bot, user, message_text)

            elif user.mode == Mode.ADD_PACKS:
                UserHandler.add_tags_dispatcher(context.bot, user, message_text)

            elif user.mode == Mode.REMOVE_PACKS:
                UserHandler.remove_tags_dispatcher(context.bot, user, message_text)

            elif user.mode == Mode.ACCOUNT_ADD:
                UserHandler.account_add_dispatcher(context.bot, user, message_text)

            elif user.mode == Mode.HIDING_SETUP:
                UserHandler.hiding_setup_dispatcher(context.bot, user, message_text)

    @staticmethod
    def keyboard_handler(update: Update, context: CallbackContext):
        chat_id = update.effective_message.chat_id
        message_id = update.effective_message.message_id
        query = update.callback_query
        data = query.data

        user = Users.get_user(chat_id)

        if data == Buttons.add_category.callback:
            UserHandler.category_add_dispatcher(context.bot, user, query=query, reset=True)

        elif data == Buttons.add_packs.callback:
            UserHandler.add_tags_dispatcher(context.bot, user, query=query, reset=True)

        elif data == Buttons.remove_packs.callback:
            UserHandler.remove_tags_dispatcher(context.bot, user, query=query, reset=True)

        elif data == Buttons.remove_category.callback:
            UserHandler.category_remove_dispatcher(context.bot, user, query=query, reset=True)

        elif data == Buttons.show_category.callback:
            UserHandler.category_show_dispatcher(context.bot, user, query=query, reset=True)

        elif data == Buttons.add_account.callback:
            UserHandler.account_add_dispatcher(context.bot, user, query=query, reset=True)

        elif data == Buttons.remove_account.callback:
            UserHandler.account_remove_dispatcher(context.bot, user, query=query, reset=True)

        elif data in [x.callback for x in Buttons.payment_buttons]:
            for button in Buttons.payment_buttons:
                if data == button.callback:
                    bill = PaymentSystem.create_bill(user, button.value[1], button.value[0])
                    if bill is not None:
                        update.effective_message.edit_text(bill.payment_url)
                    else:
                        for admin_id in Settings.DEBUG_IDS:
                            context.bot.send_message(admin_id, Texts.BILL_CREATE_ERROR)
                        update.effective_message.edit_text(Texts.BILL_CREATE_ERROR)

        elif user.mode == Mode.CATEGORY_ADD:
            UserHandler.category_add_dispatcher(context.bot, user, data, query)

        elif user.mode == Mode.ADD_PACKS:
            UserHandler.add_tags_dispatcher(context.bot, user, data, query)

        elif user.mode == Mode.REMOVE_PACKS:
            UserHandler.remove_tags_dispatcher(context.bot, user, data, query)

        elif user.mode == Mode.CATEGORY_SHOW:
            UserHandler.category_show_dispatcher(context.bot, user, data, query)

        elif user.mode == Mode.CATEGORY_REMOVE:
            UserHandler.category_remove_dispatcher(context.bot, user, data, query)

        elif user.mode == Mode.ACCOUNT_REMOVE:
            UserHandler.account_remove_dispatcher(context.bot, user, data, query)

        elif user.mode == Mode.HIDING_SETUP:
            UserHandler.hiding_setup_dispatcher(context.bot, user, data, query)



def error_handler(update, context):
    logging.getLogger().info(msg="Исключение при обработке:", exc_info=context.error)
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = ''.join(tb_list)

    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        f'Возникло исключение при обработке.\n'
        f'<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}'
        '</pre>\n\n'
        f'<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n'
        f'<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n'
        f'<pre>{html.escape(tb_string)}</pre>'
    )

    for chat_id in Settings.DEBUG_IDS:
        context.bot.send_message(
            chat_id=chat_id,
            text=message.replace('<', ' ').replace('>', ' ').replace('_', '-')[:Settings.MESSAGE_SIZE_LIMIT],
        )

class Bot:

    updater = None

    @classmethod
    def bot_init(cls):

        for path in Settings.REQUIRED_PATHES:
            if not os.path.exists(path):
                os.mkdir(path)

        logging.basicConfig(format='[%(asctime)s] %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S',
                            level=logging.INFO,
                            filename=f"log.txt")
        log = logging.getLogger()
        log.level = logging.INFO
        log.addHandler(logging.StreamHandler(sys.stderr))

        defaults = Defaults(parse_mode=ParseMode.HTML)
        updater = Updater(Settings.TOKEN, use_context=True, defaults=defaults)
        dp = updater.dispatcher

        dp.add_error_handler(error_handler)

        Database.init(Settings.DB_HOST, Settings.DB_USER, Settings.DB_PASSWORD, updater.bot)
        Worker.init(updater.bot, Database)
        PaymentSystem.updater_start(updater.bot)

        # -*- Admin handlers -*-
        dp.add_handler(CommandHandler('info', AdminHandler.info))
        dp.add_handler(CommandHandler('report', AdminHandler.report))
        dp.add_handler(CommandHandler('fr', AdminHandler.full_report, pass_args=True))
        dp.add_handler(CommandHandler('fp', AdminHandler.full_progress, pass_args=True))
        dp.add_handler(CommandHandler('ra', AdminHandler.random_activities, pass_args=True))
        dp.add_handler(CommandHandler('message', AdminHandler.message, pass_args=True))
        dp.add_handler(CommandHandler('users', AdminHandler.users))
        dp.add_handler(CommandHandler('set_access', AdminHandler.set_access, pass_args=True))
        dp.add_handler(CommandHandler('update_keyboard', AdminHandler.update_keyboard))
        dp.add_handler(CommandHandler('proxy', AdminHandler.proxy))
        dp.add_handler(CommandHandler('add_proxy', AdminHandler.add_proxy, pass_args=True))
        dp.add_handler(CommandHandler('set_proxy', AdminHandler.set_proxy, pass_args=True))
        dp.add_handler(CommandHandler('accounts', AdminHandler.accounts))
        dp.add_handler(CommandHandler('get_browser', AdminHandler.get_browser, pass_args=True))

        # -*- Debug handlers -*-
        dp.add_handler(CommandHandler('eval', AdminHandler.eval, pass_args=True))
        dp.add_handler(CommandHandler('exec', AdminHandler.exec, pass_args=True))
        dp.add_handler(CommandHandler('test_bill', AdminHandler.test_bill))

        # -*- User handlers -*-
        dp.add_handler(CommandHandler('start', UserHandler.start))
        dp.add_handler(CommandHandler('ref', UserHandler.referral, pass_args=True))
        dp.add_handler(MessageHandler(Filters.text, UserHandler.message_handler))
        dp.add_handler(CallbackQueryHandler(callback=UserHandler.keyboard_handler))

        updater.start_polling()
        cls.updater = updater

    @classmethod
    def bot_idle(cls):
        cls.updater.idle()

        Worker.save()
        for admin_id in Settings.DEBUG_IDS:
            Stats.full_report(cls.updater.bot, admin_id)

        logging.info("Scheduler stopped")
