import asyncio
import os
import platform
import shutil
import tempfile

from playwright.async_api import async_playwright


def copy_chrome_cookies_to_temp():

    """
    Copies Chrome cookies into temp profile
    so your real Chrome stays untouched.
    """

    sys = platform.system().lower()

    if "windows" in sys:

        src = os.path.expandvars(
            r"%LOCALAPPDATA%\Google\Chrome\User Data"
        )

    elif "darwin" in sys:

        src = os.path.expanduser(
            "~/Library/Application Support/Google/Chrome"
        )

    else:

        src = os.path.expanduser(
            "~/.config/google-chrome"
        )

    # =====================================
    # TEMP PROFILE
    # =====================================
    tmp_dir = tempfile.mkdtemp(
        prefix="chrome_ss_"
    )

    tmp_default = os.path.join(
        tmp_dir,
        "Default"
    )

    os.makedirs(
        tmp_default,
        exist_ok=True
    )

    # =====================================
    # COPY COOKIE FILES
    # =====================================
    cookie_files = [
        "Cookies",
        "Cookies-journal"
    ]

    src_default = os.path.join(
        src,
        "Default"
    )

    copied = []

    for f in cookie_files:

        src_file = os.path.join(
            src_default,
            f
        )

        dst_file = os.path.join(
            tmp_default,
            f
        )

        if os.path.exists(src_file):

            shutil.copy2(
                src_file,
                dst_file
            )

            copied.append(f)

    print(f"\nCopied cookie files: {copied}")

    print(f"Temp profile: {tmp_dir}")

    return tmp_dir


async def scrape_sender_domains(url):

    all_domains = []

    seen = set()

    print(
        "\nCloning Chrome cookies "
        "into temp profile..."
    )

    tmp_profile = copy_chrome_cookies_to_temp()

    async with async_playwright() as p:

        print(
            "\nLaunching browser "
            "with session cookies..."
        )

        browser = await p.chromium.launch_persistent_context(
            user_data_dir=tmp_profile,
            channel="chrome",
            headless=False,
            args=[
                "--start-maximized",
                "--no-first-run",
                "--no-default-browser-check",
            ],
        )

        page = (
            browser.pages[0]
            if browser.pages
            else await browser.new_page()
        )

        # =====================================
        # OPEN PAGE
        # =====================================
        print(f"\nOpening: {url}")

        await page.goto(
            url,
            wait_until="networkidle",
            timeout=120000
        )

        await page.wait_for_timeout(5000)

        # =====================================
        # SCROLL PAGE
        # =====================================
        print(
            "\nScrolling page "
            "to load sections..."
        )

        for i in range(1, 21):

            await page.evaluate(
                f"""
                window.scrollTo(
                    0,
                    document.body.scrollHeight * {i/20}
                )
                """
            )

            await page.wait_for_timeout(300)

        await page.wait_for_timeout(3000)

        # =====================================
        # WAIT FOR SECTION
        # =====================================
        print(
            "\nWaiting for "
            "Sending Domains section..."
        )

        try:

            await page.wait_for_selector(
                "text=Sending Domains",
                timeout=30000
            )

            print(
                "Found Sending Domains section!"
            )

            el = page.locator(
                "text=Sending Domains"
            ).first

            await el.scroll_into_view_if_needed()

            await page.wait_for_timeout(3000)

        except Exception:

            print(
                "WARNING: Could not "
                "confirm section."
            )

        page_num = 1

        visited_pages = set()

        # =====================================
        # PAGINATION LOOP
        # =====================================
        while True:

            print(f"\n--- Page {page_num} ---")

            await page.wait_for_timeout(2000)

            page_domains = []

            # =====================================
            # METHOD 1
            # =====================================
            try:

                rows = page.locator(
                    "table tbody tr"
                )

                count = await rows.count()

                print(f"Rows found: {count}")

                for i in range(count):

                    try:

                        row = rows.nth(i)

                        link = row.locator(
                            "td a"
                        ).first

                        if await link.count() > 0:

                            text = (
                                await link.inner_text()
                            ).strip().lower()

                        else:

                            text = (
                                await row.locator(
                                    "td"
                                ).first.inner_text()
                            ).strip().lower()

                        if (
                            text
                            and "." in text
                            and " " not in text
                            and "/" not in text
                            and len(text) > 3
                        ):

                            page_domains.append(text)

                    except Exception:
                        pass

            except Exception:
                pass

            # =====================================
            # METHOD 2 FALLBACK
            # =====================================
            if not page_domains:

                try:

                    cells = await page.locator(
                        "td"
                    ).all_inner_texts()

                    for text in cells:

                        text = (
                            text.strip().lower()
                        )

                        if (
                            text
                            and "." in text
                            and " " not in text
                            and "/" not in text
                            and len(text) > 3
                        ):

                            page_domains.append(text)

                except Exception:
                    pass

            # =====================================
            # REMOVE DUPLICATES
            # =====================================
            page_domains = list(
                dict.fromkeys(page_domains)
            )

            # =====================================
            # STOP IF EMPTY
            # =====================================
            if not page_domains:

                print("\nNo domains found.")

                break

            # =====================================
            # STOP IF REPEATED PAGE
            # =====================================
            first_domain = page_domains[0]

            if first_domain in visited_pages:

                print(
                    "\nRepeated page detected."
                )

                print(
                    "Stopping pagination."
                )

                break

            visited_pages.add(first_domain)

            # =====================================
            # STORE UNIQUE DOMAINS
            # =====================================
            new_count = 0

            for d in page_domains:

                if d not in seen:

                    seen.add(d)

                    all_domains.append(d)

                    new_count += 1

                    print(d)

            print(
                f"\nNew: {new_count} | "
                f"Total so far: {len(all_domains)}"
            )

            # =====================================
            # NEXT BUTTON
            # =====================================
            next_clicked = False

            for sel in [

                "a.paginate_button.next",

                "li.paginate_button.next > a",

                "xpath=//a[normalize-space()='Next']",

                "xpath=//button[normalize-space()='Next']",
            ]:

                try:

                    btn = page.locator(
                        sel
                    ).first

                    if await btn.count() == 0:
                        continue

                    cls = (
                        await btn.get_attribute(
                            "class"
                        )
                        or ""
                    )

                    if "disabled" in cls.lower():

                        print(
                            "\nLast page reached."
                        )

                        next_clicked = False

                        break

                    print(
                        "\nOpening next page..."
                    )

                    await btn.scroll_into_view_if_needed()

                    await btn.click(
                        timeout=10000
                    )

                    await page.wait_for_timeout(4000)

                    next_clicked = True

                    page_num += 1

                    break

                except Exception:
                    continue

            if not next_clicked:

                print("\nNo more pages.")

                break

            # =====================================
            # SAFETY STOP
            # =====================================
            if page_num > 50:

                print(
                    "\nSafety stop triggered."
                )

                break

        # =====================================
        # CLOSE BROWSER
        # =====================================
        await browser.close()

    # =====================================
    # CLEAN TEMP PROFILE
    # =====================================
    shutil.rmtree(
        tmp_profile,
        ignore_errors=True
    )

    # =====================================
    # OUTPUT 1 - ALL DOMAINS
    # =====================================
    print("\n" + "=" * 60)

    print(
        f"TOTAL SENDING DOMAINS FOUND: "
        f"{len(all_domains)}"
    )

    print("=" * 60)

    for d in all_domains:
        print(d)

    # =====================================
    # OUTPUT 2 - ROOT DOMAINS ONLY
    # =====================================
    root_domains = []

    seen_roots = set()

    for domain in all_domains:

        try:

            domain = domain.lower().strip()

            parts = domain.split(".")

            # =================================
            # HANDLE co.uk etc
            # =================================
            special_suffixes = [
                "co.uk",
                "org.uk",
                "ac.uk",
                "gov.uk",
            ]

            root = None

            for suf in special_suffixes:

                if domain.endswith("." + suf):

                    remain = domain[:-(len(suf) + 1)]

                    remain_parts = remain.split(".")

                    if remain_parts:

                        root = (
                            remain_parts[-1]
                            + "."
                            + suf
                        )

                    break

            # =================================
            # NORMAL DOMAINS
            # =================================
            if not root and len(parts) >= 2:

                root = (
                    parts[-2]
                    + "."
                    + parts[-1]
                )

            if root and root not in seen_roots:

                seen_roots.add(root)

                root_domains.append(root)

        except:
            pass

    # =====================================
    # OUTPUT 2 DISPLAY
    # =====================================
    print("\n" + "=" * 60)

    print("ROOT DOMAINS ONLY")

    print("=" * 60)

    for d in root_domains:
        print(d)

    print("\n" + "=" * 60)

    print(
        f"TOTAL ROOT DOMAINS: "
        f"{len(root_domains)}"
    )

    print("=" * 60)


# =====================================
# MAIN
# =====================================
async def main():

    user_url = input(
        "Enter SenderScore URL: "
    ).strip()

    if not user_url:

        print("No URL entered.")

        return

    await scrape_sender_domains(
        user_url
    )


# =====================================
# START
# =====================================
asyncio.run(main())