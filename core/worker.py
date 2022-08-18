from datetime import datetime, timedelta
import traceback
from threading import Thread
import time
import random
import os
import json
import logging

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium import webdriver
from telegram import ParseMode
import psutil

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
    from database import Database, AccountEntry, ProxyEntry, CategoryEntry
except ImportError:
    from core.database import Database, AccountEntry, ProxyEntry, CategoryEntry
try:
    from users import User, Users
except ImportError:
    from core.users import User, Users
try:
    from user_agents import UserAgents
except ImportError:
    from core.user_agents import UserAgents
try:
    from keyboard import Keyboard, Buttons
except ImportError:
    from core.keyboard import Keyboard, Buttons


from core.stats import Stats
from payment_core.payment_system import PaymentSystem


class Selenium:

    HEADLESS = Settings.SELENIUM_HEADLESS

    # Timeouts
    POST_URLS_GETTING_TIMEOUT = 8
    GET_ELEMENT_TIMEOUT = 10

    proxies = ()

    desktop_user_agents = UserAgents.desktop_user_agents
    mobile_user_agents = UserAgents.mobile_user_agents

    __cookies__ = dict()

    @classmethod
    def get_post_urls(cls, browser, hashtag):
        hashtag = hashtag.replace('#', '')

        post_urls = list()
        browser.get(f"https://www.instagram.com/explore/tags/{hashtag}/")

        top_posts_title = cls.get_element(browser, By.XPATH,
                                              '//*[@id]/section/main/article/div[1]/h2/div')
        if top_posts_title is not None:
            posts_xpath = '//*[@id]/section/main/article/div[1]/div/div//a'
            elements = browser.find_elements_by_xpath(posts_xpath)
            for elem in elements:
                elem_href = elem.get_attribute('href')
                post_urls.append(elem_href)


        most_recent_posts_title = cls.get_element(browser, By.XPATH, '//*[@id]/section/main/article/h2')
        if most_recent_posts_title is not None:
            scroll_target_xpath = '//*[@id]/section/footer'
            scroll_target = cls.get_element(browser, By.XPATH, scroll_target_xpath)

            posts_xpath = '//*[@id]/section/main/article/div[2]/div//a'
            last_posts_time = time.time()
            while time.time() - last_posts_time < cls.POST_URLS_GETTING_TIMEOUT:
                browser.execute_script('arguments[0].scrollIntoView(true);', scroll_target)
                time.sleep(0.1)
                posts_elements = browser.find_elements_by_xpath(posts_xpath)
                for post_elem in posts_elements:
                    url = post_elem.get_attribute('href')
                    if url not in post_urls:
                        post_urls.append(url)
                        last_posts_time = time.time()

        post_urls = list(set(post_urls))
        random.shuffle(post_urls)

        print('Posts:', len(post_urls))
        return post_urls

    @classmethod
    def log_in(cls, browser, username, password):
        try:
            browser.get(f"https://www.instagram.com/")

            # continue_as_button_xpath = '//*[@id]//section/main/article/div//button/span'
            # continue_as_button = cls.get_element(browser, By.XPATH, continue_as_button_xpath, timeout=4)
            # if continue_as_button is not None:
            #     continue_as_button.click()

            profile_icon_xpath = '//*[@id]//section/nav/div//span/img'
            profile_icon = cls.get_element(browser, By.XPATH, profile_icon_xpath, timeout=5)
            if profile_icon is not None:
                cls.save_cookies(username, password, browser.get_cookies())
                not_now_button_xpath = '/html/body//div/div/div/button[2]'
                not_now_button = cls.get_element(browser, By.XPATH, not_now_button_xpath, timeout=3)
                if not_now_button is not None:
                    not_now_button.click()
                return True

            browser.delete_all_cookies()
            cookies = cls.get_cookies(username, password)
            for cookie in cookies:
                browser.add_cookie(cookie)
            browser.get(f"https://www.instagram.com/")

            accept_cookies_xpath = '/html/body/div//button[2]'
            accept_cookies_button = cls.get_element(browser, By.XPATH, accept_cookies_xpath, timeout=2)
            if accept_cookies_button is not None:
                accept_cookies_button.click()


            profile_icon = cls.get_element(browser, By.XPATH, profile_icon_xpath)
            if profile_icon is not None:
                cls.save_cookies(username, password, browser.get_cookies())
                save_info_button_xpath = '//*[@id]/div//section/main//div/section/div/button'
                save_info_button = cls.get_element(browser, By.XPATH, save_info_button_xpath, timeout=3)
                if save_info_button is not None:
                    save_info_button.click()
                not_now_button_xpath = '/html/body//div/div/div/button[2]'
                not_now_button = cls.get_element(browser, By.XPATH, not_now_button_xpath, timeout=1)
                if not_now_button is not None:
                    not_now_button.click()
                return True

            else:
                accept_cookies_button_xpath = '/html/body/div[2]/div//div[2]/button[1]'
                accept_cookies_button = cls.get_element(browser, By.XPATH, accept_cookies_button_xpath, timeout=3)
                if accept_cookies_button is not None:
                    accept_cookies_button.click()

                login_field = cls.get_element(browser, By.XPATH, '//*[@id="loginForm"]/div/div[1]/div/label/input')
                login_field.send_keys(username)

                password_field = cls.get_element(browser, By.XPATH, '//*[@id="loginForm"]/div/div[2]/div/label/input')
                password_field.send_keys(password)

                log_in_button = cls.get_element(browser, By.XPATH, '//*[@id="loginForm"]/div/div[3]/button')
                log_in_button.click()

                profile_icon = cls.get_element(browser, By.XPATH, profile_icon_xpath)
                if profile_icon is None:
                    return False
                else:
                    cls.save_cookies(username, password, browser.get_cookies())
                    save_info_button_xpath = '//*[@id]/section/main/div/div/div/section/div/button'
                    save_info_button = cls.get_element(browser, By.XPATH, save_info_button_xpath, timeout=3)
                    if save_info_button is not None:
                        save_info_button.click()
                    return True

        except:
            Worker.__error_handler__(username=username, message="Аккаунт не произвел вход в браузер")
            return False

        finally:
            try:
                save_login_info_button_xpath = '//*[@id]/section/main//section/div/button'
                save_login_info_button_xpath = cls.get_element(browser, By.XPATH, save_login_info_button_xpath,
                                                               timeout=3)
                save_login_info_button_xpath.click()
            except:
                pass

    @classmethod
    def get_browser(cls, username: str, proxy: ProxyEntry=None) -> webdriver.Chrome:
        chrome_options = Options()
        chrome_options.headless = Selenium.HEADLESS

        chrome_options.add_argument("--disable-blink-features")
        # chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument(f'--user-data-dir={Settings.BROWSER_PROFILES_PATH}/{username}')
        chrome_options.add_argument(f'--profile-directory={username}')

        if proxy is not None:
            chrome_options.add_argument(f'--proxy-server={proxy.ip}:{proxy.port}')
        # chrome_options.add_argument("--incognito")
        # chrome_options.add_argument("--start-maximized")

        user_agent = cls.desktop_user_agents[Utils.username_hash(username) % len(cls.desktop_user_agents)]
        chrome_options.add_argument(f'user-agent={user_agent}')

        chrome_caps = DesiredCapabilities.CHROME
        chrome_caps['goog:loggingPrefs'] = {'performance': 'ALL'}
        logging.info(Settings.WEBDRIVER_LOCATION)
        browser = webdriver.Chrome(executable_path=Settings.WEBDRIVER_LOCATION,
                                   options=chrome_options,
                                   desired_capabilities=chrome_caps)
        browser.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                  const newProto = navigator.__proto__
                  delete newProto.webdriver
                  navigator.__proto__ = newProto
                  """
        })

        return browser

    @classmethod
    def get_element(cls, parent, by, arg, timeout = None):
        if timeout is None:
            timeout = cls.GET_ELEMENT_TIMEOUT

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                element = parent.find_element(by, arg)
                return element
            except:
                time.sleep(0.01)
        return None

    @classmethod
    def get_cookies(cls, username, password):
        if cls.__cookies__.get(username + password) is None:
            return list()
        else:
            return cls.__cookies__.get(username + password)

    @classmethod
    def save_cookies(cls, username, password, cookies: list):
        cls.__cookies__[username + password] = cookies.copy()
        Worker.save()

    @classmethod
    def remove_cookies(cls, username, password):
        cls.__cookies__[username + password] = None


class HidingProcessor:

    @classmethod
    def hiding(cls, user: User, account: AccountEntry, category: CategoryEntry, url: str):
        browser = None
        start_hour = datetime.now(tz=Settings.TIMEZONE).hour
        start_minute = datetime.now(tz=Settings.TIMEZONE).minute

        hiding = None

        block_count = 0
        errors_count = 0
        try:
            browser = Selenium.get_browser(account.username, account.proxy())
            if not Selenium.log_in(browser, account.username, account.password):
                Worker.bot.send_message(
                    chat_id=user.chat_id,
                    text=Texts.LOG_IN_FAILED_F.format(account.username)
                )
                return

            if url is None:
                browser.get(f"https://www.instagram.com/{account.username}/")
                first_post_xpath = '//*[@id]/section/main//div/article/div/div/div/div[1]/a'
                first_post = Selenium.get_element(browser, By.XPATH, first_post_xpath)
                url = first_post.get_attribute('href')

            if Stats.hidden_tags.get(url) is not None:
                category.remove_tags(Stats.hidden_tags[url])

            packs = category.packs
            hiding = Stats.Hiding(user, account, category, url, start_hour, start_minute, len(packs))
            Stats.hidings_in_progress.append(hiding)

            Worker.bot.send_message(
                chat_id=user.chat_id,
                text=Texts.HIDING_STARTED_FF.format(account.username, category.name)
            )
            user.set_account_in_use(account.username)

            retries = list()
            for pack in packs:
                try:
                    if hiding.stop or hiding.blocked:
                        break
                    elif block_count >= Settings.COMMENT_HIDING_BLOCK_SIZE:
                        block_count = 0
                        time.sleep(Settings.COMMENT_HIDING_BLOCK_INTERVAL)

                    cls.hide_pack(browser, hiding, pack)
                    block_count += 1

                    if pack != packs[-1]:
                        time.sleep(Settings.COMMENT_HIDING_INTERVAL + random.randint(0, 10))

                except:
                    errors_count += 1
                    if errors_count > 30:
                        hiding.blocked = True
                    if pack not in retries:
                        Worker.__error_handler__(username=account.username, message=f"Ошибка во время скрытия тегов\n"
                                                                                 f"{pack}")
                        retries.append(pack)
                        packs.append(pack)
                    else:
                        Worker.__error_handler__(username=account.username,
                                              message=f"Ошибка во время скрытия тегов, retry\n"
                                                      f"{pack}")
                    if errors_count % 10 == 0:
                        browser.get(url)
                    if hiding.stop:
                        break
                    time.sleep(20)

            Worker.bot.send_message(
                chat_id=user.chat_id,
                text=Texts.HIDING_ENDED_FFF.format(account.username, hiding.packs_completed, hiding.total_packs)
            )
            if hiding.blocked:
                Worker.bot.send_message(
                    chat_id=user.chat_id,
                    text=Texts.HIDING_BLOCKED
                )
                for chat_id in Settings.DEBUG_IDS:
                    Worker.bot.send_message(
                        chat_id=chat_id,
                        text=f"Аккаунт {account.username} заблокировали."
                    )

            if Settings.RETURN_HIDING_ENABLED and hiding.total_packs > 0:
                complete_percent = hiding.packs_completed / hiding.total_packs
                if complete_percent < Settings.RETURN_HIDING_PERCENT:
                    Database.Users.increase_access(user.chat_id, 1)
                    Worker.bot.send_message(chat_id=user.chat_id, text=Texts.HIDING_RETURNED)


        except:
            Worker.__error_handler__(username=account.username, message="Критическая ошибка во время __hiding__(), "
                                                                     "ошибка на потоке, поток был прерван полностью, "
                                                                     "пользователь не оповещен")

        finally:
            Stats.hidings_in_progress.remove(hiding)
            Stats.hidings_completed.append(hiding)
            user.remove_account_from_use(account.username)
            if browser is not None:
                browser.quit()

    @classmethod
    def hide_pack(cls, browser, hiding, pack):
        browser.get(hiding.url)
        time.sleep(1)

        try:
            browser.execute_script(
                'document.getElementsByTagName("article")[0].children[0].children[0].children[0].remove();')
        except:
            pass
        try:
            browser.execute_script('document.getElementsByTagName("ul")[0].children[0].remove();')
        except:
            pass
        finally:
            time.sleep(1)

        text_area_xpath = '//*[@id]//section/main//article//section//form/textarea'
        text_area = Selenium.get_element(browser, By.XPATH, text_area_xpath)
        text_area.click()
        time.sleep(1)

        comment = random.choice(Texts.COMMENTS)
        try:
            text_area = Selenium.get_element(browser, By.XPATH, text_area_xpath)
            text_area.send_keys(comment, Keys.ENTER)
            time.sleep(5)
        except:
            Worker.__error_handler__(username=hiding.account.username, message="reply send error")

        try:
            browser.execute_script('elems = document.getElementsByTagName("ul");')
            script = 'for (i = elems.length - 1; i >= 0; i--) ' \
                     '   try {' \
                     f'       if (!elems[i].innerText.toLowerCase().startsWith("{hiding.account.username.username.lower()}\\n")) ' \
                     '            elems[i].remove();' \
                     '   } catch (err) {console.log(err)};'
            browser.execute_script(script)
        except:
            pass

        time.sleep(1)

        comment_uls_xpath = '//*[@id]//section/main//div/article//div/ul/ul'
        comment_uls = browser.find_elements_by_xpath(comment_uls_xpath)
        reply_buttons_xpath = '//*[@id]//section/main//div/article//div/ul//div/li/div/div/div/div/div/button'
        reply_buttons = browser.find_elements_by_xpath(reply_buttons_xpath)
        comment_settings_buttons_xpath = '//*[@id]//section/main//div/article//div/ul/ul/div/li/div/div/div/div/div/div//button'
        comment_settings_buttons = browser.find_elements_by_xpath(comment_settings_buttons_xpath)

        is_reply_send = False
        is_comment_deleted = False
        for i in range(min(len(reply_buttons), len(comment_settings_buttons))):
            if hiding.account.username.lower() in comment_uls[i].text.lower():
                reply_buttons[i].click()
                time.sleep(5)

                text_area = Selenium.get_element(browser, By.XPATH, text_area_xpath)
                if hiding.account.username.lower() in text_area.text:
                    text_area.send_keys(pack, Keys.ENTER)
                    time.sleep(10)
                    is_reply_send = True

                try:
                    text_area = Selenium.get_element(browser, By.XPATH, text_area_xpath)
                    if (len(text_area.text)) > 2:
                        is_reply_send = False
                        hiding.blocked = True

                except:
                    pass

                ActionChains(browser).move_to_element(reply_buttons[i]).perform()
                time.sleep(1)
                comment_settings_buttons[i].click()
                time.sleep(2)
                delete_button_xpath = '/html/body/div//button[2]'
                delete_button = Selenium.get_element(browser, By.XPATH, delete_button_xpath)
                ActionChains(browser).move_to_element(delete_button).perform()
                time.sleep(1)
                delete_button.click()
                time.sleep(2)
                is_comment_deleted = True
                break

        if is_comment_deleted and is_reply_send:
            hiding.packs_completed += 1
            Stats.add_hidden_tags(hiding.url, pack.split(' '))
        elif not is_comment_deleted:
            Worker.__error_handler__(username=hiding.account.username, message="Комментарий не удален")
        elif not is_reply_send:
            Worker.__error_handler__(username=hiding.account.username, message="Ответ не отправился")


class Worker:
    bot = None

    handler_thread = None

    @classmethod
    def init(cls, bot, database):
        cls.bot = bot
        cls.database = database

        try:
            hidden_tags_file = open(Settings.HIDDEN_TAGS_SAVE_PATH, "r")
            Stats.hidden_tags = json.loads(hidden_tags_file.readline())
            print("Inited hidden tags:", len(Stats.hidden_tags))
        except BaseException as exc:
            print(f"Exception while reading {Settings.HIDDEN_TAGS_SAVE_PATH}:\n\t{exc}")

        try:
            cookies_file = open(Settings.COOKIES_SAVE_PATH, "r")
            Selenium.__cookies__ = json.loads(cookies_file.readline())
            print("Inited cookies:", len(Selenium.__cookies__))
        except BaseException as exc:
            print(f"Exception while reading {Settings.COOKIES_SAVE_PATH}:\n\t{exc}")

        cls.handler_thread = Thread(target=cls.__handler_threading__)
        cls.handler_thread.start()

        print("Worker: connected")

    @classmethod
    def save(cls):
        to_save = (
            (Settings.HIDDEN_TAGS_SAVE_PATH,        Stats.hidden_tags),
            (Settings.COOKIES_SAVE_PATH,            Selenium.__cookies__)
        )
        for path, obj in to_save:
            try:
                try:
                    os.remove(path)
                except:
                    pass
                file = open(path, "w")
                file.write(json.dumps(obj))
                file.close()
            except:
                cls.__error_handler__(message=f"Error while saving {path}")

        Stats.last_save = Stats.get_date()

    @classmethod
    def start_hiding(cls, user, account, category, url=None):
        hidings_count = Stats.hidings_count_by_id.get(user.chat_id)
        if not Settings.WORKER_ENABLED:
            cls.bot.send_message(chat_id=user.chat_id, text=Texts.WORKER_DISABLED)

        elif user.is_account_in_use(account.username):
            cls.bot.send_message(chat_id=user.chat_id, text=Texts.ACCOUNT_IN_USE_F.format(account.username))

        elif Database.Users.get_access(user.chat_id) <= 0 and user.chat_id not in Settings.ADMIN_IDS:
            cls.bot.send_message(chat_id=user.chat_id, text=Texts.ACCESS_NOT_PROVIDED_F.format(user.chat_id))

        elif user.chat_id not in Settings.ADMIN_IDS and \
                hidings_count is not None and hidings_count >= Settings.DAY_HIDINGS_LIMIT:
                cls.bot.send_message(user.chat_id, Texts.DAY_LIMIT_REACHED_F.format(Settings.DAY_HIDINGS_LIMIT))

        elif len(Stats.hidings_in_progress) >= Settings.WORKS_LIMIT:
            cls.bot.send_message(chat_id=user.chat_id, text=Texts.SERVER_OVERLOADED)

        else:
            if url is not None:
                url = url.replace('?utm_medium=copy_link', '')
            thread = Thread(
                target=HidingProcessor.hiding,
                args=[user, account, category, url]
            )
            thread.start()

            if hidings_count is None:
                Stats.hidings_count_by_id[user.chat_id] = 1
            else:
                Stats.hidings_count_by_id[user.chat_id] += 1

            Database.Users.decrease_access(user.chat_id, 1)

    @classmethod
    def delay_hiding(cls, user, account, category, tags, dt):
        category.add_tags(tags)
        Stats.delay_hidings.append(Stats.DelayHiding(user, account, category, dt))
        cls.bot.send_message(chat_id=user.chat_id,
                             text="Отложенное скрытие установлено")

    @classmethod
    def start_random_activity(cls):
        accounts = Database.Accounts.get_all()
        available_accounts = list()
        for account in accounts:
            last_use = Stats.last_account_use.get(account.username)
            if last_use is None or time.time() - last_use > Settings.ACCOUNT_ACTIVITY_REFRESH_TIME:
                if 'alowator' not in account.username:
                    user = Users.get_user(account.chat_id)
                    if not user.is_account_in_use(account.username):
                        available_accounts.append(account)

        if len(available_accounts) == 0:
            return

        account = random.choice(available_accounts)
        Stats.last_account_use[account.username] = time.time()
        Thread(target=cls.__random_activity__, args=[account]).start()

    @classmethod
    def __random_activity__(cls, account: AccountEntry):
        browser = None

        try:
            random_activity = Stats.RandomActivity(account)

            browser = Selenium.get_browser(account.username, account.proxy())
            Selenium.log_in(browser, account.username, account.password)

            time.sleep(7)

            # Stories watching
            story_xpath = '//*[@id]//section/main/section/div//ul/li/div/button'
            story = Selenium.get_element(browser, By.XPATH, story_xpath)
            story.click()
            time.sleep(3)

            time_stories_watching = random.randint(1, 13) * 60
            watch_start_time = time.time()
            while True:
                next_button_xpath = '//*[@id]//section/div/div/div/section/div/button[2]/div'
                next_button = Selenium.get_element(browser, By.XPATH, next_button_xpath)
                if next_button is not None:
                    next_button.click()
                    random_activity.stories += 1
                    time.sleep(random.randint(4, 10))

                close_button_xpath = '//*[@id]//section/div[3]/button'
                close_button = Selenium.get_element(browser, By.XPATH, close_button_xpath)
                if close_button is None:
                    break
                elif time.time() - watch_start_time > time_stories_watching:
                    close_button.click()
                    break

            # Posts liking
            button_ids_liked = list()
            pack_to_like = random.randint(2, 30)
            for i in range(pack_to_like):
                like_buttons_xpath = '//*[@id]//section/main/section/div[1]/div[2]/div/article/div/div[3]/div/div/section[1]/span[1]/button'
                like_buttons = browser.find_elements_by_xpath(like_buttons_xpath)
                for like_button in like_buttons:
                    if random.random() <= 0.9:
                        if like_button.id not in button_ids_liked:
                            try:
                                like_button.click()
                                button_ids_liked.append(like_button.id)
                                random_activity.likes += 1
                            except Exception as exc:
                                print(str(exc))
                                continue
                    time.sleep(random.randint(3, 7))

            time.sleep(3)

            Stats.random_activities.append(random_activity)

        except:
            cls.__error_handler__(username=account.username, message="Ошибка во время __random_activity__()")

        finally:
            if browser is not None:
                browser.quit()

    @classmethod
    def confirm_account(cls, user, username:str, password:str):
        if username.startswith('@'):
            username = username[1:]
        thread = Thread(
            target=cls.__confirm_account_thread__,
            args=[user, username, password]
        )
        thread.start()

    @classmethod
    def __confirm_account_thread__(cls, user, username, password):
        logging.info(f"confirm_account: {username}:{password}")
        browser = None
        confirmed = False

        try:
            cls.bot.send_message(
                chat_id=user.chat_id,
                text=Texts.ACCOUNT_CONFIRMATION_STARTED
            )
            browser = Selenium.get_browser(username)
            if Selenium.log_in(browser, username, password):
                Database.Accounts.add_account(user.chat_id, username, password)
                cls.bot.send_message(
                    chat_id=user.chat_id,
                    parse_mode=ParseMode.HTML,
                    text=Texts.LOG_IN_SUCCESSFUL
                )
            else:

                incorrect_password_label_id = 'slfErrorAlert'
                incorrect_password_label = Selenium.get_element(browser, By.ID, incorrect_password_label_id, timeout=5)
                if incorrect_password_label is not None:
                    cls.bot.send_message(
                        chat_id=user.chat_id,
                        text=Texts.INCORRECT_PASSWORD_OR_LOGIN
                    )
                else:
                    text_message_button_xpath = '//*[@id]/section/main//div/form/div[3]/button[1]'
                    text_message_button = Selenium.get_element(browser, By.XPATH, text_message_button_xpath, timeout=3)
                    if text_message_button is not None:
                        text_message_button.click()

                    message_elements_xpathes = ['//*[@id="verificationCodeDescription"]',
                                                '//*[@id]/section/main/div[2]/div/div/div[1]/div[1]',
                                                '//*[@id]/section/main/div[2]/div/div/div[2]/div[1]/h3',
                                                '//*[@id]/section/div/div/div[3]/form/div/div/label']

                    text = ""
                    for xpath in message_elements_xpathes:
                        message_element = Selenium.get_element(browser, By.XPATH, xpath, timeout=3)
                        if message_element is not None:
                            text = message_element.text
                        if len(text) > 0:
                            break

                    if len(text) == 0:
                        # cls.__error_handler__(username=username, message="While account confirmation info text wasn't found")
                        pass

                    send_code_button_xpath = '//*[@id]/section//div/form/span/button'
                    send_code_button = Selenium.get_element(browser, By.XPATH, send_code_button_xpath, timeout=15)
                    if send_code_button is not None:
                        send_code_button.click()

                    cls.bot.send_message(
                        chat_id=user.chat_id,
                        text=Texts.ENTER_EMAIL_OR_PHONE_CODE + f"\n{text}",
                        reply_markup=Keyboard.resend_code_menu()
                    )

                    try:
                        error_message_xpath = '//*[@id="twoFactorErrorAlert"]'
                        error_message = Selenium.get_element(browser, By.XPATH, error_message_xpath, timeout=3)
                        if error_message is not None:
                            cls.bot.send_message(
                                chat_id=user.chat_id,
                                text=Texts.CONFIRMATION_ERROR + f"\n{error_message.text}",
                            )
                    except:
                        # cls.__error_handler__(username=f"{username}:{password}", message="error_message")
                        pass

                    user.code = None
                    user.waiting = User.CODE

                    start_time = time.time()
                    while time.time() - start_time < 5 * 60:
                        code = user.code
                        if code is not None:
                            user.code = None

                        if code == Buttons.resend_code.text:
                            try:
                                code_resend_button_xpathes = ('//*[@id]/section/div/div/p/span/a',
                                                              '//*[@id]/section/main/div/div/div[1]/div/form/div[3]/button')
                                for xpath in code_resend_button_xpathes:
                                    code_resend_button = Selenium.get_element(browser, By.XPATH, xpath)
                                    if code_resend_button is None and xpath == code_resend_button_xpathes[-1]:
                                        cls.__error_handler__(username=f"{username}:{password}",
                                                              message="code_resend_button wasnt found")
                                    elif code_resend_button is not None:
                                        code_resend_button.click()
                                        break

                            except:
                                cls.__error_handler__(username=f"{username}:{password}", message="Code resend button error")
                            finally:
                                user.code = None

                        elif code is not None:
                            code_input_xpathes = (
                                '//*[@id]/section/main/div/div/div[1]/div/form/div[1]/div/label/input',
                                '//*[@id="security_code"]'
                            )
                            for xpath in code_input_xpathes:
                                code_input = Selenium.get_element(browser, By.XPATH, xpath)
                                if code_input is None and xpath == code_input_xpathes[-1]:
                                    cls.__error_handler__(username=f"{username}:{password}", message="code_input wasnt found")
                                elif code_input is not None:
                                    for i in range(10):
                                        code_input.send_keys(Keys.BACKSPACE)
                                        time.sleep(0.05)
                                    code_input.send_keys(code)
                                    break

                            time.sleep(1)

                            confirm_button_xpathes = (
                                '//*[@id]/section/main/div/div/div[1]/div/form/div[2]/button',
                                '//*[@id]/section//div/form/span/button'
                            )
                            for xpath in confirm_button_xpathes:
                                confirm_button = Selenium.get_element(browser, By.XPATH, xpath)
                                if confirm_button is None and xpath == confirm_button_xpathes[-1]:
                                    cls.__error_handler__(username=f"{username}:{password}", message="confirm_button wasnt found")
                                elif confirm_button is not None:
                                    confirm_button.click()
                                    break

                            profile_icon_xpath = '//*[@id]/section/nav/div[2]/div/div/div[3]/div/div[5]/span/img'
                            profile_icon = Selenium.get_element(browser, By.XPATH, profile_icon_xpath, timeout=15)
                            if profile_icon is not None:
                                Database.Accounts.add_account(user.chat_id, username, password)
                                cls.bot.send_message(
                                    chat_id=user.chat_id,
                                    parse_mode=ParseMode.HTML,
                                    text=Texts.CONFIRMED_SUCCESSFUL
                                )
                                confirmed = True
                                try:
                                    Selenium.save_cookies(username, password, browser.get_cookies())
                                except:
                                    pass
                                break
                            else:
                                cls.bot.send_message(
                                    chat_id=user.chat_id,
                                    parse_mode=ParseMode.HTML,
                                    text=Texts.WRONG_CODE
                                )

                            time.sleep(1)

                        profile_icon_xpath = '//*[@id]/section/nav/div[2]/div/div/div[3]/div/div[5]/span/img'
                        profile_icon = Selenium.get_element(browser, By.XPATH, profile_icon_xpath, timeout=2)
                        if profile_icon is not None:
                            Database.Accounts.add_account(user.chat_id, username, password)
                            cls.bot.send_message(
                                chat_id=user.chat_id,
                                parse_mode=ParseMode.HTML,
                                text=Texts.CONFIRMED_SUCCESSFUL
                            )
                            confirmed = True
                            try:
                                Selenium.save_cookies(username, password, browser.get_cookies())
                            except:
                                pass
                            try:
                                save_login_info_button_xpath = '//*[@id]/section/main//section/div/button'
                                save_login_info_button_xpath = Selenium.get_element(browser, By.XPATH,
                                                                               save_login_info_button_xpath, timeout=3)
                                save_login_info_button_xpath.click()
                            except:
                                pass
                            break

                        time.sleep(1)

                    if not confirmed:
                        cls.bot.send_message(
                            chat_id=user.chat_id,
                            parse_mode=ParseMode.HTML,
                            text=Texts.CODE_TIME_OUT
                        )

        except:
            cls.__error_handler__(username=f"{username}:{password}", message="Error while account confirmation")

        finally:
            user.clear_mode()
            if browser is not None:
                browser.quit()

    @classmethod
    def __handler_threading__(cls):
        prev_hour = datetime.now(tz=Settings.TIMEZONE).hour
        prev_minute = datetime.now(tz=Settings.TIMEZONE).minute

        while True:
            try:
                hour = datetime.now(tz=Settings.TIMEZONE).hour
                minute = datetime.now(tz=Settings.TIMEZONE).minute
                day = datetime.now(tz=Settings.TIMEZONE).day
                month = datetime.now(tz=Settings.TIMEZONE).month

                try:
                    if (hour, minute) == (23, 59) and (hour, minute) != (prev_hour, prev_minute):
                        Stats.report(cls.bot)
                        Stats.full_report(cls.bot)
                        Stats.random_activities_report(cls.bot)
                        Stats.reset()
                except:
                    cls.__error_handler__(message="Daily report error")

                try:
                    # if minute % 5 == 0 and (hour, minute) != (prev_hour, prev_minute):
                    if (hour, minute) != (prev_hour, prev_minute):
                        cls.save()
                except:
                    cls.__error_handler__(message="Worker.save() error")

                try:
                    Stats.cpu_percents.append(psutil.cpu_percent())
                    if len(Stats.cpu_percents) > 400:
                        Stats.cpu_percents = Stats.cpu_percents[100:]
                except:
                    cls.__error_handler__(message="cpu load stats getting error")

                try:
                    if (hour * 60 + minute) % 40 == 0 and (hour, minute) != (prev_hour, prev_minute):
                        cls.start_random_activity()
                except:
                    cls.__error_handler__(message="Worker.start_random_activity() error")

                try:
                    if Stats.last_update_bills is not None and \
                            datetime.now() - Stats.last_update_bills > timedelta(seconds=Settings.BILLS_UPDATE_RESTART_WATCHDOG):

                        PaymentSystem.updater_start(cls.bot)
                        Stats.last_update_bills = Stats.get_date()
                        cls.__error_handler__(message="Updater restarted")
                except:
                    cls.__error_handler__(message="PaymentSystem.updater_start error")

                try:
                    to_del = list()
                    for delay_hiding in Stats.delay_hidings:
                        try:
                            if delay_hiding.dt.hour == hour and delay_hiding.dt.minute == minute and \
                                delay_hiding.dt.day == day and delay_hiding.dt.month == month:
                                to_del.append(delay_hiding)
                                cls.start_hiding(delay_hiding.user, delay_hiding.account, delay_hiding.category)
                        except:
                            pass


                    for delay_hiding in to_del:
                        Stats.delay_hidings.remove(delay_hiding)

                except:
                    cls.__error_handler__(message="delay_hidings error")

                prev_hour = hour
                prev_minute = minute

            except:
                cls.__error_handler__(message="Handler thread fatal error!!!")

            finally:
                time.sleep(0.1)

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


class Utils:
    tag_corrector = lambda tag: tag if tag.startswith('#') else '#' + tag
    abc = '#_абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ0123456789'

    @classmethod
    def username_hash(cls, username: str):
        value = 0
        for x in username:
            value += ord(x)
        return value

    @classmethod
    def is_correct_tag(cls, tag):
        for letter in tag:
            if letter not in cls.abc:
                return False
        return True

    @classmethod
    def extract_tags(cls, string):
        good_tags, bad_tags = list(), list()
        tags = [cls.tag_corrector(x) for x in string.replace('\n', ' ').replace('#', ' ').split(' ') if x != '']
        for tag in tags:
            if cls.is_correct_tag(tag):
                good_tags.append(tag)
            else:
                bad_tags.append(tag)

        return good_tags, bad_tags


