import os
import time
import pandas as pd
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from openpyxl import load_workbook
import re

# Configure logging
log_dir = "logs"
screenshots_dir = "screenshots"
report_dir = "reports"

# Create directories if they don't exist
for directory in [log_dir, screenshots_dir, report_dir]:
    if not os.path.exists(directory):
        os.makedirs(directory)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"{log_dir}/translation_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger()

class TranslationTester:
    def __init__(self, base_url, excel_path, username, password):
        """
        Initialize the TranslationTester with configuration parameters
        
        Args:
            base_url (str): The URL of the web application
            excel_path (str): Path to the Excel file containing translations
            username (str): Username for authentication
            password (str): Password for authentication
        """
        self.base_url = base_url
        self.excel_path = excel_path
        self.username = username
        self.password = password
        self.driver = None
        self.translations_df = None
        self.results = {
            "total_elements": 0,
            "en_matched": 0,
            "kh_matched": 0,
            "cn_matched": 0,
            "en_mismatched": 0,
            "kh_mismatched": 0,
            "cn_mismatched": 0,
            "mismatches": []
        }
        self.current_page = ""
        
    def setup(self):
        """Set up the WebDriver and load translation data"""
        try:
            # Setup Chrome options
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-notifications")
            chrome_options.add_argument("--disable-gpu")  # Disable GPU hardware acceleration
            chrome_options.add_argument("--no-sandbox")  # Bypass OS security model
            chrome_options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems
            chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])  # Disable logging
            
            # Initialize WebDriver
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options
            )
            self.driver.implicitly_wait(10)
            
            # Load translation data
            self.load_translations()
            
            logger.info("Setup completed successfully")
            return True
        except Exception as e:
            logger.error(f"Setup failed: {str(e)}")
            return False
            
    def load_translations(self):
        """Load translation data from Excel file"""
        try:
            # Load the Excel file
            logger.info(f"Loading translations from {self.excel_path}")
            self.translations_df = pd.read_excel(self.excel_path)
            
            # Validate the expected columns exist
            required_columns = ["Key", "Original EN", "Original CN", "Original KH", "KH Confirm from BIC", "CN Confirm from BIC"]
            for column in required_columns:
                if column not in self.translations_df.columns:
                    raise ValueError(f"Required column '{column}' not found in Excel file")
            
            logger.info(f"Successfully loaded {len(self.translations_df)} translation entries")
        except Exception as e:
            logger.error(f"Failed to load translations: {str(e)}")
            raise
            
    def login(self):
        """Perform authentication to the web application"""
        try:
            logger.info(f"Navigating to {self.base_url}")
            self.driver.get(self.base_url)

            # Add a longer initial wait for the page to fully load
            time.sleep(5)

            # Wait for login form with more flexible locators
            logger.info("Waiting for login form")
            username_field = WebDriverWait(self.driver, 20).until(
                EC.any_of(
                    EC.presence_of_element_located((By.ID, "username")),
                    EC.presence_of_element_located((By.NAME, "username")),
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text']")),
                    EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Username' or contains(@class, 'username')]"))
                )
            )

            password_field = WebDriverWait(self.driver, 20).until(
                EC.any_of(
                    EC.presence_of_element_located((By.ID, "password")),
                    EC.presence_of_element_located((By.NAME, "password")),
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']")),
                    EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Password' or contains(@class, 'password')]"))
                )
            )

            # Enter credentials with explicit waits
            logger.info("Entering credentials")
            username_field.clear()
            username_field.send_keys(self.username)
            time.sleep(1)

            password_field.clear()
            password_field.send_keys(self.password)
            time.sleep(1)

            # Find and click login button with multiple possible locators
            logger.info("Submitting login form")
            login_button = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((
                    By.XPATH, "//button[@type='submit' or contains(text(), 'Login') or contains(text(), 'Sign in')]"
                ))
            )
            login_button.click()

            # Wait for successful login with multiple possible indicators
            logger.info("Waiting for successful login")
            WebDriverWait(self.driver, 30).until(
                EC.any_of(
                    EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'Dashboard')]")),
                    EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'dashboard')]")),
                    EC.url_contains("dashboard")
                )
            )

            logger.info("Login successful")
            return True

        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            self.take_screenshot("login_failure")
            # Print the current URL and page source for debugging
            logger.error(f"Current URL: {self.driver.current_url}")
            logger.error(f"Page source: {self.driver.page_source[:500]}...")  # First 500 chars
            return False

    def handle_2fa(self):
        """Handle two-factor authentication if present"""
        try:
            # Check if 2FA is present (wait briefly for 2FA elements)
            try:
                two_fa_element = WebDriverWait(self.driver, 5).until(
                    EC.visibility_of_element_located((By.XPATH, "//div[contains(text(), '2FA') or contains(text(), 'verification code')]"))  # Adjust selector as needed
                )

                logger.info("2FA detected, handling verification")

                # Here you would implement the logic to handle 2FA
                # For example, wait for user input:
                verification_code = input("Please enter the 2FA verification code: ")

                # Enter the verification code
                self.driver.find_element(By.ID, "verificationCode").send_keys(verification_code)  # Adjust selector as needed

                # Submit the verification code
                self.driver.find_element(By.XPATH, "//button[contains(text(), 'Verify')]").click()  # Adjust selector as needed

                logger.info("2FA verification submitted")
            except TimeoutException:
                logger.info("No 2FA detected, proceeding")
                pass

        except Exception as e:
            logger.error(f"Error handling 2FA: {str(e)}")
            self.take_screenshot("2fa_handling_failure")
            raise

    def change_language(self, language):
        """
        Change the application language

        Args:
            language (str): Language code ('en', 'kh', 'cn')
        """
        try:
            # Wait for language selector to be clickable
            language_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'language-selector') or contains(text(), 'English')]"))  # Adjust selector as needed
            )
            language_button.click()

            # Map language codes to expected text in the language dropdown
            language_map = {
                'en': 'English',
                'kh': 'ខ្មែរ',  # Khmer
                'cn': '中文'     # Chinese
            }

            # Select the specified language
            language_option = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, f"//li[contains(text(), '{language_map[language]}')]"))  # Adjust selector as needed
            )
            language_option.click()

            # Wait for page to reload/update after language change
            time.sleep(2)

            logger.info(f"Changed language to {language}")
            return True
        except Exception as e:
            logger.error(f"Failed to change language to {language}: {str(e)}")
            self.take_screenshot(f"language_change_failure_{language}")
            return False

    def navigate_to_page(self, menu_path):
        """
        Navigate to a specific page in the application

        Args:
            menu_path (list): List of menu items to click, in order
        """
        try:
            self.current_page = " > ".join(menu_path)
            logger.info(f"Navigating to {self.current_page}")

            for i, menu_item in enumerate(menu_path):
                # Adjust XPath for menu items based on level
                if i == 0:  # Main menu
                    menu_element = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, f"//span[contains(text(), '{menu_item}')]"))  # Adjust selector as needed
                    )
                else:  # Submenu
                    menu_element = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, f"//li[contains(text(), '{menu_item}')]"))  # Adjust selector as needed
                    )

                menu_element.click()
                time.sleep(1)  # Wait for submenu to appear or page to load

            # Wait for page content to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'content') or contains(@class, 'page')]"))  # Adjust selector as needed
            )

            logger.info(f"Successfully navigated to {self.current_page}")
            return True
        except Exception as e:
            logger.error(f"Failed to navigate to {self.current_page}: {str(e)}")
            self.take_screenshot(f"navigation_failure_{self.current_page.replace(' > ', '_')}")
            return
import os
import time
import pandas as pd
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from openpyxl import load_workbook
import re

# Configure logging
log_dir = "logs"
screenshots_dir = "screenshots"
report_dir = "reports"

# Create directories if they don't exist
for directory in [log_dir, screenshots_dir, report_dir]:
    if not os.path.exists(directory):
        os.makedirs(directory)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"{log_dir}/translation_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger()

class TranslationTester:
    def __init__(self, base_url, excel_path, username, password):
        """
        Initialize the TranslationTester with configuration parameters
        
        Args:
            base_url (str): The URL of the web application
            excel_path (str): Path to the Excel file containing translations
            username (str): Username for authentication
            password (str): Password for authentication
        """
        self.base_url = base_url
        self.excel_path = excel_path
        self.username = username
        self.password = password
        self.driver = None
        self.translations_df = None
        self.results = {
            "total_elements": 0,
            "en_matched": 0,
            "kh_matched": 0,
            "cn_matched": 0,
            "en_mismatched": 0,
            "kh_mismatched": 0,
            "cn_mismatched": 0,
            "mismatches": []
        }
        self.current_page = ""
        
    def setup(self):
        """Set up the WebDriver and load translation data"""
        try:
            # Setup Chrome options
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-notifications")
            chrome_options.add_argument("--disable-gpu")  # Disable GPU hardware acceleration
            chrome_options.add_argument("--no-sandbox")  # Bypass OS security model
            chrome_options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems
            chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])  # Disable logging
            
            # Initialize WebDriver
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options
            )
            self.driver.implicitly_wait(10)
            
            # Load translation data
            self.load_translations()
            
            logger.info("Setup completed successfully")
            return True
        except Exception as e:
            logger.error(f"Setup failed: {str(e)}")
            return False
            
    def load_translations(self):
        """Load translation data from Excel file"""
        try:
            # Load the Excel file
            logger.info(f"Loading translations from {self.excel_path}")
            self.translations_df = pd.read_excel(self.excel_path)
            
            # Validate the expected columns exist
            required_columns = ["Key", "Original EN", "Original CN", "Original KH", "KH Confirm from BIC", "CN Confirm from BIC"]
            for column in required_columns:
                if column not in self.translations_df.columns:
                    raise ValueError(f"Required column '{column}' not found in Excel file")
            
            logger.info(f"Successfully loaded {len(self.translations_df)} translation entries")
        except Exception as e:
            logger.error(f"Failed to load translations: {str(e)}")
            raise
            
    def login(self):
        """Perform authentication to the web application"""
        try:
            logger.info(f"Navigating to {self.base_url}")
            self.driver.get(self.base_url)
            
            # Add a longer initial wait for the page to fully load
            time.sleep(5)
            
            # Wait for login form with more flexible locators
            logger.info("Waiting for login form")
            username_field = WebDriverWait(self.driver, 20).until(
                EC.any_of(
                    EC.presence_of_element_located((By.ID, "username")),
                    EC.presence_of_element_located((By.NAME, "username")),
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text']")),
                    EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Username' or contains(@class, 'username')]"))
                )
            )

            password_field = WebDriverWait(self.driver, 20).until(
                EC.any_of(
                    EC.presence_of_element_located((By.ID, "password")),
                    EC.presence_of_element_located((By.NAME, "password")),
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']")),
                    EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Password' or contains(@class, 'password')]"))
                )
            )

            # Enter credentials with explicit waits
            logger.info("Entering credentials")
            username_field.clear()
            username_field.send_keys(self.username)
            time.sleep(1)

            password_field.clear()
            password_field.send_keys(self.password)
            time.sleep(1)

            # Find and click login button with multiple possible locators
            logger.info("Submitting login form")
            login_button = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((
                    By.XPATH, "//button[@type='submit' or contains(text(), 'Login') or contains(text(), 'Sign in')]"
                ))
            )
            login_button.click()

            # Wait for successful login with multiple possible indicators
            logger.info("Waiting for successful login")
            WebDriverWait(self.driver, 30).until(
                EC.any_of(
                    EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'Dashboard')]")),
                    EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'dashboard')]")),
                    EC.url_contains("dashboard")
                )
            )

            logger.info("Login successful")
            return True

        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            self.take_screenshot("login_failure")
            # Print the current URL and page source for debugging
            logger.error(f"Current URL: {self.driver.current_url}")
            logger.error(f"Page source: {self.driver.page_source[:500]}...")  # First 500 chars
            return False
            
    def handle_2fa(self):
        """Handle two-factor authentication if present"""
        try:
            # Check if 2FA is present (wait briefly for 2FA elements)
            try:
                two_fa_element = WebDriverWait(self.driver, 5).until(
                    EC.visibility_of_element_located((By.XPATH, "//div[contains(text(), '2FA') or contains(text(), 'verification code')]"))  # Adjust selector as needed
                )

                logger.info("2FA detected, handling verification")

                # Here you would implement the logic to handle 2FA
                # For example, wait for user input:
                verification_code = input("Please enter the 2FA verification code: ")

                # Enter the verification code
                self.driver.find_element(By.ID, "verificationCode").send_keys(verification_code)  # Adjust selector as needed

                # Submit the verification code
                self.driver.find_element(By.XPATH, "//button[contains(text(), 'Verify')]").click()  # Adjust selector as needed

                logger.info("2FA verification submitted")
            except TimeoutException:
                logger.info("No 2FA detected, proceeding")
                pass

        except Exception as e:
            logger.error(f"Error handling 2FA: {str(e)}")
            self.take_screenshot("2fa_handling_failure")
            raise

    def change_language(self, language):
        """
        Change the application language

        Args:
            language (str): Language code ('en', 'kh', 'cn')
        """
        try:
            # Wait for language selector to be clickable
            language_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'language-selector') or contains(text(), 'English')]"))  # Adjust selector as needed
            )
            language_button.click()

            # Map language codes to expected text in the language dropdown
            language_map = {
                'en': 'English',
                'kh': 'ខ្មែរ',  # Khmer
                'cn': '中文'     # Chinese
            }

            # Select the specified language
            language_option = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, f"//li[contains(text(), '{language_map[language]}')]"))  # Adjust selector as needed
            )
            language_option.click()

            # Wait for page to reload/update after language change
            time.sleep(2)

            logger.info(f"Changed language to {language}")
            return True
        except Exception as e:
            logger.error(f"Failed to change language to {language}: {str(e)}")
            self.take_screenshot(f"language_change_failure_{language}")
            return False

    def navigate_to_page(self, menu_path):
        """
        Navigate to a specific page in the application

        Args:
            menu_path (list): List of menu items to click, in order
        """
        try:
            self.current_page = " > ".join(menu_path)
            logger.info(f"Navigating to {self.current_page}")

            for i, menu_item in enumerate(menu_path):
                # Adjust XPath for menu items based on level
                if i == 0:  # Main menu
                    menu_element = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, f"//span[contains(text(), '{menu_item}')]"))  # Adjust selector as needed
                    )
                else:  # Submenu
                    menu_element = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, f"//li[contains(text(), '{menu_item}')]"))  # Adjust selector as needed
                    )

                menu_element.click()
                time.sleep(1)  # Wait for submenu to appear or page to load

            # Wait for page content to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'content') or contains(@class, 'page')]"))  # Adjust selector as needed
            )

            logger.info(f"Successfully navigated to {self.current_page}")
            return True
        except Exception as e:
            logger.error(f"Failed to navigate to {self.current_page}: {str(e)}")
            self.take_screenshot(f"navigation_failure_{self.current_page.replace(' > ', '_')}")
            return False
