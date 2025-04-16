import concurrent.futures
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager

def get_browser_driver(browser_name, headless=False):
    """
    Get WebDriver instance for specified browser
    
    Args:
        browser_name (str): Name of the browser (chrome, firefox, edge)
        headless (bool): Whether to run in headless mode
        
    Returns:
        WebDriver: Configured browser driver
    """
    browser_name = browser_name.lower()
    
    if browser_name == 'chrome':
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument('--headless')
        options.add_argument('--start-maximized')
        options.add_argument('--disable-notifications')
        options.add_argument('--disable-extensions')
        options.add_argument('--no-sandbox')
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        return webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    
    elif browser_name == 'firefox':
        options = webdriver.FirefoxOptions()
        if headless:
            options.add_argument('--headless')
        options.add_argument('--width=1920')
        options.add_argument('--height=1080')
        return webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()), options=options)
    
    elif browser_name == 'edge':
        options = webdriver.EdgeOptions()
        if headless:
            options.add_argument('--headless')
        options.add_argument('--start-maximized')
        options.add_argument('--disable-notifications')
        return webdriver.Edge(service=EdgeService(EdgeChromiumDriverManager().install()), options=options)
    
    else:
        raise ValueError(f"Unsupported browser: {browser_name}")

def run_test_on_browser(browser, config):
    """
    Run test on a specific browser
    
    Args:
        browser (str): Browser name
        config (dict): Test configuration
    
    Returns:
        dict: Test results for this browser
    """
    from src.tester import TranslationTester
    
    logger.info(f"Starting test on {browser}")
    
    try:
        # Setup driver for this browser
        driver = get_browser_driver(browser, config.get('headless', False))
        
        # Create and configure tester
        tester = TranslationTester(
            config.get('base_url', ''),
            config.get('excel_path', ''),
            config.get('username', ''),
            config.get('password', '')
        )
        
        # Use the provided driver
        tester.driver = driver
        
        # Configure additional options
        tester.headless = config.get('headless', False)
        tester.wait_time = config.get('wait_time', 10)
        tester.check_dynamic_content = config.get('check_dynamic_content', True)
        tester.screenshot_on_mismatch = config.get('screenshot_on_mismatch', True)
        
        # Run the test
        success = tester.run_test()
        
        # Get results
        results = {
            'browser': browser,
            'success': success,
            'results': tester.results,
            'report_file': tester.report_file if hasattr(tester, 'report_file') else None
        }
        
        logger.info(f"Test on {browser} completed with success={success}")
        return results
    
    except Exception as e:
        logger.error(f"Test on {browser} failed with error: {str(e)}")
        return {
            'browser': browser,
            'success': False,
            'error': str(e)
        }
    finally:
        if 'driver' in locals() and driver:
            driver.quit()

def run_parallel_tests(config, concurrency=None):
    """
    Run tests in parallel on multiple browsers
    
    Args:
        config (dict): Test configuration
        concurrency (int): Max number of concurrent tests (defaults to number of browsers)
    
    Returns:
        dict: Results for each browser
    """
    browsers = config.get('browsers', ['chrome'])
    
    if not browsers:
        logger.warning("No browsers specified for testing")
        return {}
    
    if not concurrency:
        concurrency = len(browsers)
    
    results = {}
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        future_to_browser = {
            executor.submit(run_test_on_browser, browser, config): browser
            for browser in browsers
        }
        
        for future in concurrent.futures.as_completed(future_to_browser):
            browser = future_to_browser[future]
            try:
                results[browser] = future.result()
            except Exception as e:
                logger.error(f"Test on {browser} generated an exception: {str(e)}")
                results[browser] = {
                    'browser': browser,
                    'success': False,
                    'error': str(e)
                }
    
        return results
    
def optimize_memory_usage(self):
    """
    Optimize memory usage during test run
    """
    try:
        # Clear browser cache periodically
        if hasattr(self.driver, "execute_cdp_cmd"):
            self.driver.execute_cdp_cmd('Network.clearBrowserCache', {})
        
        # Clear browser cookies
        self.driver.delete_all_cookies()
        
        # Reduce screenshot size in memory for large pages
        if self.results['total_elements'] > 500:
            self.driver.set_window_size(1024, 768)  # Smaller window size
        
        # Limit Excel data in memory by using chunked processing
        if len(self.translations_df) > 5000:
            # Convert to dict of key translations for faster lookups
            self.translation_lookup = {}
            for _, row in self.translations_df.iterrows():
                key = row['Key']
                self.translation_lookup[key] = {
                    'en': row['Original EN'],
                    'kh': row['KH Confirm from BIC'],
                    'cn': row['CN Confirm from BIC']
                }
            
            # Clear DataFrame to free memory
            self.translations_df = None
            
        # Limit number of mismatches stored to prevent memory issues
        max_mismatches = 1000
        if len(self.results['mismatches']) > max_mismatches:
            logger.warning(f"Limiting stored mismatches to {max_mismatches} to conserve memory")
            self.results['mismatches'] = self.results['mismatches'][:max_mismatches]
        
        # Force garbage collection
        import gc
        gc.collect()
        
    except Exception as e:
        logger.warning(f"Memory optimization failed: {str(e)}")