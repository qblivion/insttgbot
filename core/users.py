class Mode:
    CATEGORY_SHOW = "category_show"
    CATEGORY_ADD = "category_add"
    ADD_PACKS = "add_packs"
    REMOVE_PACKS = "remove_packs"
    CATEGORY_REMOVE = "category_remove"

    ACCOUNT_ADD = "account_add"
    ACCOUNT_REMOVE = "account_remove"

    HIDING_SETUP = "hiding_setup"


class User:

    CONFIRM = "confirm"
    VERIFICATION_TAG = "verification_tag"
    CATEGORY = "category"
    CAT_NAME = "cat_name"
    CAT_HASHTAGS = "cat_hashtags"
    PACK_NUMBER = "pack_number"

    ACC_NAME = "acc_name"
    ACC_PASS = "acc_pass"

    CODE = "code"

    URL = "url"

    def __init__(self, chat_id: int):
        self.chat_id = chat_id
        self.mode = None
        self.waiting = None

        self.category = None
        self.url = None

        self.account = None
        self.acc_name = None
        self.acc_pass = None

        self.code = None

        self.__accounts_in_use__ = list()

    def set_mode(self, mode, waiting=None):
        self.mode = mode
        self.waiting = waiting

    def clear_mode(self):
        self.mode = None
        self.waiting = None

    def is_account_in_use(self, username):
        if username in self.__accounts_in_use__:
            return True
        else:
            return False

    def set_account_in_use(self, username):
        if username not in self.__accounts_in_use__:
            self.__accounts_in_use__.append(username)

    def remove_account_from_use(self, username):
        if username in self.__accounts_in_use__:
            self.__accounts_in_use__.remove(username)


class Users:

    __users__ = dict()

    @classmethod
    def get_user(self, user_id: int):
        user = self.__users__.get(user_id)

        if user is None:
            user = User(user_id)
            self.__users__[user_id] = user

        return user