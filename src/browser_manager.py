import concurrent.futures

def run_parallel_tests(base_url, excel_path, username, password, browsers=None):
    """
    Run tests in parallel on multiple browsers
    
    Args:
        base_url (str): The URL of the web application
        excel_path (str): Path to the Excel file containing translations
        username (str): Username for authentication
        password (str): Password for authentication
        browsers (list): List of browser names to test on (e.g., ['chrome', 'firefox', 'edge'])
    """
    if browsers is None:
        browsers = ['chrome']
    
    results = {}
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(browsers)) as executor:
        future_to_browser = {
            executor.submit(run_test_on_browser, browser, base_url, excel_path, username, password): browser
            for browser in browsers
        }
        
        for future in concurrent.futures.as_completed(future_to_browser):
            browser = future_to_browser[future]
            try:
                results[browser] = future.result()
            except Exception as e:
                logger.error(f"Test on {browser} generated an exception: {str(e)}")
                results[browser] = False
    
    return results

def run_test_on_browser(browser, base_url, excel_path, username, password):
    """Run test on a specific browser"""
    try:
        # Setup WebDriver based on browser
        if browser.lower() == 'chrome':
            from selenium.webdriver.chrome.service import Service
            from webdriver_manager.chrome import ChromeDriverManager
            
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-notifications")
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        elif browser.lower() == 'firefox':
            from selenium.webdriver.firefox.service import Service
            from webdriver_manager.firefox import GeckoDriverManager
            
            firefox_options = webdriver.FirefoxOptions()
            firefox_options.add_argument("--start-maximized")
            driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=firefox_options)
        elif browser.lower() == 'edge':
            from selenium.webdriver.edge.service import Service
            from webdriver_manager.microsoft import EdgeChromiumDriverManager
            
            edge_options = webdriver.EdgeOptions()
            edge_options.add_argument("--start-maximized")
            edge_options.add_argument("--disable-notifications")
            driver = webdriver.Edge(service=Service(EdgeChromiumDriverManager().install()), options=edge_options)
        else:
            logger.error(f"Unsupported browser: {browser}")
            return False
            
        # Create tester with custom driver
        tester = TranslationTester(base_url, excel_path, username, password)
        tester.driver = driver
        
        # Load translations
        tester.load_translations()
        
        # Run the test
        result = tester.run_test()
        
        return result
    except Exception as e:
        logger.error(f"Test on {browser} failed: {str(e)}")
        return False