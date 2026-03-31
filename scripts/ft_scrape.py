#!/usr/bin/env python3
"""Scrape FlyerTalk thread pages using Playwright.

Usage:
    python3 scripts/ft_scrape.py URL [--pages N] [--out FILE]

Extracts post content (author, date, text) from FlyerTalk forum threads.
Supports multi-page threads by appending page numbers.
"""

import argparse
import json
import re
import sys
import time


def scrape_ft_page(page, url: str) -> list[dict]:
    """Scrape a single FlyerTalk page for posts."""
    page.goto(url, timeout=30000)
    time.sleep(2)

    # Close cookie banner if present
    try:
        cookie_btn = page.query_selector('button[id*="accept"], button[class*="accept"], .cookie-consent button')
        if cookie_btn:
            cookie_btn.click()
            time.sleep(0.5)
    except Exception:
        pass

    posts = []

    # FlyerTalk uses different structures depending on the forum version
    # Try the common post container selectors
    post_elements = page.query_selector_all('div.post, article.post, li.postbit, div[id^="post_message_"], div.postbody')

    if not post_elements:
        # Fallback: try to get all text content from the main content area
        post_elements = page.query_selector_all('table.post, div[id^="edit"], blockquote.postcontent')

    if not post_elements:
        # Last resort: grab the main content
        body_text = page.evaluate("() => document.body?.innerText || ''")
        # Split by common post separators
        chunks = re.split(r'(?=\b(?:Join Date|Originally Posted|Senior Member|FlyerTalk Evangelist)\b)', body_text)
        for i, chunk in enumerate(chunks[:50]):  # limit
            if len(chunk.strip()) > 50:
                posts.append({
                    "index": i,
                    "text": chunk.strip()[:3000]
                })
        return posts

    for i, el in enumerate(post_elements):
        try:
            text = el.evaluate("el => el.innerText || ''")
            if len(text.strip()) > 20:
                posts.append({
                    "index": i,
                    "text": text.strip()[:3000]
                })
        except Exception:
            pass

    return posts


def scrape_thread(url: str, max_pages: int = 1) -> list[dict]:
    """Scrape up to max_pages of a FlyerTalk thread."""
    from playwright.sync_api import sync_playwright

    all_posts = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1400, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()

        for pg in range(1, max_pages + 1):
            # FlyerTalk pagination: append -N to URL before .html
            if pg == 1:
                page_url = url
            else:
                # https://www.flyertalk.com/forum/oneworld/2008084-oneworld-explorer-user-guide.html
                # becomes: .../2008084-oneworld-explorer-user-guide-2.html
                page_url = re.sub(r'\.html$', f'-{pg}.html', url)

            print(f"Scraping page {pg}: {page_url}", file=sys.stderr)
            try:
                posts = scrape_ft_page(page, page_url)
                for post in posts:
                    post["page"] = pg
                    post["url"] = page_url
                all_posts.extend(posts)
                if pg < max_pages:
                    time.sleep(2)  # rate limit
            except Exception as e:
                print(f"Error on page {pg}: {e}", file=sys.stderr)
                break

        browser.close()

    return all_posts


def main():
    parser = argparse.ArgumentParser(description="Scrape FlyerTalk thread")
    parser.add_argument("url", help="FlyerTalk thread URL")
    parser.add_argument("--pages", type=int, default=3, help="Number of pages to scrape (default: 3)")
    parser.add_argument("--out", help="Output file (default: stdout)")
    args = parser.parse_args()

    posts = scrape_thread(args.url, max_pages=args.pages)

    output = json.dumps(posts, indent=2, ensure_ascii=False)

    if args.out:
        with open(args.out, "w") as f:
            f.write(output)
        print(f"Wrote {len(posts)} posts to {args.out}", file=sys.stderr)
    else:
        print(output)

    print(f"Total posts scraped: {len(posts)}", file=sys.stderr)


if __name__ == "__main__":
    main()
