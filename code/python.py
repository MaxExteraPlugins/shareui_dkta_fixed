from typing import Any, List

try:
    from base_plugin import BasePlugin, MethodHook
except Exception:
    from base_plugin import BasePlugin

    class MethodHook:
        pass

from hook_utils import find_class

__id__ = "shareui_dkta_fixed"
__name__ = "Don't kill the download! [fixed]"
__description__ = "[fixed by @maxExteraPlugins] Continues downloading files in the background when exiting the chat."
__author__ = "@itNotMax - @MaxExteraPlugins, original: @shareui"
__version__ = "1.10.0"
__icon__ = "MaxExteraPluginsStickers/27"
__min_version__ = "12.10.6"
__app_version__ = ">=12.2.10"
__sdk_version__ = ">=1.4.3.3"

WAKE_KEY = "block_sleep_while_downloading"

PRIORITY_LOW = 0
POLL_INTERVAL_MS = 7000
MSG_CLASS = "org.telegram.messenger.MessageObject"


def _setting(plugin, key, default):
    try:
        return bool(plugin.get_setting(key, default))
    except Exception:
        try:
            value = plugin.settings.get(key, default)
            return bool(value)
        except Exception:
            return default


def _try_declared_method(cls, name, param_types):
    """Chaquopy exposes Class.getDeclaredMethod(name, *types) on JavaClass
    proxies, but NOT getDeclaredMethods(). Look the method up by signature."""
    try:
        m = cls.getDeclaredMethod(name, *param_types)
        if m is not None:
            return m
    except Exception:
        pass
    return None


def _is_message_parent(parent):
    if parent is None:
        return False
    try:
        return parent.getClass().getName() == MSG_CLASS
    except Exception:
        return False


def _should_keep_download(plugin, target):
    try:
        parent = target.parentObject
        if not _is_message_parent(parent):
            return False
        if bool(parent.loadingCancelled):
            return False
        return True
    except Exception:
        return False


def _should_keep_cancel_load(parent_msg):
    """User-initiated pause/cancel must NOT be blocked.
    Cleanup on cell detach (auto cancel) goes through
    ChatMessageCell.cancelLoading, so we prevent only that path."""
    if parent_msg is None:
        return False
    try:
        if bool(parent_msg.loadingCancelled):
            return False
        return True
    except Exception:
        return False


class _DualHook(MethodHook):
    """SDK hook engine looks up snake_case callbacks (before_hooked_method);
    camelCase aliases kept for compatibility with older SDK versions."""

    def before_hooked_method(self, param):
        return self._before_hooked_method(param)

    def beforeHookedMethod(self, param):
        return self._before_hooked_method(param)

    def after_hooked_method(self, param):
        return self._after_hooked_method(param)

    def afterHookedMethod(self, param):
        return self._after_hooked_method(param)

    def _before_hooked_method(self, param):
        return None

    def _after_hooked_method(self, param):
        return None


class PriorityHook(_DualHook):
    def __init__(self, plugin):
        self.plugin = plugin

    def _before_hooked_method(self, param):
        try:
            if int(param.args[0]) == PRIORITY_LOW:
                param.setResult(None)
        except Exception:
            pass
        return None


class CancelLoadingHook(_DualHook):
    """Автоотмена при отсоединении клетки: ChatMessageCell.cancelLoading(msg).
    Блокируется ТОЛЬКО эта автоматическая отмена (выход из чата/скролл).
    Пользовательские пауза/отмена (SearchDownloadsContainer.cancelLoadFile)
    идут мимо cancelLoading и остаются нетронутыми."""

    def __init__(self, plugin):
        self.plugin = plugin

    def _before_hooked_method(self, param):
        try:
            msg = param.args[0] if param.args else None
            if _is_message_parent(msg) and _should_keep_cancel_load(msg):
                param.setResult(None)
        except Exception as e:
            self.plugin.log("[CL] error: %s" % e)
        return None



# ============================================================
# MaxExteraPlugins Shared Author & Channel Subscription Module
# ============================================================

# ============================================================
# MaxExteraPlugins Shared Author & Channel Subscription Module
# ============================================================
class AuthorChannelHelper:
    CONFIG_URL = "https://raw.githubusercontent.com/MaxExteraPlugins/config/main/links.json"

    DEFAULT_LINKS = {
        "channel_username": "MaxExteraPlugins",
        "channel_url": "https://t.me/MaxExteraPlugins",
        "trial_days": 7,
        "header": {"ru": "MaxExteraPlugins", "en": "MaxExteraPlugins"},
        "buttons": [
            {"title": {"ru": "Канал автора", "en": "Author's Channel"}, "icon": "msg_channel", "url": "https://t.me/MaxExteraPlugins"},
            {"title": {"ru": "Поддержать автора", "en": "Support author"}, "icon": "msg_share", "url": "https://t.me/itNotMax"},
            {"title": {"ru": "Сообщить о баге", "en": "Report a bug"}, "icon": "msg_help", "url": "https://t.me/itNotMax"}
        ]
    }

    _TEXTS = {
        "install_card_title": {"ru": "Спасибо за установку!", "en": "Thank you for installing!"},
        "install_card_msg": {
            "ru": "Надеемся, что плагин будет вам полезен!\n\nМы делаем плагины бесплатными и доступными для всех: пожалуйста, поддержите нас подпиской. Там будут только важные новости, обновления и розыгрыши.",
            "en": "We hope this plugin will be useful to you!\n\nWe keep our plugins free and open for everyone: please support us with a subscription. We only post key news, updates, and giveaways."
        },
        "subscribe_btn": {"ru": "Подписаться", "en": "Subscribe"},
        "remind_later_btn": {"ru": "Напомнить позже", "en": "Remind later"},
        "check_sub_btn": {"ru": "Проверить подписку", "en": "Check subscription"},
        "trial_expired_title": {"ru": "Пожалуйста, подпишитесь на канал", "en": "Please subscribe to the channel"},
        "trial_expired_msg": {
            "ru": "Пожалуйста, подпишитесь на наш официальный канал.\n\nМы делаем плагины бесплатно, ничего не требуя взамен. До подписки функции плагина временно приостановлены.",
            "en": "Please subscribe to our official channel.\n\nWe develop plugins for free and ask nothing in return. Plugin features are paused until you subscribe."
        },
        "sub_thank_you": {"ru": "Спасибо за подписку на наш канал!", "en": "Thank you for subscribing to our channel!"},
        "sub_thank_you_after_expired": {"ru": "Спасибо за подписку на наш канал!\nПлагин продолжит работу!", "en": "Thank you for subscribing to our channel!\nThe plugin will continue working!"},
        "sub_not_found": {"ru": "Подписка не обнаружена. Пожалуйста, подпишитесь на канал.", "en": "Subscription not found. Please subscribe to the channel."},
        "settings_channel": {"ru": "Канал автора", "en": "Author's Channel"},
        "settings_donate": {"ru": "Поддержать автора", "en": "Support author"},
        "settings_bug_report": {"ru": "Сообщить о баге", "en": "Report a bug"}
    }

    @classmethod
    def is_ru(cls) -> bool:
        try:
            from org.telegram.messenger import LocaleController
            cur = str(LocaleController.getInstance().getCurrentLocale().getLanguage() or "").lower()
            if cur.startswith(("ru", "uk", "be")): return True
            if cur: return False
        except Exception:
            pass
        try:
            from java.util import Locale
            code = str(Locale.getDefault().getLanguage() or "").lower()
            if code.startswith(("ru", "uk", "be")): return True
        except Exception:
            pass
        return False

    @classmethod
    def tr(cls, key: str) -> str:
        entry = cls._TEXTS.get(key, {})
        return entry.get("ru" if cls.is_ru() else "en", entry.get("en", key))

    def __init__(self, plugin, icon_sticker=None):
        self.plugin = plugin
        self.icon_sticker = icon_sticker or getattr(plugin, "__icon__", "MaxExteraPluginsStickers/1")
        self._stopped = False
        self._active_dialog = None
        self._last_known_sub = None

    def on_load(self):
        self._stopped = False
        self._active_dialog = None
        self._last_known_sub = None
        self._load_remote_links_async()
        self._check_initial_subscription_flow()
        self._start_subscription_watcher()

    def on_event(self, event_type):
        try:
            name = str(event_type).upper()
            if name.endswith("START") or name.endswith("RESUME"):
                self._check_subscription_change_instant()
        except Exception:
            pass

    def on_unload(self):
        self._stopped = True
        self._dismiss_active_dialog()

    def _get_links(self) -> dict:
        raw = self.plugin.get_setting("remote_links_cache", None)
        if raw:
            try:
                import json
                data = json.loads(raw)
                if isinstance(data, dict): return data
            except Exception:
                pass
        return self.DEFAULT_LINKS

    def _load_remote_links_async(self):
        def worker():
            try:
                import urllib.request, json
                req = urllib.request.Request(self.CONFIG_URL, headers={"User-Agent": "MaxExteraPlugins"})
                with urllib.request.urlopen(req, timeout=4) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode("utf-8"))
                        if isinstance(data, dict):
                            self.plugin.set_setting("remote_links_cache", json.dumps(data))
                            self._resolve_channel_in_telegram(data.get("channel_username", "MaxExteraPlugins"))
            except Exception:
                pass
        import threading
        t = threading.Thread(target=worker, daemon=True)
        t.start()

    def _open_url(self, url: str, view=None):
        try:
            from org.telegram.messenger.browser import Browser
            from org.telegram.messenger import ApplicationLoader
            from client_utils import get_last_fragment
            ctx = None
            if view is not None:
                ctx = view.getContext()
            if ctx is None:
                frag = get_last_fragment()
                if frag is not None:
                    ctx = frag.getParentActivity()
            if ctx is None:
                ctx = ApplicationLoader.applicationContext
            Browser.openUrl(ctx, url)
        except Exception:
            pass

    def _resolve_channel_in_telegram(self, username: str):
        try:
            from org.telegram.messenger import UserConfig, MessagesController
            from org.telegram.tgnet import TLRPC, ConnectionsManager, RequestDelegate
            clean_user = username.lstrip("@")
            acc = int(UserConfig.selectedAccount)
            mc = MessagesController.getInstance(acc)
            if not mc: return
            req = TLRPC.TL_contacts_resolveUsername()
            req.username = clean_user
            helper_ref = self
            class Delegate(RequestDelegate):
                def run(self, response, error):
                    if error is None and response is not None:
                        chats = getattr(response, "chats", None)
                        if chats is not None and chats.size() > 0:
                            mc.putChats(chats, False)
                            c = chats.get(0)
                            cid = getattr(c, "id", 0)
                            if cid > 0:
                                helper_ref.plugin.set_setting("resolved_channel_id", int(cid))
            ConnectionsManager.getInstance(acc).sendRequest(req, Delegate())
        except Exception:
            pass

    def is_subscribed(self) -> bool:
        try:
            from org.telegram.messenger import UserConfig, MessagesController
            links = self._get_links()
            target = str(links.get("channel_username", "MaxExteraPlugins") or "MaxExteraPlugins").lower().lstrip("@")
            saved_cid = self.plugin.get_setting("resolved_channel_id", 0)

            for acc in range(UserConfig.MAX_ACCOUNT_COUNT):
                uconf = UserConfig.getInstance(acc)
                if not uconf.isClientActivated(): continue
                mc = MessagesController.getInstance(acc)
                if not mc: continue

                if saved_cid:
                    try:
                        from java.lang import Long as JLong
                        c = mc.getChat(JLong(int(saved_cid)))
                        if c is not None:
                            left = bool(getattr(c, "left", True))
                            kicked = bool(getattr(c, "kicked", False))
                            if not left and not kicked: return True
                    except Exception:
                        pass

                try:
                    chat = mc.getUserOrChat(target)
                    if chat is not None:
                        cid = getattr(chat, "id", 0)
                        if cid and not saved_cid:
                            self.plugin.set_setting("resolved_channel_id", int(cid))
                        left = bool(getattr(chat, "left", True))
                        kicked = bool(getattr(chat, "kicked", False))
                        if not left and not kicked: return True
                except Exception:
                    pass

                try:
                    dialogs = mc.allDialogs
                    if dialogs is not None:
                        limit = min(dialogs.size(), 300)
                        for i in range(limit):
                            d = dialogs.get(i)
                            did = getattr(d, "id", 0)
                            if did < 0:
                                from java.lang import Long as JLong
                                c = mc.getChat(JLong(-did))
                                if c is not None:
                                    uname = str(getattr(c, "username", "") or "").lower()
                                    if uname == target:
                                        cid = getattr(c, "id", 0)
                                        if cid and not saved_cid:
                                            self.plugin.set_setting("resolved_channel_id", int(cid))
                                        left = bool(getattr(c, "left", True))
                                        kicked = bool(getattr(c, "kicked", False))
                                        if not left and not kicked: return True
                except Exception:
                    pass
        except Exception:
            pass
        return False

    def is_allowed(self) -> bool:
        import time
        if self.is_subscribed():
            if not self.plugin.get_setting("was_subscribed", False):
                was_exp = bool(self.plugin.get_setting("was_expired_state", False))
                self.plugin.set_setting("was_subscribed", True)
                self.plugin.set_setting("was_expired_state", False)
                self._notify_subscribed(was_expired=was_exp)
            return True

        if self.plugin.get_setting("was_expired_state", False) or self.plugin.get_setting("was_subscribed", False):
            self.plugin.set_setting("was_subscribed", False)
            self.plugin.set_setting("was_expired_state", True)
            self._show_expired_card()
            return False

        now = time.time()
        install_time = float(self.plugin.get_setting("install_time", 0.0) or 0.0)
        if install_time <= 0:
            install_time = now
            self.plugin.set_setting("install_time", install_time)

        trial_days = float(self._get_links().get("trial_days", 7))
        trial_sec = trial_days * 86400.0

        if (now - install_time) < trial_sec:
            return True

        self.plugin.set_setting("was_expired_state", True)
        self._show_expired_card()
        return False

    def prepend_settings(self, original_items=None) -> list:
        from ui.settings import Header, Text, Divider

        # Prevent double-prepending
        if original_items and any(getattr(x, "text", "") == "MaxExteraPlugins" for x in original_items if type(x).__name__ == "Header"):
            return original_items

        links = self._get_links()
        buttons_config = links.get("buttons")

        author_items = []
        if isinstance(buttons_config, list):
            for btn in buttons_config:
                if not isinstance(btn, dict): continue
                url = str(btn.get("url") or "").strip()
                if not url: continue

                title_data = btn.get("title")
                if isinstance(title_data, dict):
                    title = title_data.get("ru" if self.is_ru() else "en") or title_data.get("en") or title_data.get("ru") or ""
                elif isinstance(title_data, str) and title_data:
                    title = title_data
                else:
                    title = btn.get("title_ru" if self.is_ru() else "title_en") or btn.get("title_ru") or btn.get("title_en") or ""

                if not title: continue
                icon = str(btn.get("icon") or "msg_channel").strip()

                def make_click(u):
                    return lambda v=None: self._open_url(u, v)

                author_items.append(Text(text=title, icon=icon, on_click=make_click(url)))
        else:
            for k, text_key, icon_name in [
                ("channel_url", "settings_channel", "msg_channel"),
                ("donate_url", "settings_donate", "msg_share"),
                ("bug_report_url", "settings_bug_report", "msg_help")
            ]:
                u = str(links.get(k) or "").strip()
                if u:
                    author_items.append(Text(text=self.tr(text_key), icon=icon_name, on_click=lambda v=None, target_u=u: self._open_url(target_u, v)))

        res = []
        if author_items:
            hdr = links.get("header") or "MaxExteraPlugins"
            if isinstance(hdr, dict):
                hdr_text = hdr.get("ru" if self.is_ru() else "en") or hdr.get("ru") or hdr.get("en") or "MaxExteraPlugins"
            else:
                hdr_text = str(hdr)
            res.append(Header(text=hdr_text))
            res.extend(author_items)
            res.append(Divider())

        # Clean original_items by removing any old "Информация" / "Information" category
        cleaned_items = []
        if original_items:
            skipping_info = False
            for item in original_items:
                item_cls = type(item).__name__
                if item_cls == "Header":
                    txt = str(getattr(item, "text", "") or getattr(item, "title", "") or "").lower()
                    if "информ" in txt or "inform" in txt:
                        skipping_info = True
                        continue
                    else:
                        skipping_info = False
                elif skipping_info and item_cls == "Divider":
                    skipping_info = False
                    continue

                if not skipping_info:
                    cleaned_items.append(item)

        res.extend(cleaned_items)
        return res

    def _dismiss_active_dialog(self):
        try:
            if self._active_dialog is not None:
                self._active_dialog.dismiss()
        except Exception:
            pass
        self._active_dialog = None

    def _is_dialog_active(self) -> bool:
        try:
            if self._active_dialog is not None:
                return bool(self._active_dialog.isShowing())
        except Exception:
            pass
        return False

    def _notify_subscribed(self, was_expired=False):
        self.plugin.set_setting("was_subscribed", True)
        from ui.bulletin import BulletinHelper
        msg_key = "sub_thank_you_after_expired" if was_expired else "sub_thank_you"
        BulletinHelper.show_success(self.tr(msg_key))

    def _check_subscription_change_instant(self):
        try:
            from android_utils import run_on_ui_thread
            cur_sub = self.is_subscribed()
            prev_sub = self._last_known_sub
            if prev_sub is not None and prev_sub != cur_sub:
                self._last_known_sub = cur_sub
                if cur_sub:
                    was_exp = bool(self.plugin.get_setting("was_expired_state", False))
                    self.plugin.set_setting("was_subscribed", True)
                    self.plugin.set_setting("was_expired_state", False)
                    self._dismiss_active_dialog()
                    self._notify_subscribed(was_expired=was_exp)
                else:
                    self.plugin.set_setting("was_subscribed", False)
                    self.plugin.set_setting("was_expired_state", True)
                    self._dismiss_active_dialog()
                    self._show_expired_card()
            else:
                self._last_known_sub = cur_sub
        except Exception:
            pass

    def _start_subscription_watcher(self):
        def watcher_loop():
            import time
            from android_utils import run_on_ui_thread
            time.sleep(2.0)
            if self._stopped: return
            self._last_known_sub = self.is_subscribed()

            while not self._stopped:
                try:
                    time.sleep(2.0)
                    if self._stopped: break
                    cur_sub = self.is_subscribed()
                    prev_sub = self._last_known_sub

                    if prev_sub is not None and prev_sub != cur_sub:
                        self._last_known_sub = cur_sub
                        if cur_sub:
                            was_exp = bool(self.plugin.get_setting("was_expired_state", False))
                            self.plugin.set_setting("was_subscribed", True)
                            self.plugin.set_setting("was_expired_state", False)
                            def on_sub():
                                self._dismiss_active_dialog()
                                self._notify_subscribed(was_expired=was_exp)
                            run_on_ui_thread(on_sub)
                        else:
                            self.plugin.set_setting("was_subscribed", False)
                            self.plugin.set_setting("was_expired_state", True)
                            def on_unsub():
                                self._dismiss_active_dialog()
                                self._show_expired_card()
                            run_on_ui_thread(on_unsub)
                    else:
                        self._last_known_sub = cur_sub
                except Exception:
                    pass
        import threading
        t = threading.Thread(target=watcher_loop, daemon=True)
        t.start()

    def _check_initial_subscription_flow(self):
        def flow():
            import time
            try:
                now = time.time()
                install_time = float(self.plugin.get_setting("install_time", 0.0) or 0.0)
                if install_time <= 0:
                    install_time = now
                    self.plugin.set_setting("install_time", install_time)

                is_sub = self.is_subscribed()
                self._last_known_sub = is_sub
                was_sub = bool(self.plugin.get_setting("was_subscribed", False))
                was_exp = bool(self.plugin.get_setting("was_expired_state", False))

                if is_sub:
                    if not was_sub:
                        self.plugin.set_setting("was_subscribed", True)
                        self.plugin.set_setting("was_expired_state", False)
                        self._notify_subscribed(was_expired=was_exp)
                    return

                if was_sub or was_exp:
                    self.plugin.set_setting("was_subscribed", False)
                    self.plugin.set_setting("was_expired_state", True)
                    self._show_expired_card()
                    return

                trial_days = float(self._get_links().get("trial_days", 7))
                trial_sec = trial_days * 86400.0
                last_remind = float(self.plugin.get_setting("last_remind_time", 0.0) or 0.0)

                if (now - install_time) < trial_sec:
                    if last_remind <= 0 or (now - last_remind) >= trial_sec:
                        self._show_welcome_card()
                else:
                    self.plugin.set_setting("was_expired_state", True)
                    self._show_expired_card()
            except Exception:
                pass
        from android_utils import run_on_ui_thread
        run_on_ui_thread(flow, 1500)

    def _create_card_content(self, act, title_text, message_text):
        try:
            from android.widget import LinearLayout, TextView
            from android.view import Gravity
            from android.graphics import Typeface
            from org.telegram.messenger import AndroidUtilities, UserConfig, MediaDataController
            from org.telegram.ui.ActionBar import Theme
            from org.telegram.ui.Components import BackupImageView

            dp = AndroidUtilities.dp
            layout = LinearLayout(act)
            layout.setOrientation(LinearLayout.VERTICAL)
            layout.setGravity(Gravity.CENTER_HORIZONTAL)
            layout.setPadding(dp(24), dp(16), dp(24), dp(6))

            size = dp(76)
            iv = BackupImageView(act)
            iv.setRoundRadius(dp(18))
            lp_iv = LinearLayout.LayoutParams(size, size)
            lp_iv.gravity = Gravity.CENTER_HORIZONTAL
            lp_iv.setMargins(0, dp(4), 0, dp(16))
            iv.setLayoutParams(lp_iv)

            try:
                acc = int(UserConfig.selectedAccount)
                mdc = MediaDataController.getInstance(acc)
                raw_icon = str(self.icon_sticker)
                if "/" in raw_icon:
                    pack, idx_s = raw_icon.split("/", 1)
                    mdc.setPlaceholderImageByIndex(iv, pack, int(idx_s), "150_150")
            except Exception:
                pass
            layout.addView(iv)

            if title_text:
                tt = TextView(act)
                tt.setText(title_text)
                tt.setTextSize(19.0)
                tt.setTypeface(None, Typeface.BOLD)
                tt.setTextColor(Theme.getColor(Theme.key_dialogTextBlack))
                tt.setGravity(Gravity.CENTER_HORIZONTAL)
                lp_t = LinearLayout.LayoutParams(-1, -2)
                lp_t.setMargins(0, 0, 0, dp(12))
                tt.setLayoutParams(lp_t)
                layout.addView(tt)

            if message_text:
                mt = TextView(act)
                mt.setText(message_text)
                mt.setTextSize(15.0)
                mt.setTextColor(Theme.getColor(Theme.key_dialogTextBlack))
                mt.setLineSpacing(float(dp(3)), 1.0)
                mt.setGravity(Gravity.CENTER_HORIZONTAL)
                lp_m = LinearLayout.LayoutParams(-1, -2)
                mt.setLayoutParams(lp_m)
                layout.addView(mt)

            return layout
        except Exception:
            return None

    def _show_welcome_card(self):
        def show():
            try:
                if self._is_dialog_active(): return
                from client_utils import get_last_fragment
                frag = get_last_fragment()
                if not frag: return
                act = frag.getParentActivity()
                if not act: return

                links = self._get_links()
                url = links.get("channel_url", "https://t.me/MaxExteraPlugins")

                from ui.alert import AlertDialogBuilder
                b = AlertDialogBuilder(act)
                content = self._create_card_content(act, self.tr("install_card_title"), self.tr("install_card_msg"))
                if content is not None:
                    b.set_view(content)
                else:
                    b.set_title(self.tr("install_card_title"))
                    b.set_message(self.tr("install_card_msg"))

                def on_sub(d, w):
                    self._dismiss_active_dialog()
                    self._open_url(url)
                    def check_after():
                        if self.is_subscribed():
                            self._notify_subscribed(was_expired=False)
                    from android_utils import run_on_ui_thread
                    run_on_ui_thread(check_after, 3000)

                def on_later(d, w):
                    import time
                    self._dismiss_active_dialog()
                    self.plugin.set_setting("last_remind_time", time.time())

                b.set_positive_button(self.tr("subscribe_btn"), on_sub)
                b.set_negative_button(self.tr("remind_later_btn"), on_later)
                self._active_dialog = b.show()
            except Exception:
                pass
        from android_utils import run_on_ui_thread
        run_on_ui_thread(show)

    def _show_expired_card(self):
        def show():
            try:
                if self._is_dialog_active(): return
                from client_utils import get_last_fragment
                frag = get_last_fragment()
                if not frag: return
                act = frag.getParentActivity()
                if not act: return

                links = self._get_links()
                url = links.get("channel_url", "https://t.me/MaxExteraPlugins")

                from ui.alert import AlertDialogBuilder
                from ui.bulletin import BulletinHelper
                b = AlertDialogBuilder(act)
                content = self._create_card_content(act, self.tr("trial_expired_title"), self.tr("trial_expired_msg"))
                if content is not None:
                    b.set_view(content)
                else:
                    b.set_title(self.tr("trial_expired_title"))
                    b.set_message(self.tr("trial_expired_msg"))

                def on_sub(d, w):
                    self._dismiss_active_dialog()
                    self._open_url(url)
                    def check_after():
                        if self.is_subscribed():
                            self.plugin.set_setting("was_subscribed", True)
                            self.plugin.set_setting("was_expired_state", False)
                            self._notify_subscribed(was_expired=True)
                    from android_utils import run_on_ui_thread
                    run_on_ui_thread(check_after, 3000)

                def on_check(d, w):
                    self._dismiss_active_dialog()
                    if self.is_subscribed():
                        self.plugin.set_setting("was_subscribed", True)
                        self.plugin.set_setting("was_expired_state", False)
                        self._notify_subscribed(was_expired=True)
                    else:
                        BulletinHelper.show_error(self.tr("sub_not_found"))
                        from android_utils import run_on_ui_thread
                        run_on_ui_thread(self._show_expired_card, 500)

                b.set_positive_button(self.tr("subscribe_btn"), on_sub)
                b.set_negative_button(self.tr("check_sub_btn"), on_check)
                self._active_dialog = b.show()
            except Exception:
                pass
        from android_utils import run_on_ui_thread
        run_on_ui_thread(show)


class ShareuiDktaFixed(BasePlugin):

    def on_plugin_load(self):
        self._author_helper = AuthorChannelHelper(self, icon_sticker=globals().get("__icon__", "MaxExteraPluginsStickers/1"))
        self._author_helper.on_load()
        self._unhook_refs = []
        self.__dict__["_wake_lock"] = None
        self.__dict__["_polling"] = False
        self._install_hooks()
        if _setting(self, WAKE_KEY, False):
            self._start_polling()

    def on_plugin_unload(self):
        if hasattr(self, "_author_helper"):
            self._author_helper.on_unload()
        try:
            self._stop_polling()
        except Exception:
            pass
        try:
            self._release_wake_lock()
        except Exception:
            pass
        for h in getattr(self, "_unhook_refs", []):
            try:
                self.unhook_method(h)
            except Exception:
                pass
        self._unhook_refs.clear()

    def on_app_event(self, event):
        if hasattr(self, "_author_helper"):
            self._author_helper.on_event(event)
        try:
            name = str(event).lower()
            if "pause" in name or "resume" in name or "start" in name:
                self._sync_wake_lock()
        except Exception:
            pass

    # ----------------------------------------------------------
    # hooks
    # ----------------------------------------------------------

    def _install_hooks(self):
        try:
            cmc = find_class("org.telegram.ui.Cells.ChatMessageCell")
            msg_cls = find_class("org.telegram.messenger.MessageObject")
        except Exception as e:
            self.log("required classes not found: %s" % e)
            return

        # Path A: hook_all_methods finds overloads by name. The SDK throws an
        # AttributeError on JavaClass.getName() AFTER installing the hook on
        # some builds - the hook is installed, so the error is swallowed.
        try:
            handlers = self.hook_all_methods(cmc, "cancelLoading", CancelLoadingHook(self))
            for h in handlers or []:
                self._keep_unhook(h)
        except Exception:
            pass

        # Path B (new SDK >= 1.4.4.2): per-method via getDeclaredMethod proxy.
        if hasattr(cmc, "getDeclaredMethod"):
            try:
                from java.lang import Boolean as JBool
                for params in ([msg_cls], [msg_cls, JBool.TYPE], [msg_cls, JBool.TYPE, JBool.TYPE]):
                    m = _try_declared_method(cmc, "cancelLoading", params)
                    if m is not None:
                        self._safe_hook(m, CancelLoadingHook(self), "cancelLoading arity=%d" % len(params))
            except Exception as e:
                self.log("per-method cancelLoading path failed: %s" % e)
            try:
                from java.lang import Integer as JInt, String as JString
                fl = find_class("org.telegram.messenger.FileLoader")
                tm = _try_declared_method(
                    fl, "changePriority",
                    [JInt.TYPE,
                     find_class("org.telegram.tgnet.TLRPC$Document"),
                     find_class("org.telegram.messenger.SecureDocument"),
                     find_class("org.telegram.messenger.WebFile"),
                     find_class("org.telegram.tgnet.TLRPC$FileLocation"),
                     JString, JString],
                )
                if tm is not None:
                    self._safe_hook(tm, PriorityHook(self), "FileLoader.changePriority")
            except Exception as e:
                self.log("PriorityHook setup skipped: %s" % e)
        else:
            try:
                fl = find_class("org.telegram.messenger.FileLoader")
                handlers = self.hook_all_methods(fl, "changePriority", PriorityHook(self))
                for h in handlers or []:
                    self._keep_unhook(h)
            except Exception:
                pass

    def _safe_hook(self, method, hook, label="?"):
        """hook_method on the exact method; falls back to hook_all_methods
        on older SDKs that lack hook_method."""
        installed = False
        try:
            handler = self.hook_method(method, hook)
            self._keep_unhook(handler)
            installed = handler is not None
        except Exception as e:
            self.log("hook_method failed for %s: %s" % (label, e))
        if not installed:
            try:
                self._keep_unhook(self.hook_all_methods(method.getDeclaringClass().getClass(), method.getName(), hook))
                installed = True
            except Exception as e:
                self.log("hook_all_methods fallback failed for %s: %s" % (label, e))

    def _keep_unhook(self, handler):
        if handler is None:
            return
        refs = getattr(self, "_unhook_refs", None)
        if refs is not None:
            refs.append(handler)

    # ----------------------------------------------------------
    # wake lock: block sleep while downloads are in progress
    # ----------------------------------------------------------

    def _start_polling(self):
        try:
            if getattr(self, "_polling", False):
                return
            self.__dict__["_polling"] = True
            self._poll_tick()
        except Exception:
            pass

    def _stop_polling(self):
        self.__dict__["_polling"] = False

    def _poll_tick(self):
        if not getattr(self, "_polling", False):
            return
        try:
            self._sync_wake_lock()
        except Exception:
            pass
        if not getattr(self, "_polling", False):
            return
        try:
            self._post_delayed(self._poll_tick, POLL_INTERVAL_MS)
        except Exception:
            pass

    def _sync_wake_lock(self):
        if not getattr(self, "_polling", False) or not _setting(self, WAKE_KEY, False):
            self._release_wake_lock()
            return
        if self._has_active_downloads():
            self._acquire_wake_lock()
        else:
            self._release_wake_lock()

    def _has_active_downloads(self):
        try:
            from java.util import ArrayList as JArrayList
            from org.telegram.messenger import FileLoader, UserConfig
            accounts = [0]
            try:
                accounts = range(UserConfig.getActivatedAccountsCount())
            except Exception:
                pass
            for account in accounts:
                loader = FileLoader.getInstance(account)
                files = JArrayList()
                loader.getCurrentLoadingFiles(files)
                if files is not None and files.size() > 0:
                    return True
        except Exception:
            pass
        return False

    def _acquire_wake_lock(self):
        try:
            if getattr(self, "_wake_lock", None) is not None:
                return
            from android.os import PowerManager
            from org.telegram.messenger import ApplicationLoader
            context = None
            try:
                context = ApplicationLoader.applicationContext
            except Exception:
                context = None
            if context is None:
                return
            pm = context.getSystemService(PowerManager.POWER_SERVICE)
            if pm is None:
                return
            wl = pm.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "extera:shareui_dkta_fixed")
            try:
                wl.setReferenceCounted(False)
            except Exception:
                pass
            wl.acquire()
            self.__dict__["_wake_lock"] = wl
        except Exception:
            pass

    def _release_wake_lock(self):
        try:
            wl = getattr(self, "_wake_lock", None)
            if wl is not None:
                if wl.isHeld():
                    wl.release()
                self.__dict__["_wake_lock"] = None
        except Exception:
            pass

    def _post_delayed(self, fn, ms):
        try:
            from java import dynamic_proxy
            from java.lang import Runnable
            from android.os import Handler, Looper

            class _Runnable(dynamic_proxy(Runnable)):
                def run(self_d):
                    try:
                        self_d._fn()
                    except Exception:
                        pass

            runner = _Runnable()
            runner._fn = fn
            Handler(Looper.getMainLooper()).postDelayed(runner, ms)
        except Exception:
            pass

    # ----------------------------------------------------------
    # settings
    # ----------------------------------------------------------

    def create_settings(self):
        try:
            items = self._inner_create_settings()
        except Exception:
            items = []
        if hasattr(self, '_author_helper'):
            return self._author_helper.prepend_settings(items)
        return items

    def _inner_create_settings(self):
        try:
            from ui.settings import Header, Text, Divider, Switch
        except Exception:
            return []
        return [
            Header(text="Sleep mode"),
            Switch(
                key=WAKE_KEY,
                text="Block sleep while downloading",
                default=False,
                subtext="Keep the device awake while files are downloading",
            ),
        ]

# __DEX_BEGIN__
# PLACEHOLDER
# __DEX_END__