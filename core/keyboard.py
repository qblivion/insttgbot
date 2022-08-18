from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup)

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


class Menu:
    TITLE_HIDING_START = 'Начать'
    TITLE_HIDING_PROGRESS = 'Прогресс'
    TITLE_CATEGORIES = 'Подборки'
    TITLE_ACCOUNTS = 'Аккаунты'
    TITLE_BUY_ACCESS = 'Купить доступ'
    TITLE_SUPPORT = 'Поддержка'

    ADMIN_TITLE_REPORT = '💻 Сервер'
    ADMIN_TITLE_FULL_REPORT = '📄 Отчет'
    ADMIN_TITLE_PROGRESS = '📝 В процессе'


class Button:

    def __init__(self, text, value=None):
        self.text = text
        self.callback = str(id(self))

        self.value = value


class Buttons:

    payment_buttons = [
        Button(
            f"{count}  {Texts.hidings(count)} - {price} ₽",
            value=(count, price)
        ) for count, price in Settings.HIDINGS_TO_BUY
    ]

    ok = Button('Ок ✅')
    not_use = Button('Не использовать')

    show_category = Button('Посмотреть подборку')
    add_packs = Button('Добавить теги')
    remove_packs = Button('Удалить теги')
    add_category = Button('Добавить подборку')
    remove_category = Button('Удалить подборку')

    save_category = Button('Сохранить')

    add_account = Button('Добавить аккаунт')
    remove_account = Button('Удалить аккаунт')

    resend_code = Button('Отправить заново')

    end_hiding = Button('Остановить скрытие')

class Keyboard:

    @classmethod
    def main_menu(cls, is_admin=False):
        keyboard = [
            [
                KeyboardButton(Menu.TITLE_HIDING_START)
            ],
            [
                KeyboardButton(Menu.TITLE_BUY_ACCESS),
                KeyboardButton(Menu.TITLE_SUPPORT)
            ],
            [
                KeyboardButton(Menu.TITLE_CATEGORIES),
                KeyboardButton(Menu.TITLE_ACCOUNTS),
                KeyboardButton(Menu.TITLE_HIDING_PROGRESS),
            ],
        ]
        if is_admin:
            keyboard.append([
                KeyboardButton(Menu.ADMIN_TITLE_REPORT),
                KeyboardButton(Menu.ADMIN_TITLE_FULL_REPORT),
                KeyboardButton(Menu.ADMIN_TITLE_PROGRESS),
            ])
        return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

    @classmethod
    def ok(cls):
        keyboard = [
            [
                InlineKeyboardButton(Buttons.ok.text, callback_data=Buttons.ok.callback)
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    @classmethod
    def not_use(cls):
        keyboard = [
            [
                InlineKeyboardButton(Buttons.not_use.text, callback_data=Buttons.not_use.callback)
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    @classmethod
    def list(cls, values):
        keyboard = list()
        for value in values:
            if isinstance(value, list) or isinstance(value, tuple):
                if len(value) == 1:
                    keyboard.append(
                        [InlineKeyboardButton(value[0], callback_data=value[0])]
                    )
                else:
                    keyboard.append(
                        [InlineKeyboardButton(value[0], callback_data=value[1])]
                    )
            else:
                keyboard.append(
                    [InlineKeyboardButton(value, callback_data=value)]
                )
        return InlineKeyboardMarkup(keyboard)

    @classmethod
    def payment_menu(cls):
        keyboard = list()
        for button in Buttons.payment_buttons:
            keyboard.append([InlineKeyboardButton(button.text, callback_data=button.callback)])
        return InlineKeyboardMarkup(keyboard)

    @classmethod
    def categories_menu(cls, has_categories=True):
        if has_categories:
            keyboard = [
                [
                    InlineKeyboardButton(Buttons.show_category.text, callback_data=Buttons.show_category.callback)
                ],
                [
                    InlineKeyboardButton(Buttons.add_packs.text, callback_data=Buttons.add_packs.callback),
                    InlineKeyboardButton(Buttons.remove_packs.text, callback_data=Buttons.remove_packs.callback)
                ],
                [
                    InlineKeyboardButton(Buttons.add_category.text, callback_data=Buttons.add_category.callback),
                    InlineKeyboardButton(Buttons.remove_category.text, callback_data=Buttons.remove_category.callback)
                ]
            ]
        else:
            keyboard = [
                [
                    InlineKeyboardButton(Buttons.add_category.text, callback_data=Buttons.add_category.callback)
                ]
            ]

        return InlineKeyboardMarkup(keyboard)

    @classmethod
    def category_adding_menu(cls):
        keyboard = [
            [
                InlineKeyboardButton(Buttons.save_category.text, callback_data=Buttons.save_category.callback)
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    @classmethod
    def accounts_menu(cls):
        keyboard = [
            [
                InlineKeyboardButton(Buttons.add_account.text, callback_data=Buttons.add_account.callback),
                InlineKeyboardButton(Buttons.remove_account.text, callback_data=Buttons.remove_account.callback)
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    @classmethod
    def resend_code_menu(cls):
        keyboard = [
            [
                InlineKeyboardButton(Buttons.resend_code.text, callback_data=Buttons.resend_code.callback)
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    @classmethod
    def end_hiding(cls):
        keyboard = [
            [
                InlineKeyboardButton(Buttons.end_hiding.text, callback_data=Buttons.end_hiding.callback)
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
