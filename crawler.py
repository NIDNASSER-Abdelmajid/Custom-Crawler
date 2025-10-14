import os
import json
import time
import logging
import threading
from datetime import datetime
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

class WebCrawler:
    def __init__(self, profile_dir="profiles", chromium=None, logger=None):

        self.profile_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), profile_dir)
        self.logger = logger or logging.getLogger(__name__)
        self.driver = None
        self.current_profile = None
        self.chromium = chromium

        os.makedirs(self.profile_dir, exist_ok=True)
    
    def _init_driver(self, user_data_dir):
        """Initialize Chrome WebDriver with custom binary location"""
        
        chrome_options = Options()
        # if self.chromium:
        #     chrome_options.binary_location = self.chromium

        chrome_options.add_argument("--start-maximized")
        # chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
        
        chrome_options.add_argument("--no-sandbox")
        
        chrome_options.add_argument("--remote-debugging-port=9222")
        # chrome_options.add_argument("--autoplay-policy=no-user-gesture-required")
        # chrome_options.add_argument("--enable-features=MediaFoundationH264Remoting,UseChromeOSDirectVideoDecoder")
        # chrome_options.add_argument("--disable-features=HardwareMediaKeyHandling")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        chrome_options.add_experimental_option("useAutomationExtension", False)


        # TODO: Implement next step here

        try:
            self.driver = webdriver.Chrome(
                options=chrome_options
            )
            self.logger.info("ChromeDriver initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing ChromeDriver: {e}")
            
            try:
                self.logger.info("Trying fallback initialization...")
                self.driver = webdriver.Chrome(options=chrome_options)

                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

                self.logger.info("ChromeDriver initialized with fallback method")
                return True
            except Exception as e2:
                self.logger.error(f"Fallback initialization also failed: {e2}")
                return False
    
    def _get_profile_name(self, url):
        """Extract profile name from URL"""
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.replace("www.", "")
        safe_domain = "".join(c if c.isalnum() else "_" for c in domain)
        return safe_domain
    
    def _get_user_data_dir(self, profile_name):
        """Get user data directory for specific profile"""
        return os.path.join(self.profile_dir, profile_name, "user_data")
    
    def _ensure_directories(self, profile_name):
        """Create necessary directories for a profile"""
        profile_path = os.path.join(self.profile_dir, profile_name)
        user_data_dir = self._get_user_data_dir(profile_name)
        
        os.makedirs(profile_path, exist_ok=True)
        os.makedirs(user_data_dir, exist_ok=True)
        
        return profile_path, user_data_dir
    
    def _capture_network_requests(self):
        """Capture network requests"""
        try:
            logs = self.driver.get_log("performance")
            requests = []
            
            for log_entry in logs:
                try:
                    log_message = json.loads(log_entry["message"])["message"]
                    
                    if log_message["method"] == "Network.requestWillBeSent":
                        request = log_message["params"]["request"]
                        requests.append({
                            "url": request["url"],
                            "method": request["method"],
                            "timestamp": datetime.fromtimestamp(log_entry["timestamp"] / 1000).isoformat()
                        })
                except Exception:
                    continue
            
            return requests
        except Exception as e:
            self.logger.error(f"Error capturing requests: {e}")
            return []

    def _capture_all_cookies(self):
        """Capture all cookies (standard, CDP, JS) and merge them."""
        all_cookies = []

        # 1. Normal cookies
        try:
            selenium_cookies = self.driver.get_cookies()
            all_cookies.extend(selenium_cookies)
        except Exception as e:
            if self.logger: self.logger.error(f"Selenium get_cookies failed: {e}")

        # 2. CDP cookies
        try:
            cdp_cookies = self.driver.execute_cdp_cmd("Network.getAllCookies", {}).get("cookies", [])
            all_cookies.extend(cdp_cookies)
        except Exception as e:
            if self.logger: self.logger.error(f"CDP getAllCookies failed: {e}")

        seen = set()
        unique_cookies = []
        for c in all_cookies:
            key = (c.get("name"), c.get("domain"), c.get("path"))
            if key not in seen:
                seen.add(key)
                unique_cookies.append(c)

        return unique_cookies


    def _save_data(self, profile_path, url, cookies, requests):
        """Save all data to JSON file"""
        data_file = os.path.join(profile_path, "data.json")
        parsed_url = url.replace("www.","").replace(".", "_").split("//")[-1]
        
        crawler_data = {
            "url": url,
            "timestamp": datetime.now().isoformat(),
            "page_title": self.driver.title if self.driver else "",
            "cookies": cookies,
            "requests": requests,
            "cookies_count": len(cookies),
            "requests_count": len(requests)
        }
        
        try:
            with open(data_file, "w", encoding="utf-8") as f:
                json.dump(crawler_data, f, indent=2, ensure_ascii=False)
            with open(f"data/{parsed_url}.json", "w", encoding="utf-8") as f:
                json.dump(crawler_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Data saved: {len(requests)} requests, {len(cookies)} cookies")
            
        except Exception as e:
            self.logger.error(f"Error saving data: {e}")
    
    def visit_website(self, website_index, url, wait_time=10):
        """Visit a website and capture data"""
        try:
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
            
            profile_name = self._get_profile_name(url)
            self.current_profile = profile_name
            
            profile_path, user_data_dir = self._ensure_directories(profile_name)
            
            self.logger.info(f"Using profile: {profile_name}")
            
            if self.driver:
                self.driver.quit()
                self.driver = None
            
            if not self._init_driver(user_data_dir):
                raise RuntimeError("Failed to initialize ChromeDriver")
            
            parsed_url = urlparse(url)
            domain_root = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            self.logger.info(f"Navigating to domain root first: {domain_root}")
            self.driver.get(domain_root)
            
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            data_file = os.path.join(profile_path, "data.json")
            data_folder = "data"
            os.makedirs(data_folder, exist_ok=True)
            if os.path.exists(data_file):
                try:
                    with open(data_file, "r") as f:
                        existing_data = json.load(f)
                        cookies = existing_data.get("cookies", [])
                    self.driver.delete_all_cookies()
                    
                    current_domain = parsed_url.netloc
                    for cookie in cookies:
                        cookie_domain = cookie.get("domain", "")                        
                        if cookie_domain:
                            cookie_domain_clean = cookie_domain.lstrip(".").lstrip("www.")
                            
                            domain_matches = (
                                cookie_domain_clean == current_domain or
                                current_domain == "." + cookie_domain_clean or
                                current_domain.startswith == ".www." + cookie_domain_clean or
                                current_domain.startswith == "www." + cookie_domain_clean
                            )

                            # print(current_domain, cookie_domain_clean, domain_matches)
                            
                            if not domain_matches:
                                self.logger.warning(f"Skipping cookie {cookie.get("name")} with domain {cookie_domain} for {current_domain}")
                                continue
                        
                        cookie_copy = cookie.copy()
                        for key in list(cookie_copy.keys()):
                            if key not in ["name", "value", "domain", "path", "expiry", "secure", "httpOnly"]:
                                del cookie_copy[key]
                        
                        try:
                            self.driver.add_cookie(cookie_copy)
                            self.logger.info(f"Set cookie: {cookie.get("name")}")
                        except Exception as e:
                            self.logger.warning(f"Could not set cookie {cookie.get("name")}: {e}")
                    
                    self.logger.info(f"Set {len(cookies)} cookies from previous session")
                    
                except Exception as e:
                    self.logger.error(f"Error setting cookies: {e}")
            
            self.logger.info(f"Going to: {url} in 5s...")
            time.sleep(3.11)
            self.driver.get(url)
            
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            self.logger.info(f"Waiting for {wait_time} seconds...")
            # time.sleep(wait_time)
            comment = [""]
            input_received = threading.Event()

            def wait_for_input():
                self.logger.info("Enter a comment for this crawl (or press Enter to skip): ")
                comment[0] = input("> ")
                input_received.set()

            input_thread = threading.Thread(target=wait_for_input)
            input_thread.daemon = True
            input_thread.start()

            input_received.wait(timeout=wait_time)

            if not input_received.is_set():
                print() # Move to next line after timeout
                self.logger.info("No input received, proceeding without comment.")
                self.logger.info("Enter a comment to continue: ")
                input_thread.join()
            
            comment = comment[0]
            
            self.logger.info("Capturing data...")
            cookies = self._capture_all_cookies()
            requests = self._capture_network_requests()  
            self._save_data(profile_path, url, cookies, requests)

            #input the comment
            # comment = self.logger.info("Please enter a comment for this crawl (or press Enter to skip): ")
            # comment = input()
            # check by url if already in csv, to update it, else append it
            with open('masterfile.csv', 'r+', encoding='utf-8') as mf:
                lines = mf.readlines()
                for i, line in enumerate(lines):
                    if url in line:
                        lines[i] = f'{website_index},{url},"{self.driver.title}",{"Success" if not comment else "Failed"},{len(cookies)},{len(requests)},{datetime.now().isoformat()},{comment}\n'
                        break
                else:
                    lines.append(f'{website_index},{url},"{self.driver.title}",{ "Success" if not comment else "Failed" },{len(cookies)},{len(requests)},{datetime.now().isoformat()},{comment}\n')
                mf.seek(0)
                mf.writelines(lines)
                mf.truncate()
            self.logger.info(f"Title: {self.driver.title}")
            self.logger.info(f"URL(last visited page/subpage): {self.driver.current_url}")
            self.logger.info(f"Cookies: {len(cookies)}")
            self.logger.info(f"Requests: {len(requests)}")
            
        except Exception as e:
            self.logger.error(f"Error visiting {url}: {e}")
            
            if self.driver:
                self.driver.quit()
                self.driver = None

            try:
                with open('masterfile.csv', 'r+', encoding='utf-8') as mf:
                    lines = mf.readlines()
                    for i, line in enumerate(lines):
                        if url in line:
                            lines[i] = f'{website_index},{url},"",Failed,0,0,{datetime.now().isoformat()},Connection timeout\n'
                            break
                    else:
                        lines.append(f'{website_index},{url},"",Failed,0,0,{datetime.now().isoformat()},Connection timeout\n')
                    mf.seek(0)
                    mf.writelines(lines)
                    mf.truncate()
            except Exception as csv_error:
                self.logger.error(f"Error updating CSV: {csv_error}")
            raise

    def close(self):
        """Close the browser"""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("Browser closed")
            except Exception:
                pass
            finally:
                self.driver = None
