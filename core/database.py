import mysql.connector
import mysql.connector.errorcode
import json
import traceback
import datetime

try:
    from local_settings import Settings
except ImportError:
    try:
        from settings import Settings
    except ImportError:
        from core.settings import Settings


class AccountEntry:

    def __init__(self, account_id, chat_id, username, password, comment_limit, proxy_id):
        self.account_id = account_id
        self.chat_id = chat_id
        self.username = username
        self.password = password
        self.comment_limit = comment_limit
        self.proxy_id = proxy_id

    def proxy(self):
        if self.proxy_id is None:
            return None
        else:
            return Database.Proxy.get(self.proxy_id)

    def __str__(self):
        return self.username


class UserEntry:

    def __init__(self, chat_id, access, referral_id, referral_amount):
        self.chat_id = chat_id
        self.access = access
        self.referral_id = referral_id
        self.referral_amount = referral_amount


class CategoryEntry:

    def __init__(self, id=None, chat_id=None, name=None, verification_tag=None, tags_dump=None):
        self.id = id
        self.chat_id = chat_id
        self.name = name
        self.verification_tag = verification_tag
        self.tags = list()

        self.packs = list()
        if tags_dump is not None:
            self.add_tags(json.loads(tags_dump))

    def __update_packs__(self):
        self.packs = list()

        number = 1
        tags = self.tags
        while len(tags) > 0:
            if self.verification_tag is None:
                self.packs.append(' '.join(tags[:Settings.COMMENT_HIDING_PACK_SIZE]))
                tags = tags[Settings.COMMENT_HIDING_PACK_SIZE:]
            else:
                self.packs.append(
                    ' '.join([self.verification_tag + str(number)] + tags[:Settings.COMMENT_HIDING_PACK_SIZE - 1]))
                tags = tags[Settings.COMMENT_HIDING_PACK_SIZE - 1:]
                number += 1

    def add_tags(self, tags):
        for tag in tags:
            if tag not in self.tags:
                self.tags.append(tag)
        self.tags.reverse()
        self.tags = self.tags[:Settings.HASHTAGS_COUNT_LIMIT]
        self.__update_packs__()

    def remove_tags(self, tags):
        for tag in tags:
            try:
                self.tags.remove(tag)
            except Exception:
                pass
        self.__update_packs__()


class BillEntry:

    def __init__(self, bill_id, chat_id, amount, status, value, date_created):
        self.bill_id = bill_id
        self.chat_id = chat_id
        self.amount = amount
        self.status = status
        self.value = value
        self.date_created = date_created


class ProxyEntry:

    def __init__(self, id, ip, port, login, password, date_end: datetime.datetime):
        self.id = id
        self.ip = ip
        self.port = port
        self.login = login
        self.password = password
        self.date_end = date_end


class Database:
    NAME = f"`{Settings.DB_NAME}`"

    class Users:
        NAME = "`users`"

        chat_id = "`chat_id`"
        access = "`access`"
        referral_id = "`referral_id`"
        referral_amount = "`referral_amount`"

        @classmethod
        def create_table(cls):
            Database.execute(f"""
                CREATE TABLE IF NOT EXISTS {cls.NAME} (
                  {cls.chat_id} BIGINT NOT NULL,
                  {cls.access} INT UNSIGNED NOT NULL DEFAULT '0',
                  {cls.referral_id} BIGINT DEFAULT NULL,
                  {cls.referral_amount} INT UNSIGNED NOT NULL DEFAULT '0',
                  PRIMARY KEY ({cls.chat_id}),
                  UNIQUE INDEX `{cls.chat_id.replace('`', '')}_UNIQUE` ({cls.chat_id}))
                ENGINE = InnoDB
                DEFAULT CHARACTER SET = utf8mb4
                COLLATE = utf8mb4_bin
            """)

        @classmethod
        def register_user(cls, chat_id):
            Database.execute(f"INSERT INTO {cls.NAME} "
                             f"({cls.chat_id}) "
                             f"VALUES "
                             f"(%s)",
                             [chat_id],
                             ignore_errors=[mysql.connector.errorcode.ER_DUP_ENTRY])

        @classmethod
        def set_referral(cls, chat_id, referral_id):
            if chat_id == referral_id:
                return False

            available_referral_ids = [user.chat_id for user in Database.Users.get_users()]
            if referral_id not in available_referral_ids:
                return False

            current_referral_id = cls.get_referral(chat_id)
            if current_referral_id is not None:
                return False

            Database.execute(f"UPDATE {cls.NAME} "
                             f"SET {cls.referral_id} = %s, {cls.access} = {cls.access} + %s "
                             f"WHERE ({cls.chat_id} = %s AND {cls.referral_id} IS NULL)",
                             [referral_id, Settings.REFERRER_AWARD_VALUE, chat_id])
            cls.increase_access(referral_id, Settings.REFERRAL_AWARD_VALUE)
            return True

        @classmethod
        def get_referral_amount(cls, chat_id):
            Database.execute(f"SELECT {cls.referral_amount} "
                             f"FROM {cls.NAME} "
                             f"WHERE {cls.chat_id} = %s",
                             [chat_id])
            data = Database.fetchall()
            access_level = data[0][0]
            return access_level

        @classmethod
        def get_referral(cls, chat_id):
            Database.execute(f"SELECT {cls.referral_id} "
                             f"FROM {cls.NAME}"
                             f"WHERE {cls.chat_id} = %s",
                             [chat_id])
            referral_id = Database.fetchall()[0][0]
            return referral_id

        @classmethod
        def get_users(cls):
            Database.execute(f"SELECT * "
                             f"FROM {cls.NAME}")
            data = Database.fetchall()
            users = [UserEntry(*x) for x in data]
            return users

        @classmethod
        def set_access(cls, chat_id, access_level):
            Database.execute(f"UPDATE {cls.NAME} "
                             f"SET {cls.access} = %s "
                             f"WHERE {cls.chat_id} = %s",
                             [access_level, chat_id])

        @classmethod
        def decrease_access(cls, chat_id, value):
            Database.execute(f"UPDATE {cls.NAME} "
                             f"SET {cls.access} = {cls.access} - %s "
                             f"WHERE {cls.chat_id} = %s",
                             [value, chat_id])

        @classmethod
        def increase_access(cls, chat_id, value):
            Database.execute(f"UPDATE {cls.NAME} "
                             f"SET {cls.access} = {cls.access} + %s "
                             f"WHERE {cls.chat_id} = %s",
                             [value, chat_id])

        @classmethod
        def get_access(cls, chat_id):
            Database.execute(f"SELECT {cls.access} "
                             f"FROM {cls.NAME} "
                             f"WHERE {cls.chat_id} = %s",
                             [chat_id])
            data = Database.fetchall()
            access_level = data[0][0]
            return access_level

    class Accounts:
        NAME = "`accounts`"

        id = "`id`"
        chat_id = "`chat_id`"
        username = "`username`"
        password = "`password`"
        comment_limit = "`comment_limit`"
        ip = "`ip`"

        username_max_len = 255
        password_max_len = 255
        comment_limit_default = 150

        @classmethod
        def create_table(cls):
            Database.execute(f"""
                CREATE TABLE IF NOT EXISTS {cls.NAME} (
                  {cls.id} INT UNSIGNED NOT NULL AUTO_INCREMENT,
                  {cls.chat_id} BIGINT NOT NULL,
                  {cls.username} VARCHAR({cls.username_max_len}) NOT NULL,
                  {cls.password} VARCHAR({cls.password_max_len}) NOT NULL,
                  {cls.comment_limit} INT UNSIGNED NOT NULL DEFAULT {cls.comment_limit_default},
                  PRIMARY KEY ({cls.id}),
                  UNIQUE INDEX `{cls.id.replace('`', '')}_UNIQUE` ({cls.id}))
                ENGINE = InnoDB
                DEFAULT CHARACTER SET = utf8mb4
                COLLATE = utf8mb4_bin
            """)

            Database.execute(f"""
                ALTER TABLE {cls.NAME} 
                ADD COLUMN {cls.ip} INT NULL AFTER {cls.comment_limit};
            """, ignore_errors=[mysql.connector.errorcode.ER_DUP_FIELDNAME])

        @classmethod
        def get_accounts(cls, chat_id) -> [AccountEntry]:
            Database.execute(f"SELECT * "
                             f"FROM {cls.NAME} "
                             f"WHERE {cls.chat_id} = %s",
                             [chat_id])
            data = Database.fetchall()
            accounts = [AccountEntry(*x) for x in data]
            return accounts

        @classmethod
        def get_all(cls) -> [AccountEntry]:
            Database.execute(f"SELECT * "
                             f"FROM {cls.NAME}")
            data = Database.fetchall()
            accounts = [AccountEntry(*x) for x in data]
            return accounts

        @classmethod
        def add_account(cls, chat_id, username, password):
            Database.execute(f"INSERT INTO {cls.NAME} "
                             f"({cls.chat_id}, {cls.username}, {cls.password}, {cls.comment_limit}) "
                             f"VALUES (%s, %s, %s, %s)",
                             [chat_id, username, password, cls.comment_limit_default])

        @classmethod
        def remove_account(cls, chat_id, username):
            Database.execute(f"DELETE FROM {cls.NAME} "
                             f"WHERE ({cls.chat_id} = %s AND {cls.username} = %s)",
                             [chat_id, username])

        @classmethod
        def set_proxy(cls, account_id, proxy_id):
            if proxy_id is not None:
                proxy = Database.Proxy.get(proxy_id)
                proxy_id = proxy.id
            Database.execute(f"UPDATE {cls.NAME} "
                             f"SET {cls.ip} = %s "
                             f"WHERE {cls.id} = %s;",
                             [proxy_id, account_id])

    class Categories:
        NAME = "`categories`"

        id = "`id`"
        chat_id = "`chat_id`"
        name = "`name`"
        verification_tag = "`verification_tag`"
        tags = "`tags`"

        @classmethod
        def create_table(cls):
            Database.execute(f"""
                        CREATE TABLE IF NOT EXISTS {cls.NAME} (
                          {cls.id} INT UNSIGNED NOT NULL AUTO_INCREMENT,
                          {cls.chat_id} BIGINT NOT NULL,
                          {cls.name} VARCHAR(255) NOT NULL,
                          {cls.verification_tag} VARCHAR(255) NULL,
                          {cls.tags} JSON NOT NULL,
                          PRIMARY KEY ({cls.id}),
                          UNIQUE INDEX `{cls.id.replace('`', '')}_UNIQUE` ({cls.id}))
                        ENGINE = InnoDB
                        DEFAULT CHARACTER SET = utf8mb4
                        COLLATE = utf8mb4_bin
                    """)

        @classmethod
        def get_categories(cls, chat_id):
            Database.execute(f"SELECT * "
                             f"FROM {cls.NAME} "
                             f"WHERE {cls.chat_id} = %s",
                             [chat_id])
            data = Database.fetchall()
            categories = [CategoryEntry(*x) for x in data]
            return categories

        @classmethod
        def get_category(cls, category_id):
            Database.execute(f"SELECT * "
                             f"FROM {cls.NAME} "
                             f"WHERE {cls.id} = %s",
                             [category_id])
            data = Database.fetchall()
            category = CategoryEntry(*data[0])
            return category

        @classmethod
        def add_category(cls, category: CategoryEntry):
            if category.chat_id is None or category.name is None:
                return
            category.tags = category.tags[:Settings.HASHTAGS_COUNT_LIMIT]

            # if len(categories) > Settings.CATEGORIES_COUNT_LIMIT:
            #     return

            Database.execute(f"INSERT INTO {cls.NAME} "
                             f"({cls.chat_id}, {cls.name}, {cls.verification_tag}, {cls.tags}) "
                             f"VALUES (%s, %s, %s, %s)",
                             [category.chat_id, category.name, category.verification_tag, json.dumps(category.tags)])
            categories = cls.get_categories(category.chat_id)
            for cat in categories:
                if cat.chat_id == category.chat_id and cat.name == category.name:
                    category.id = cat.id

        @classmethod
        def remove_category(cls, category: CategoryEntry):
            Database.execute(f"DELETE FROM {cls.NAME} "
                             f"WHERE {cls.id} = %s",
                             [category.id])

        @classmethod
        def update_category(cls, category: CategoryEntry):
            Database.execute(f"UPDATE {cls.NAME} "
                             f"SET {cls.tags} = %s "
                             f"WHERE {cls.id} = %s",
                             [json.dumps(category.tags), category.id])

    class Bills:

        NAME = "`bills`"

        bill_id = "`bill_id`"
        chat_id = "`chat_id`"
        amount = "`amount`"
        status = "`status`"
        value = "`value`"
        date_created = "`date_created`"

        @classmethod
        def create_table(cls):
            Database.execute(f"""
                      CREATE TABLE IF NOT EXISTS {cls.NAME} (
                      {cls.bill_id} VARCHAR(255) NOT NULL,
                      {cls.chat_id} BIGINT NOT NULL,
                      {cls.amount} INT UNSIGNED NOT NULL,
                      {cls.status} INT UNSIGNED NOT NULL,
                      {cls.value} INT UNSIGNED NOT NULL,
                      {cls.date_created} DATETIME NOT NULL,
                      PRIMARY KEY ({cls.bill_id}),
                      UNIQUE INDEX `{cls.bill_id.replace('`', '')}_UNIQUE` ({cls.bill_id}));
                    """)

        @classmethod
        def create_bill(cls, bill_id, chat_id, amount, value):
            dt = datetime.datetime.now().isoformat(sep=' ')
            Database.execute(f"INSERT INTO {cls.NAME} "
                             f"({cls.bill_id}, {cls.chat_id}, {cls.amount}, {cls.status}, {cls.value}, {cls.date_created}) "
                             f"VALUES (%s, %s, %s, %s, %s, %s)",
                             [bill_id, chat_id, amount, 0, value, dt])

        @classmethod
        def get_unpaid_bills(cls):
            Database.execute(f"SELECT * "
                             f"FROM {cls.NAME} "
                             f"WHERE {cls.status} = 0")
            data = Database.fetchall()
            bills = [BillEntry(*x) for x in data]
            return bills

    class Proxy:

        NAME = "`proxy`"

        id = "`id`"
        ip = "`ip`"
        port = "`port`"
        login = "`login`"
        password = "`password`"
        date_end = "`date_end`"

        @classmethod
        def create_table(cls):
            Database.execute(f"""
            CREATE TABLE IF NOT EXISTS {cls.NAME} (
              {cls.id} INT NOT NULL AUTO_INCREMENT,
              {cls.ip} VARCHAR(45) NOT NULL,
              {cls.port} VARCHAR(45) NOT NULL,
              {cls.login} VARCHAR(45) NULL,
              {cls.password} VARCHAR(45) NULL,
              {cls.date_end} DATETIME NOT NULL,
              PRIMARY KEY ({cls.id}),
              UNIQUE INDEX `{cls.id.replace('`', '')}_UNIQUE` ({cls.id}),
              UNIQUE INDEX `{cls.ip.replace('`', '')}_UNIQUE` ({cls.ip}));
            """)

        @classmethod
        def add(cls, ip, port, login, password, days_left: int):
            dt = (datetime.datetime.now() + datetime.timedelta(days=days_left)).isoformat(sep=' ')
            Database.execute(f"INSERT INTO {cls.NAME} "
                             f"({cls.ip}, {cls.port}, {cls.login}, {cls.password}, {cls.date_end}) "
                             f"VALUES (%s, %s, %s, %s, %s)",
                             [ip, port, login, password, dt])

        @classmethod
        def get(cls, id) -> ProxyEntry:
            Database.execute(f"SELECT * "
                             f"FROM {cls.NAME} "
                             f"WHERE {cls.id} = %s",
                             [id])
            data = Database.fetchall()
            return ProxyEntry(*data[0])

        @classmethod
        def get_all(cls) -> [ProxyEntry]:
            Database.execute(f"SELECT * "
                             f"FROM {cls.NAME}")
            data = Database.fetchall()
            return [ProxyEntry(*x) for x in data]

        @classmethod
        def update_date_end(cls, id, days_left: int):
            dt = (datetime.datetime.now() + datetime.timedelta(days=days_left)).isoformat(sep=' ')
            Database.execute(f"UPDATE {cls.NAME} "
                             f"SET {cls.date_end} = %s "
                             f"WHERE {cls.id} = %s;",
                             [dt, id])

    __db__ = None
    __cursor__ = None

    __bot__ = None

    __host__ = str()
    __user__ = str()
    __password__ = str()
    __database__ = str()

    @classmethod
    def init(cls, host, user, password, bot):
        cls.__host__ = host
        cls.__user__ = user
        cls.__password__ = password
        cls.__bot__ = bot

        cls.db_connect()
        cls.db_setup()
        print("Database: connected")

    @classmethod
    def execute(cls, sql, args=(), commit=True, ignore_errors=None):
        try:
            cls.__cursor__.execute(sql, args)
            if commit and 'SELECT' not in sql:
                cls.__db__.commit()
            return True

        except BaseException as exc:

            if ignore_errors is not None and exc.args[0] in ignore_errors:
                return False

            for chat_id in Settings.DEBUG_IDS:
                cls.__bot__.send_message(
                    chat_id=chat_id,
                    text=f"Database error: {str(exc)}\n\n"
                         f"SQL request: {sql}\n\n"
                         f"Args: {str(args)}\n\n"
                         f"Trying to reconnect..."
                )

            try:
                cls.db_connect()
                cls.__cursor__.execute(sql, args)
                if commit and 'SELECT' not in sql:
                    cls.__db__.commit()
                return True

            except BaseException as fatal_exc:
                for chat_id in Settings.DEBUG_IDS:
                    cls.__bot__.send_message(
                        chat_id=chat_id,
                        text=f"Database error: {str(exc)}\n\n"
                             f"Database fatal error after reconnection: {str(fatal_exc)}\n\n"
                             f"SQL request: {sql}\n\n"
                             f"Args: {str(args)}\n\n"
                             f"Reconnection failed."
                    )
                return False

    @classmethod
    def commit(cls):
        cls.__db__.commit()

    @classmethod
    def fetchall(cls):
        return cls.__cursor__.fetchall()

    @classmethod
    def db_connect(cls):
        cls.__db__ = mysql.connector.connect(
            host=cls.__host__,
            user=cls.__user__,
            password=cls.__password__,
            database=cls.NAME.replace('`', ''),
            auth_plugin='mysql_native_password',
        )
        cls.__cursor__ = cls.__db__.cursor()

    @classmethod
    def db_setup(cls):
        cls.Users.create_table()
        cls.Accounts.create_table()
        cls.Categories.create_table()
        cls.Bills.create_table()
        cls.Proxy.create_table()

    @classmethod
    def __error_handler__(cls, message=None):
        if cls.__bot__ is not None:
            exc_str = traceback.format_exc().lstrip()
            exc_str = f"{message}\n\n" + exc_str
            exc_str = "❗️❗️❗️ALERT❗️❗️❗️\n\n" + exc_str
            for chat_id in Settings.DEBUG_IDS:
                cls.__bot__.send_message(
                    chat_id=chat_id,
                    text=exc_str,
                )

    @classmethod
    def approve_bill(cls, bill: BillEntry):
        cls.execute(f"UPDATE {cls.Users.NAME}, {cls.Bills.NAME} "
                    f"SET {cls.Users.access} = {cls.Users.access} + %s, {cls.Bills.status} = 1 "
                    f"WHERE ({cls.Users.NAME}.{cls.Users.chat_id} = %s AND {cls.Bills.bill_id} = %s)",
                    [bill.value, bill.chat_id, bill.bill_id])
        # cls.execute(f"UPDATE {cls.NAME}.{cls.Bills.NAME} "
        #             f"SET {cls.Bills.status} = 1 "
        #             f"WHERE {cls.Bills.bill_id} = %s;",
        #             [bill.bill_id])
        # cls.execute(f"UPDATE {cls.NAME}.{cls.Users.NAME} "
        #             f"SET {cls.Users.access} = {cls.Users.access} + %s "
        #             f"WHERE {cls.Users.chat_id} = %s;",
        #             [bill.value, bill.chat_id])

        referral_id = cls.Users.get_referral(bill.chat_id)
        if Settings.PAYMENT_SYSTEM_ENABLED and referral_id is not None:
            referral_reward = int(bill.amount * Settings.REFERRAL_AWARD_COEFFICIENT)
            cls.execute(f"UPDATE {cls.Users.NAME} "
                        f"SET {cls.Users.referral_amount} = {cls.Users.referral_amount} + %s "
                        f"WHERE {cls.Users.chat_id} = %s",
                        [referral_reward, referral_id])
