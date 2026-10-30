from urllib.parse import quote_plus, urlparse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


NEWS_SOURCE = "TechCrunch"
NEWS_DOMAIN = "techcrunch.com"


def create_driver():
    """Configure headless Chromium for execution inside Docker."""

    options = Options()
    options.binary_location = "/usr/bin/chromium"
    options.page_load_strategy = "eager"

    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-background-networking")

    service = Service("/usr/bin/chromedriver")

    driver = webdriver.Chrome(
        service=service,
        options=options
    )

    driver.set_page_load_timeout(45)
    driver.set_script_timeout(20)

    return driver


def open_page(driver, url):
    """
    Open a page without getting stuck on slow-loading resources.

    If navigation times out, stop loading and continue only if
    the browser has successfully reached a usable document.
    """

    try:
        driver.get(url)

    except TimeoutException:
        print(f"Page loading timed out: {url}")

        try:
            driver.execute_script("window.stop();")

            WebDriverWait(driver, 10).until(
                lambda d: d.execute_script(
                    "return document.readyState"
                ) in ("interactive", "complete")
            )

        except Exception as error:
            raise RuntimeError(
                f"Unable to load a usable page: {url}"
            ) from error

    except Exception as error:
        raise RuntimeError(
            f"Browser failed to open: {url}"
        ) from error


def get_article_url(driver, keyword):
    """Search TechCrunch and select the first plausible article."""

    search_url = (
        "https://techcrunch.com/search/"
        + quote_plus(keyword)
        + "/"
    )

    open_page(driver, search_url)

    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located(
            (By.TAG_NAME, "body")
        )
    )

    links = driver.find_elements(
        By.CSS_SELECTOR,
        "a[href]"
    )

    excluded_prefixes = (
        "search/",
        "category/",
        "tag/",
        "author/",
        "page/",
        "wp-content/",
        "about",
        "events/",
        "videos/",
        "newsletter/",
        "podcasts/",
        "advertise/",
        "privacy/",
        "terms/"
    )

    for link in links:
        try:
            href = link.get_attribute("href")

            if not href:
                continue

            parsed = urlparse(href)

            if parsed.hostname not in {
                NEWS_DOMAIN,
                "www." + NEWS_DOMAIN
            }:
                continue

            path = parsed.path.strip("/")

            if not path:
                continue

            if any(
                path.lower().startswith(prefix)
                for prefix in excluded_prefixes
            ):
                continue

            # Skip links that look like category or navigation pages.
            if path.lower() in {
                "latest",
                "newsletter",
                "podcasts",
                "about"
            }:
                continue

            # Prefer article URLs with a date or a multi-part slug.
            path_parts = path.split("/")

            if len(path_parts) < 2:
                continue

            # Avoid returning links without a meaningful title.
            link_text = (link.text or "").strip()

            if not link_text:
                continue

            return href.split("#")[0]

        except Exception:
            continue

    raise RuntimeError(
        "No suitable TechCrunch article was found. "
        "The search page may have changed or blocked access."
    )


def extract_article_text(driver, article_url):
    """Extract the main text from a TechCrunch article."""

    open_page(driver, article_url)

    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located(
            (By.TAG_NAME, "body")
        )
    )

    # Prefer the article's main content over the entire page.
    selectors = [
        "[itemprop='articleBody']",
        "article",
        "main"
    ]

    for selector in selectors:
        elements = driver.find_elements(
            By.CSS_SELECTOR,
            selector
        )

        for element in elements:
            try:
                paragraphs = element.find_elements(
                    By.CSS_SELECTOR,
                    "p"
                )

                text_parts = []

                for paragraph in paragraphs:
                    paragraph_text = paragraph.text.strip()

                    if paragraph_text:
                        text_parts.append(paragraph_text)

                text = " ".join(text_parts)

                if len(text.split()) >= 50:
                    return text

            except Exception:
                continue

    # Fallback: collect visible paragraphs from the page.
    paragraphs = driver.find_elements(
        By.CSS_SELECTOR,
        "p"
    )

    text_parts = []

    for paragraph in paragraphs:
        try:
            paragraph_text = paragraph.text.strip()

            if paragraph_text:
                text_parts.append(paragraph_text)

        except Exception:
            continue

    text = " ".join(text_parts)

    if len(text.split()) < 20:
        raise RuntimeError(
            "Could not extract enough article text. "
            "TechCrunch may have blocked access or changed its page."
        )

    return text


def scrape_news(keyword):
    """
    Search TechCrunch and return the selected article's URL and text.
    """

    if not keyword or not keyword.strip():
        raise ValueError("A keyword is required.")

    driver = create_driver()

    try:
        article_url = get_article_url(
            driver,
            keyword.strip()
        )

        article_text = extract_article_text(
            driver,
            article_url
        )

        return {
            "newssource": NEWS_SOURCE,
            "url": article_url,
            "text": article_text
        }

    finally:
        driver.quit()