import argparse
import os
import shutil
import logging
from datetime import datetime
from crawler import WebCrawler

def setup_logging():
    """Setup logging configuration with log rotation into logs/ folder"""
    log_file = 'crawler.log'
    logs_dir = 'logs'

    os.makedirs(logs_dir, exist_ok=True)

    if os.path.exists(log_file) and os.path.getsize(log_file) > 0:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archived_log = os.path.join(logs_dir, f"crawler_{timestamp}.log")
        shutil.copy(log_file, archived_log)

        open(log_file, 'w').close()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

    return logging.getLogger(__name__)

def read_urls_from_file(file_path):
    """Read URLs from a file"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            file_urls = f.read().splitlines()
            urls = [url.strip().replace('\n', '') for url in file_urls if url.strip() and '#' not in url]
        return urls
    except Exception as e:
        raise IOError(f"Error reading file {file_path}: {e}")

def main():
    parser = argparse.ArgumentParser(description='Simple Web Crawler')
    
    url_group = parser.add_mutually_exclusive_group(required=True)
    url_group.add_argument('-u', '--url', help='Single URL to crawl')
    url_group.add_argument('-f', '--file', help='Path to file containing URLs')
    
    parser.add_argument('-t', '--time', type=int, default=60, 
                       help='Time to wait on each website (seconds)')
    parser.add_argument('-p', '--profile-dir', default='profiles',
                       help='Directory to store website profiles')
    parser.add_argument('-ch', '--chromium', help='Path to Chromium executable')

    args = parser.parse_args()
    
    if args.file:
        urls = read_urls_from_file(args.file)
    else:
        urls = [args.url]

    if not urls:
        print("No URLs provided or found in file.")
        return
    
    logger = setup_logging()
    logger.info(f"Starting crawler with {len(urls)} URLs")

    crawler = WebCrawler(profile_dir=args.profile_dir, chromium=args.chromium, logger=logger)

    try:
        for i, url in enumerate(urls, 1):
            logger.info(f"[{i}/{len(urls)}] Crawling: {url}")
            
            crawler.visit_website(url, wait_time=args.time)
    
    except KeyboardInterrupt:
        logger.warning("Crawler interrupted by user")
    except Exception as e:
        logger.error(f"Error during crawling: {e}")
    finally:
        crawler.close()
        logger.info("Crawler session completed")

if __name__ == "__main__":
    main()