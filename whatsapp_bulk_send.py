"""
WhatsApp Bulk Messenger
-----------------------
Automatically sends a WhatsApp message to every contact name in the list
by searching for them in WhatsApp Web — no phone numbers needed.

SETUP (one time):
    pip install selenium

HOW TO USE:
1. Fill in CONTACT_NAMES and MESSAGE below
2. Names must match exactly how they appear in your WhatsApp contacts
3. Run all cells — first time only, scan the QR code in the Chrome window
   (after that your login is saved, no QR on future runs)
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os

# ── EDIT THESE ──────────────────────────────────────────────────────────────

CHROME_PROFILE_PATH = os.path.join(os.path.expanduser("~"), "whatsapp_sender_profile")

# Names exactly as they appear in your WhatsApp contacts
CONTACT_NAMES = [
    "John Smith",
    # add all 27 names here, one per line, in quotes with a comma
]

MESSAGE = """Hello! Replace this with your actual message.

You can use multiple lines.
"""

# Seconds to wait for search results and chat to load
LOAD_WAIT = 15

# ── DO NOT EDIT BELOW THIS LINE ─────────────────────────────────────────────

def type_message(msg_box, message):
    # Send line by line — Shift+Enter for newlines, Enter to send at the end
    lines = message.strip().split('\n')
    for i, line in enumerate(lines):
        msg_box.send_keys(line)
        if i < len(lines) - 1:
            msg_box.send_keys(Keys.SHIFT, Keys.RETURN)


def send_to_contact(driver, name):
    # Open the search box
    search_btn = WebDriverWait(driver, LOAD_WAIT).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="chat-list-search"]'))
    )
    search_btn.click()

    # Type the contact name
    search_input = WebDriverWait(driver, LOAD_WAIT).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="search-input"]'))
    )
    search_input.clear()
    search_input.send_keys(name)
    time.sleep(2)  # Wait for results to appear

    # Click the first result
    first_result = WebDriverWait(driver, LOAD_WAIT).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="cell-frame-container"]'))
    )
    first_result.click()

    # Wait for the chat compose box to appear
    msg_box = WebDriverWait(driver, LOAD_WAIT).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="conversation-compose-box-input"]'))
    )
    time.sleep(1)

    # Type message and send
    type_message(msg_box, MESSAGE)
    time.sleep(1)
    msg_box.send_keys(Keys.RETURN)
    time.sleep(2)


def send_all():
    total = len(CONTACT_NAMES)
    if total == 0:
        print("ERROR: CONTACT_NAMES list is empty.")
        return

    print(f"WhatsApp Bulk Sender — {total} contacts")
    print("Opening Chrome...")

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

    for i, name in enumerate(CONTACT_NAMES, start=1):
        print(f"[{i}/{total}] Sending to '{name}' ...", end=" ")
        try:
            send_to_contact(driver, name)
            print("Sent!")
            sent += 1
        except Exception:
            print(f"FAILED — '{name}' not found or chat did not load.")
            failed.append(name)
            # Press Escape to close any open search/chat and reset state
            driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            time.sleep(1)

    driver.quit()
    print(f"\nDone — {sent}/{total} sent.")
    if failed:
        print(f"Failed contacts: {failed}")


send_all()
