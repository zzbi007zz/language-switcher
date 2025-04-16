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
            
            # Initialize WebDriver
            self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
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
            
            # Wait for login form to be visible
            logger.info("Waiting for login form")
            WebDriverWait(self.driver, 20).until(
                EC.visibility_of_element_located((By.ID, "username"))  # Adjust selector as needed
            )
            
            # Enter credentials
            logger.info("Entering credentials")
            self.driver.find_element(By.ID, "username").send_keys(self.username)  # Adjust selector as needed
            self.driver.find_element(By.ID, "password").send_keys(self.password)  # Adjust selector as needed
            
            # Click login button
            logger.info("Submitting login form")
            self.driver.find_element(By.XPATH, "//button[@type='submit']").click()  # Adjust selector as needed
            
            # Handle 2FA if present
            self.handle_2fa()
            
            # Verify successful login by checking for dashboard or home page element
            WebDriverWait(self.driver, 20).until(
                EC.visibility_of_element_located((By.XPATH, "//span[contains(text(), 'Dashboard')]"))  # Adjust selector as needed
            )
            
            logger.info("Login successful")
            return True
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            self.take_screenshot("login_failure")
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
     def find_element_safe(self, by, value, timeout=10):
        """
        Safely find an element with better error handling
        
        Args:
            by: The method to locate elements (e.g., By.ID)
            value: The value to search for
            timeout: Maximum time to wait for element
            
        Returns:
            WebElement or None
        """
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except (TimeoutException, NoSuchElementException):
            logger.warning(f"Element not found: {by}={value}")
            return None
        except Exception as e:
            logger.error(f"Error finding element {by}={value}: {str(e)}")
            return None
    
    def find_elements_safe(self, by, value, timeout=10):
        """
        Safely find elements with better error handling
        
        Args:
            by: The method to locate elements (e.g., By.ID)
            value: The value to search for
            timeout: Maximum time to wait for element
            
        Returns:
            List of WebElements or empty list
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return self.driver.find_elements(by, value)
        except (TimeoutException, NoSuchElementException):
            logger.warning(f"No elements found: {by}={value}")
            return []
        except Exception as e:
            logger.error(f"Error finding elements {by}={value}: {str(e)}")
            return []
    
    def extract_translation_key(self, element):
        """
        Attempt to extract translation key from element's attributes
        
        Args:
            element: WebElement to examine
            
        Returns:
            str or None: Translation key if found
        """
        try:
            # Check common attribute names that might contain translation keys
            for attr in ['data-translation-key', 'data-i18n', 'data-key', 'i18n-key']:
                key = element.get_attribute(attr)
                if key:
                    return key
            
            # Check for key in class (some frameworks add key as a class)
            classes = element.get_attribute('class')
            if classes:
                class_list = classes.split()
                for cls in class_list:
                    if cls.startswith('i18n-') or cls.startswith('trans-'):
                        return cls.split('-', 1)[1]
            
            # Check for key pattern in element ID
            element_id = element.get_attribute('id')
            if element_id and ('.' in element_id or '_' in element_id):
                if element_id.startswith('trans.') or element_id.startswith('i18n.'):
                    return element_id.split('.', 1)[1]
            
            return None
        except Exception as e:
            logger.error(f"Error extracting translation key: {str(e)}")
            return None
    
    def check_element_translations(self, element):
        """
        Check translations for a specific element in all languages
        
        Args:
            element: WebElement to check
            
        Returns:
            dict: Results for this element
        """
        results = {
            "element": self.get_element_xpath(element),
            "translations": [],
            "has_mismatch": False
        }
        
        # Try to get the translation key
        key = self.extract_translation_key(element)
        
        # Get initial English text
        try:
            en_text = element.text.strip()
            if not en_text:
                return None  # Skip empty elements
        except:
            return None  # Skip problematic elements
            
        # Record English result
        english_result = {
            "language": "English",
            "actual": en_text,
            "expected": None,
            "matched": False
        }
        
        # Look for translation by key if available
        if key and key in self.translations_df['Key'].values:
            # Direct key lookup
            translation_row = self.translations_df[self.translations_df['Key'] == key].iloc[0]
            english_result["expected"] = translation_row['Original EN']
            english_result["matched"] = english_result["actual"].lower() == english_result["expected"].lower()
        else:
            # Text-based lookup
            matches = self.translations_df[self.translations_df['Original EN'].str.lower() == en_text.lower()]
            if not matches.empty:
                english_result["expected"] = matches.iloc[0]['Original EN']
                english_result["matched"] = True
                key = matches.iloc[0]['Key']  # Get key for other languages
        
        results["translations"].append(english_result)
        
        # Update statistics for English
        if english_result["matched"]:
            self.results["en_matched"] += 1
        else:
            self.results["en_mismatched"] += 1
            results["has_mismatch"] = True
        
        # If we have a key or English match, check other languages
        if key or english_result["matched"]:
            element_id = element.get_attribute('id') or ""
            element_class = element.get_attribute('class') or ""
            element_xpath = self.get_element_xpath(element)
            
            # For each other language
            for lang_code, lang_name in [('kh', 'Khmer'), ('cn', 'Chinese')]:
                # Change language
                self.change_language(lang_code)
                
                # Try to find the same element after language change
                try:
                    # Try to find element by ID first (most reliable)
                    if element_id:
                        lang_element = self.find_element_safe(By.ID, element_id)
                    # Then by exact XPath
                    elif element_xpath:
                        lang_element = self.find_element_safe(By.XPATH, element_xpath)
                    # Then by class if it's unique enough
                    elif element_class and len(element_class.split()) > 1:  # Multiple classes increase uniqueness
                        xpath = f"//*[@class='{element_class}']"
                        lang_element = self.find_element_safe(By.XPATH, xpath)
                    else:
                        # Fallback to position-based approach
                        lang_element = None
                
                    # If found, check translation
                    if lang_element:
                        lang_text = lang_element.text.strip()
                        
                        # Get expected translation
                        if key:
                            matches = self.translations_df[self.translations_df['Key'] == key]
                        else:
                            matches = self.translations_df[self.translations_df['Original EN'].str.lower() == en_text.lower()]
                            
                        if not matches.empty:
                            column = f"{lang_code.upper()} Confirm from BIC" if lang_code.upper() in ["KH", "CN"] else f"Original {lang_code.upper()}"
                            expected_text = matches.iloc[0][column]
                            is_matched = lang_text.lower() == expected_text.lower()
                            
                            lang_result = {
                                "language": lang_name,
                                "actual": lang_text,
                                "expected": expected_text,
                                "matched": is_matched
                            }
                            
                            results["translations"].append(lang_result)
                            
                            # Update statistics
                            if is_matched:
                                self.results[f"{lang_code}_matched"] += 1
                            else:
                                self.results[f"{lang_code}_mismatched"] += 1
                                results["has_mismatch"] = True
                                
                                # Take screenshot for mismatch
                                self.take_screenshot(f"mismatch_{lang_code}_{self.current_page.replace(' > ', '_')}_{element_id or 'unknown'}")
                except Exception as e:
                    logger.error(f"Error checking {lang_name} translation: {str(e)}")
            
            # Return to English for next element
            self.change_language('en')
        
        return results
    
    def scan_dynamic_content(self):
        """
        Scan for dynamic content that might not be in the initial page load
        """
        try:
            # Check for expandable sections
            expandable_elements = self.find_elements_safe(
                By.XPATH, 
                "//*[contains(@class, 'expandable') or contains(@class, 'collapse') or contains(@class, 'accordion')]"
            )
            
            for element in expandable_elements:
                try:
                    # Try to expand the element
                    self.driver.execute_script("arguments[0].click();", element)
                    time.sleep(1)  # Wait for expansion
                    
                    # Check newly visible elements
                    new_elements = self.get_page_elements()
                    logger.info(f"Found {len(new_elements)} elements after expanding section")
                    
                    # Check translations
                    for new_element in new_elements:
                        self.check_element_translations(new_element)
                    
                    # Collapse back
                    self.driver.execute_script("arguments[0].click();", element)
                    time.sleep(1)  # Wait for collapse
                except Exception as e:
                    logger.warning(f"Error handling expandable content: {str(e)}")
            
            # Check for tabs
            tab_elements = self.find_elements_safe(
                By.XPATH,
                "//ul[contains(@class, 'tabs') or contains(@class, 'nav-tabs')]/li"
            )
            
            for tab in tab_elements:
                try:
                    tab_name = tab.text.strip()
                    # Click on tab
                    self.driver.execute_script("arguments[0].click();", tab)
                    time.sleep(1)  # Wait for tab content to load
                    
                    logger.info(f"Checking tab: {tab_name}")
                    
                    # Check elements in tab content
                    tab_content_elements = self.get_page_elements()
                    for element in tab_content_elements:
                        self.check_element_translations(element)
                except Exception as e:
                    logger.warning(f"Error handling tab content: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error scanning dynamic content: {str(e)}")        
            
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
    
    def get_page_elements(self):
        """
        Get all translatable elements on the current page
        
        Returns:
            list: List of WebElement objects representing translatable text elements
        """
        # Define XPath expressions for common translatable elements
        translatable_elements_xpaths = [
            "//h1", "//h2", "//h3", "//h4", "//h5", "//h6",
            "//label", "//button", "//a[text()]", 
            "//span[not(child::*)]", "//p[not(child::*)]",
            "//th", "//td[not(child::*)]",
            "//div[not(child::*) and text()]"
        ]
        
        elements = []
        for xpath in translatable_elements_xpaths:
            try:
                elements.extend(self.driver.find_elements(By.XPATH, xpath))
            except Exception as e:
                logger.warning(f"Error retrieving elements with XPath {xpath}: {str(e)}")
        
        # Filter out elements with no text or with only whitespace
        elements = [e for e in elements if e.text.strip()]
        
        logger.info(f"Found {len(elements)} translatable elements on page {self.current_page}")
        return elements
    
    def check_translation(self, element_text, language):
        """
        Check if an element's text matches its translation in the Excel file
        
        Args:
            element_text (str): The text to check
            language (str): The language code ('en', 'kh', 'cn')
        
        Returns:
            tuple: (is_matched, expected_text)
        """
        # Map language codes to Excel column names
        column_map = {
            'en': 'Original EN',
            'kh': 'KH Confirm from BIC',
            'cn': 'CN Confirm from BIC'
        }
        
        # Clean the element text
        clean_text = element_text.strip()
        
        # Look for an exact match in the "Original EN" column (case-insensitive)
        if language == 'en':
            matches = self.translations_df[self.translations_df['Original EN'].str.lower() == clean_text.lower()]
        else:
            # For other languages, first find the English version to get the key
            en_matches = self.translations_df[self.translations_df['Original EN'].str.lower() == clean_text.lower()]
            if not en_matches.empty:
                # If we find a match in English, use its key to look up the correct translation
                keys = en_matches['Key'].tolist()
                matches = self.translations_df[self.translations_df['Key'].isin(keys)]
            else:
                # If no match in English, try direct match in the target language
                matches = self.translations_df[self.translations_df[column_map[language]].str.lower() == clean_text.lower()]
        
        if matches.empty:
            # No match found in translations
            logger.warning(f"No translation entry found for '{clean_text}' in {language}")
            return False, None
        
        # Get the expected translation
        expected_text = matches.iloc[0][column_map[language]]
        
        # Compare the texts (case-insensitive)
        is_matched = clean_text.lower() == expected_text.lower()
        
        if is_matched:
            logger.debug(f"Translation match for '{clean_text}' in {language}")
        else:
            logger.warning(f"Translation mismatch for '{clean_text}' in {language}. Expected: '{expected_text}'")
        
        return is_matched, expected_text
    
    def check_page_translations(self):
        """Check translations for all elements on the current page in all languages"""
        page_results = {
            "page": self.current_page,
            "elements_checked": 0,
            "mismatches": []
        }
        
        # Check English (default language) first
        self.change_language('en')
        elements = self.get_page_elements()
        
        # Store English elements for reference
        english_elements = {}
        for i, element in enumerate(elements):
            try:
                element_text = element.text.strip()
                if not element_text:
                    continue
                
                english_elements[f"element_{i}"] = {
                    "element": element,
                    "text": element_text,
                    "xpath": self.get_element_xpath(element)
                }
                
                # Check English text against Excel
                is_matched, expected_text = self.check_translation(element_text, 'en')
                
                page_results["elements_checked"] += 1
                self.results["total_elements"] += 1
                
                if is_matched:
                    self.results["en_matched"] += 1
                else:
                    self.results["en_mismatched"] += 1
                    mismatch = {
                        "page": self.current_page,
                        "element": self.get_element_xpath(element),
                        "language": "English",
                        "actual": element_text,
                        "expected": expected_text or "Not found in translations"
                    }
                    page_results["mismatches"].append(mismatch)
                    self.results["mismatches"].append(mismatch)
            
            except (StaleElementReferenceException, NoSuchElementException) as e:
                logger.warning(f"Element became stale or not found: {str(e)}")
                continue
            except Exception as e:
                logger.error(f"Error checking English element: {str(e)}")
                continue
        
        # Check other languages
        for lang_code, lang_name in [('kh', 'Khmer'), ('cn', 'Chinese')]:
            try:
                # Change language
                self.change_language(lang_code)
                
                # Get new elements after language change
                new_elements = self.get_page_elements()
                
                # Check if number of elements matches English
                if len(new_elements) != len(elements):
                    logger.warning(f"Number of elements in {lang_name} ({len(new_elements)}) differs from English ({len(elements)})")
                
                # For each position, compare with the corresponding English element
                for i, english_key in enumerate(english_elements):
                    if i < len(new_elements):
                        try:
                            element = new_elements[i]
                            element_text = element.text.strip()
                            if not element_text:
                                continue
                            
                            en_text = english_elements[english_key]["text"]
                            
                            # Find the right translation based on the English text
                            en_matches = self.translations_df[self.translations_df['Original EN'].str.lower() == en_text.lower()]
                            
                            if not en_matches.empty:
                                key = en_matches.iloc[0]['Key']
                                expected_translation = self.translations_df[self.translations_df['Key'] == key].iloc[0][f"{lang_code.upper()} Confirm from BIC" if lang_code.upper() in ["KH", "CN"] else f"Original {lang_code.upper()}"]
                                
                                # Compare the texts
                                is_matched = element_text.lower() == expected_translation.lower()
                                
                                if is_matched:
                                    self.results[f"{lang_code}_matched"] += 1
                                else:
                                    self.results[f"{lang_code}_mismatched"] += 1
                                    mismatch = {
                                        "page": self.current_page,
                                        "element": self.get_element_xpath(element),
                                        "language": lang_name,
                                        "actual": element_text,
                                        "expected": expected_translation,
                                        "english_reference": en_text
                                    }
                                    page_results["mismatches"].append(mismatch)
                                    self.results["mismatches"].append(mismatch)
                                    
                                    # Take screenshot of the mismatch
                                    self.take_screenshot(f"mismatch_{lang_code}_{self.current_page.replace(' > ', '_')}_{i}")
                            else:
                                logger.warning(f"No English reference found for position {i} in {lang_name}")
                        
                        except (StaleElementReferenceException, NoSuchElementException) as e:
                            logger.warning(f"Element became stale or not found in {lang_name}: {str(e)}")
                            continue
                        except Exception as e:
                            logger.error(f"Error checking {lang_name} element: {str(e)}")
                            continue
            except Exception as e:
                logger.error(f"Error processing {lang_name} language: {str(e)}")
                self.take_screenshot(f"language_processing_error_{lang_code}")
        
        return page_results
    
    def get_element_xpath(self, element):
        """
        Generate a unique XPath for a WebElement
        
        Args:
            element (WebElement): The element to get XPath for
        
        Returns:
            str: XPath string for the element
        """
        try:
            return self.driver.execute_script("""
                function getPathTo(element) {
                    if (element.id !== '')
                        return '//*[@id="' + element.id + '"]';
                    if (element === document.body)
                        return '/html/body';

                    var index = 1;
                    var siblings = element.parentNode.childNodes;
                    for (var i = 0; i < siblings.length; i++) {
                        var sibling = siblings[i];
                        if (sibling === element)
                            return getPathTo(element.parentNode) + '/' + element.tagName.toLowerCase() + '[' + index + ']';
                        if (sibling.nodeType === 1 && sibling.tagName === element.tagName)
                            index++;
                    }
                }
                return getPathTo(arguments[0]);
            """, element)
        except Exception:
            # Fallback to simpler method
            tag_name = element.tag_name
            text = element.text.strip()
            if text:
                return f"//{tag_name}[contains(text(), '{text[:20]}')]"
            else:
                return f"//{tag_name}"
    
    def take_screenshot(self, name):
        """
        Take a screenshot and save it
        
        Args:
            name (str): Base name for the screenshot file
        """
        try:
            filename = f"{screenshots_dir}/{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            self.driver.save_screenshot(filename)
            logger.info(f"Screenshot saved: {filename}")
        except Exception as e:
            logger.error(f"Failed to take screenshot: {str(e)}")
    
    def generate_report(self):
        """Generate a detailed HTML report of the translation test results"""
        try:
            report_file = f"{report_dir}/translation_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            
            # Calculate statistics
            total_checks = self.results["total_elements"] * 3  # 3 languages
            total_matches = self.results["en_matched"] + self.results["kh_matched"] + self.results["cn_matched"]
            total_mismatches = self.results["en_mismatched"] + self.results["kh_mismatched"] + self.results["cn_mismatched"]
            
            match_percentage = (total_matches / total_checks) * 100 if total_checks > 0 else 0
            
            # Create HTML report
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Translation Test Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    h1, h2, h3 {{ color: #333; }}
                    table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                    tr:nth-child(even) {{ background-color: #f9f9f9; }}
                    .summary {{ background-color: #e6f7ff; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                    .success {{ color: green; }}
                    .error {{ color: red; }}
                    .warning {{ color: orange; }}
                </style>
            </head>
            <body>
                <h1>Translation Test Report</h1>
                <div class="summary">
                    <h2>Summary</h2>
                    <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p><strong>Total Elements Checked:</strong> {self.results["total_elements"]}</p>
                    <p><strong>Overall Match Rate:</strong> <span class="{'success' if match_percentage >= 90 else 'warning' if match_percentage >= 70 else 'error'}">{match_percentage:.2f}%</span></p>
                    <p><strong>English Matches:</strong> {self.results["en_matched"]} / {self.results["en_matched"] + self.results["en_mismatched"]} ({(self.results["en_matched"] / (self.results["en_matched"] + self.results["en_mismatched"]) * 100):.2f}% match rate)</p>
                    <p><strong>Khmer Matches:</strong> {self.results["kh_matched"]} / {self.results["kh_matched"] + self.results["kh_mismatched"]} ({(self.results["kh_matched"] / (self.results["kh_matched"] + self.results["kh_mismatched"]) * 100):.2f}% match rate)</p>
                    <p><strong>Chinese Matches:</strong> {self.results["cn_matched"]} / {self.results["cn_matched"] + self.results["cn_mismatched"]} ({(self.results["cn_matched"] / (self.results["cn_matched"] + self.results["cn_mismatched"]) * 100):.2f}% match rate)</p>
                </div>
                
                <h2>Mismatches</h2>
                <table>
                    <tr>
                        <th>Page</th>
                        <th>Element</th>
                        <th>Language</th>
                        <th>Actual Text</th>
                        <th>Expected Text</th>
                        <th>Screenshot</th>
                    </tr>
            """
            
            # Add mismatches to the report
            for mismatch in self.results["mismatches"]:
                screenshot_name = f"mismatch_{mismatch['language'].lower()}_{mismatch['page'].replace(' > ', '_')}"
                screenshots = [file for file in os.listdir(screenshots_dir) if file.startswith(screenshot_name)]
                screenshot_link = f"../screenshots/{screenshots[0]}" if screenshots else ""
                
                html_content += f"""
                    <tr>
                        <td>{mismatch['page']}</td>
                        <td>{mismatch['element']}</td>
                        <td>{mismatch['language']}</td>
                        <td>{mismatch['actual']}</td>
                        <td>{mismatch['expected']}</td>
                        <td>{'<a href="' + screenshot_link + '" target="_blank">View Screenshot</a>' if screenshot_link else 'N/A'}</td>
                    </tr>
                """
            
            html_content += """
                </table>
                
                <h2>Test Configuration</h2>
                <table>
                    <tr>
                        <th>Parameter</th>
                        <th>Value</th>
                    </tr>
                    <tr>
                        <td>Base URL</td>
                        <td>{self.base_url}</td>
                    </tr>
                    <tr>
                        <td>Excel File</td>
                        <td>{self.excel_path}</td>
                    </tr>
                    <tr>
                        <td>Browser</td>
                        <td>{self.driver.capabilities['browserName']} {self.driver.capabilities['browserVersion']}</td>
                    </tr>
                    <tr>
                        <td>Platform</td>
                        <td>{self.driver.capabilities['platformName']}</td>
                    </tr>
                </table>
                
                <p>Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </body>
            </html>
            """.format(self=self)
            
            # Write the HTML report
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"Report generated: {report_file}")
            return report_file
        except Exception as e:
            logger.error(f"Failed to generate report: {str(e)}")
            return None
    
    def run_test(self):
        """Run the complete translation test process"""
        try:
            if not self.setup():
                logger.error("Setup failed, aborting test")
                return False
            
            if not self.login():
                logger.error("Login failed, aborting test")
                return False
            
            # Define the navigation paths to test
            navigation_paths = [
                ["Dashboard"],
                ["Account"],
                ["Account", "Account List"],
                ["Pay & Transfer"],
                ["Pay & Transfer", "Domestic Transfer"],
                ["Pay & Transfer", "Bill Payment"],
                ["Pay & Transfer", "Payroll"],
                ["Requests"]
                # Add more paths as needed
            ]
            
            # Test each page
            for path in navigation_paths:
                try:
                    if self.navigate_to_page(path):
                        self.check_page_translations()
                except Exception as e:
                    logger.error(f"Error testing page {' > '.join(path)}: {str(e)}")
                    self.take_screenshot(f"error_{' > '.join(path).replace(' ', '_')}")
            
            # Generate report
            report_file = self.generate_report()
            
            logger.info("Test completed")
            
            # Return to English UI before closing
            self.change_language('en')
            
            return True
        except Exception as e:
            logger.error(f"Test execution failed: {str(e)}")
            return False
        finally:
            if self.driver:
                self.driver.quit()

# Example usage
if __name__ == "__main__":
    # Configuration parameters
    BASE_URL = "https://corp-banking.sit.bic.tech"  # Replace with the actual URL
    EXCEL_PATH = "CDB-Translate.xlsx"
    USERNAME = "sole"  # Replace with actual credentials
    PASSWORD = "Password@123"  # Replace with actual credentials
    
    # Create and run the tester
    tester = TranslationTester(BASE_URL, EXCEL_PATH, USERNAME, PASSWORD)
    tester.run_test()
