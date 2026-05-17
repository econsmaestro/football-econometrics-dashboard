"""
WhatsApp Bulk Messenger
-----------------------
Automatically sends a WhatsApp message to every number in the list
using Selenium to control Chrome — no manual clicking needed.

SETUP (one time):
    pip install selenium

HOW TO USE:
1. Close Chrome completely first (important!)
2. Find your Chrome profile path and paste it into CHROME_PROFILE_PATH below
3. Fill in PHONE_NUMBERS and MESSAGE
4. Run all cells, then call send_all()
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import urllib.parse
import time

# ── EDIT THESE ──────────────────────────────────────────────────────────────

# A dedicated profile folder just for this script.
# It is created automatically on first run — you do NOT need to change this.
# First run: WhatsApp Web will ask you to scan a QR code once.
# Every run after that: it remembers your login, no QR needed.
import os
CHROME_PROFILE_PATH = os.path.join(os.path.expanduser("~"), "whatsapp_sender_profile")

# Singapore numbers — 8 digits, no country code
# +65 is added automatically
PHONE_NUMBERS = [
    "88595363",
    # add all 27 numbers here, one per line, in quotes with a comma
]

MESSAGE = """Hello! Replace this with your actual message.

You can use multiple lines.
"""

# Seconds to wait for WhatsApp Web to load each chat (increase if your
# internet is slow — 15 is safe, 10 is usually fine)
LOAD_WAIT = 15

# ── DO NOT EDIT BELOW THIS LINE ─────────────────────────────────────────────

COUNTRY_CODE = "65"


def build_url(phone):
    full_number = COUNTRY_CODE + phone.strip()
    encoded = urllib.parse.quote(MESSAGE)
    return f"https://web.whatsapp.com/send?phone={full_number}&text={encoded}"


def send_all():
    total = len(PHONE_NUMBERS)
    if total == 0:
        print("ERROR: PHONE_NUMBERS list is empty.")
        return

    print(f"WhatsApp Bulk Sender — {total} contacts")
    print("Opening a separate Chrome window for this script...")

    options = Options()
    options.add_argument(f"--user-data-dir={CHROME_PROFILE_PATH}")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")

    driver = webdriver.Chrome(options=options)
    driver.get("https://web.whatsapp.com")
    print()
    print("*** FIRST TIME ONLY: scan the QR code in the Chrome window that just opened ***")
    print("*** After that your login is saved — no QR needed on future runs             ***")
    print()
    input("Press Enter once you can see your WhatsApp chats in that window...")

    sent = 0
    failed = []

    for i, number in enumerate(PHONE_NUMBERS, start=1):
        url = build_url(number)
        print(f"[{i}/{total}] Sending to +{COUNTRY_CODE}{number.strip()} ...", end=" ")
        driver.get(url)

        try:
            # Wait for the message input box to appear with the pre-filled text
            msg_box = WebDriverWait(driver, LOAD_WAIT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="conversation-compose-box-input"]'))
            )
            time.sleep(2)  # Let the message finish loading into the box
            msg_box.send_keys(Keys.ENTER)  # Enter sends the message
            time.sleep(2)  # Wait for the message to actually send
            print("Sent!")
            sent += 1
        except Exception:
            print("FAILED — chat did not load in time. Check the number.")
            failed.append(number)

    driver.quit()
    print(f"\nDone — {sent}/{total} sent.")
    if failed:
        print(f"Failed numbers: {failed}")


# In Jupyter, this line actually runs it:
# send_all()
