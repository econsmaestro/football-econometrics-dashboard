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
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import urllib.parse
import time

# ── EDIT THESE ──────────────────────────────────────────────────────────────

# Your Chrome user data folder — this lets Selenium use your existing
# WhatsApp Web login so no QR scan is needed.
#
# Windows:  r"C:\Users\YOUR_NAME\AppData\Local\Google\Chrome\User Data"
# Mac:      "/Users/YOUR_NAME/Library/Application Support/Google/Chrome"
# Linux:    "/home/YOUR_NAME/.config/google-chrome"
#
# Replace YOUR_NAME with your actual Windows/Mac username
CHROME_PROFILE_PATH = r"C:\Users\YOUR_NAME\AppData\Local\Google\Chrome\User Data"

# Singapore numbers — 8 digits, no country code
# +65 is added automatically
PHONE_NUMBERS = [
    "91234567",
    "81234567",
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
    print("Starting Chrome with your existing profile...")

    options = Options()
    options.add_argument(f"--user-data-dir={CHROME_PROFILE_PATH}")
    options.add_argument("--profile-directory=Default")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")

    driver = webdriver.Chrome(options=options)
    # Open WhatsApp Web first so it's ready
    driver.get("https://web.whatsapp.com")
    print("Waiting for WhatsApp Web to load (15s)...")
    time.sleep(15)

    sent = 0
    failed = []

    for i, number in enumerate(PHONE_NUMBERS, start=1):
        url = build_url(number)
        print(f"[{i}/{total}] Sending to +{COUNTRY_CODE}{number.strip()} ...", end=" ")
        driver.get(url)

        try:
            send_btn = WebDriverWait(driver, LOAD_WAIT).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="send"]'))
            )
            time.sleep(2)  # Let message fully appear in the text box
            send_btn.click()
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
