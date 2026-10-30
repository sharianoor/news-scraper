import re
from urllib.parse import quote_plus, urlparse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


NEWS_SOURCE = "TechCrunch"
NEWS_DOMAIN = "techcrunch.com"


def create_driver():
    """
    Configure Chromium for headless execution inside Docker.
    """

    options = Options()
    options.binary_location = "/usr/bin/chromium"

    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    from selenium.webdriver.chrome.service import Service

    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(30)

    return driver


def get_article_url(driver, keyword):
    """
    Search TechCrunch and identify the first article link.
    """

    search_url = (
        "https://techcrunch.com/search/"
        + quote_plus(keyword)
        + "/"
    )

    driver.get(search_url)

    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located(
            (By.TAG_NAME, "body")
        )
    )

    links = driver.find_elements(
        By.CSS_SELECTOR,
        "a[href]"
    )

    for link in links:
        href = link.get_attribute("href")

        if not href:
            continue

        parsed = urlparse(href)

        if parsed.hostname not in {
            "techcrunch.com",
            "www.techcrunch.com"
        }:
            continue

        path = parsed.path.strip("/")

        if not path:
            continue

        excluded_paths = (
            "search/",
            "category/",
            "tag/",
            "author/",
            "page/",
            "wp-content/",
            "about",
            "events/",
            "videos/"
        )

        if any(
            path.lower().startswith(prefix)
            for prefix in excluded_paths
        ):
            continue

        if path.lower() in {
            "latest",
            "newsletter",
            "podcasts"
        }:
            continue

        # Avoid links that are unlikely to be articles.
        if len(path.split("/")) < 2:
            continue

        # Return the first plausible article URL.
        return href

    raise RuntimeError(
        "No TechCrunch article link was found. "
        "The search page may have changed or blocked access."
    )


def extract_article_text(driver, article_url):
    """
    Open the selected article and extract its main text.
    """

    driver.get(article_url)

    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located(
            (By.TAG_NAME, "body")
        )
    )

    # Prefer the article's main content.
    selectors = [
        "article",
        "main",
        "[itemprop='articleBody']"
    ]

    for selector in selectors:
        elements = driver.find_elements(
            By.CSS_SELECTOR,
            selector
        )

        for element in elements:
            paragraphs = element.find_elements(
                By.CSS_SELECTOR,
                "p"
            )

            text = " ".join(
                paragraph.text.strip()
                for paragraph in paragraphs
                if paragraph.text.strip()
            )

            if len(text.split()) >= 50:
                return text

    # Fallback: collect paragraphs from the page.
    paragraphs = driver.find_elements(
        By.CSS_SELECTOR,
        "p"
    )

    text = " ".join(
        paragraph.text.strip()
        for paragraph in paragraphs
        if paragraph.text.strip()
    )

    if len(text.split()) < 20:
        raise RuntimeError(
            "The article text could not be extracted."
        )

    return text


def scrape_news(keyword):
    """
    Search TechCrunch and return the first article's URL
    and extracted text.
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