import argparse
import json
import logging
import os
import sys
from datetime import datetime
from src.tester import TranslationTester

from src.config_manager import ConfigManager

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run translation tests for web application')
    parser.add_argument('--config', type=str, help='Path to configuration file')
    parser.add_argument('--url', type=str, help='Base URL of the application')
    parser.add_argument('--excel', type=str, help='Path to Excel file with translations')
    parser.add_argument('--username', type=str, help='Username for login')
    parser.add_argument('--password', type=str, help='Password for login')
    parser.add_argument('--browser', type=str, default='chrome', help='Browser to use (chrome, firefox, edge)')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    parser.add_argument('--report-dir', type=str, default='reports', help='Directory for reports')
    
    args = parser.parse_args()
    
    # Initialize config manager
    config_manager = ConfigManager(args.config)
    
    # Override config with command line arguments if provided
    if args.url:
        config_manager.set_config('base_url', args.url)
    if args.excel:
        config_manager.set_config('excel_path', args.excel)
    if args.username:
        config_manager.set_config('username', args.username)
    if args.password:
        config_manager.set_config('password', args.password)
    if args.browser:
        config_manager.set_config('browsers', [args.browser])
    if args.headless:
        config_manager.set_config('headless', True)
    
    config = config_manager.get_config()
    
    # Validate required config values
    required_config = ['base_url', 'excel_path', 'username', 'password']
    missing_config = [key for key in required_config if not config[key]]
    
    if missing_config:
        print(f"Missing required configuration: {', '.join(missing_config)}")
        print("Please provide via config file or command line arguments.")
        sys.exit(1)
    
    # Run tests
    if len(config['browsers']) > 1:
        # Run parallel tests on multiple browsers
        results = run_parallel_tests(
            config['base_url'],
            config['excel_path'],
            config['username'],
            config['password'],
            config['browsers']
        )
        
        # Print results
        print("\nTest Results:")
        for browser, result in results.items():
            print(f"  {browser}: {'Passed' if result else 'Failed'}")
    else:
        # Run single browser test
        tester = TranslationTester(
            config['base_url'],
            config['excel_path'],
            config['username'],
            config['password']
        )
        
        # Configure additional options
        tester.headless = config['headless']
        tester.wait_time = config['wait_time']
        tester.check_dynamic_content = config['check_dynamic_content']
        tester.screenshot_on_mismatch = config['screenshot_on_mismatch']
        
        # Run the test
        result = tester.run_test()
        
        # Print result
        print(f"\nTest Result: {'Passed' if result else 'Failed'}")
        
        # Print report location if generated
        if hasattr(tester, 'report_file') and tester.report_file:
            print(f"Report generated: {tester.report_file}")

if __name__ == "__main__":
    main()
