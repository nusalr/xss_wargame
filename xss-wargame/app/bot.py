from threading import Lock
from urllib.parse import quote, urlsplit


class BotVisitError(RuntimeError):
    """Base error for an administrator visit failure."""


class BotBusyError(BotVisitError):
    pass


class BotTimeoutError(BotVisitError):
    pass


class AdminBot:
    def __init__(self, base_url, flag, navigation_timeout_ms=4_000, script_wait_ms=1_500):
        self.base_url = self._normalize_base_url(base_url)
        self.flag = flag
        self.navigation_timeout_ms = navigation_timeout_ms
        self.script_wait_ms = script_wait_ms
        self._visit_lock = Lock()

    @staticmethod
    def _normalize_base_url(value):
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("INTERNAL_BASE_URL must be an HTTP(S) origin")
        if parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
            raise ValueError("INTERNAL_BASE_URL must not contain a path, query, or fragment")
        return value.rstrip("/")

    def build_target_url(self, param):
        # The submitted value is data inside the fixed endpoint, never a destination URL.
        return f"{self.base_url}/vuln?param={quote(param, safe='')}"

    def visit(self, param):
        if not self._visit_lock.acquire(blocking=False):
            raise BotBusyError("another administrator visit is in progress")

        try:
            self._visit_with_browser(self.build_target_url(param))
        finally:
            self._visit_lock.release()

    def _visit_with_browser(self, target_url):
        try:
            from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise BotVisitError("Playwright is not installed") from exc

        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(
                    headless=True,
                    # The Docker image uses the default container user; Chromium's
                    # sandbox cannot initialize reliably in that user namespace.
                    args=["--disable-dev-shm-usage", "--no-sandbox", "--disable-setuid-sandbox"],
                )
                context = None
                try:
                    context = browser.new_context()
                    page = context.new_page()
                    page.goto(
                        f"{self.base_url}/",
                        wait_until="domcontentloaded",
                        timeout=self.navigation_timeout_ms,
                    )
                    context.add_cookies(
                        [
                            {
                                "name": "flag",
                                "value": self.flag,
                                "url": f"{self.base_url}/",
                                "httpOnly": False,
                                "secure": self.base_url.startswith("https://"),
                                "sameSite": "Lax",
                            }
                        ]
                    )
                    page.goto(
                        target_url,
                        wait_until="domcontentloaded",
                        timeout=self.navigation_timeout_ms,
                    )
                    page.wait_for_timeout(self.script_wait_ms)
                finally:
                    if context is not None:
                        context.close()
                    browser.close()
        except PlaywrightTimeoutError as exc:
            raise BotTimeoutError("administrator navigation timed out") from exc
        except BotVisitError:
            raise
        except Exception as exc:
            raise BotVisitError("administrator visit failed") from exc
