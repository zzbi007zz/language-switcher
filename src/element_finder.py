class ElementFinder:
    def __init__(self, driver, wait_time=10):
        self.driver = driver
        self.wait_time = wait_time
        
    def find_by_translation_key(self, key):
        """Find elements by translation key attributes."""
        selectors = [
            f"//*[@data-i18n='{key}']",
            f"//*[@data-translation-key='{key}']",
            f"//*[contains(@class, 'i18n-{key}')]",
            f"//*[@id='i18n.{key}']"
        ]
        
        for selector in selectors:
            elements = self.driver.find_elements(By.XPATH, selector)
            if elements:
                return elements
        
        return []
    
    def find_page_elements(self):
        """Find all translatable elements on the current page."""
        # Improved selector list with better coverage
        selectors = [
            # Header elements
            "//h1[not(ancestor::*[contains(@style,'display: none')])]",
            "//h2[not(ancestor::*[contains(@style,'display: none')])]",
            "//h3[not(ancestor::*[contains(@style,'display: none')])]",
            "//h4[not(ancestor::*[contains(@style,'display: none')])]",
            
            # UI elements
            "//label[not(ancestor::*[contains(@style,'display: none')])]",
            "//button[not(ancestor::*[contains(@style,'display: none')]) and not(descendant::*)]",
            "//a[not(ancestor::*[contains(@style,'display: none')]) and not(descendant::*)]",
            
            # Content elements
            "//p[not(ancestor::*[contains(@style,'display: none')]) and not(descendant::*)]",
            "//span[not(ancestor::*[contains(@style,'display: none')]) and not(descendant::*)]",
            
            # Table elements
            "//th[not(ancestor::*[contains(@style,'display: none')])]",
            "//td[not(ancestor::*[contains(@style,'display: none')]) and not(descendant::*)]",
            
            # Menu elements
            "//li[not(ancestor::*[contains(@style,'display: none')]) and not(descendant::*)]",
            
            # Specific app elements
            "//*[contains(@class, 'label') and not(descendant::*)]",
            "//*[contains(@class, 'menu-item') and not(descendant::*)]"
        ]
        
        elements = []
        for selector in selectors:
            elements.extend(self.find_elements_safe(By.XPATH, selector))
            
        # Filter out empty or invisible elements
        return [e for e in elements if e.text.strip() and e.is_displayed()]
    
    # Add a retry decorator for flaky operations
def retry(max_attempts=3, delay=1, backoff=2, exceptions=(Exception,)):
    """
    Retry decorator with exponential backoff
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            current_delay = delay
            
            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    attempt += 1
                    if attempt == max_attempts:
                        logger.error(f"Function {func.__name__} failed after {max_attempts} attempts: {str(e)}")
                        raise
                    
                    logger.warning(f"Attempt {attempt} failed for {func.__name__}: {str(e)}. Retrying in {current_delay}s...")
                    time.sleep(current_delay)
                    current_delay *= backoff
                    
        return wrapper
    return decorator

# Apply to key functions
@retry(max_attempts=3, delay=1, exceptions=(StaleElementReferenceException, TimeoutException))
def find_element_safe(self, by, value, timeout=10):
    """Safely find an element with retries"""
    try:
        element = WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
        return element
    except (TimeoutException, NoSuchElementException) as e:
        logger.warning(f"Element not found: {by}={value}")
        raise e