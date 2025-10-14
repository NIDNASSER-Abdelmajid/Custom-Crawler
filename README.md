# Web Crawler

## Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/NIDNASSER-Abdelmajid/Custom-Crawler
cd Custom-Crawler
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Crawler

<<<<<<< HEAD
**For urls from a region (csv file):**
```bash
# choices: EU, USA
python cli.py -uc eu -t 60 -p profiles
=======
**For multiple URLs (from file):**
```bash
python cli.py -f urls.txt -t 60 -p profiles
>>>>>>> 754b2a60be2389570ea0309ab9e73827e58f3b45
```

**For a single URL:**
```bash
python cli.py -u https://example.com -t 60 -p profiles
```

**Working with Chromium browser:**
```bash
<<<<<<< HEAD
python cli.py -uc usa -t 60 -p profiles -ch
=======
python cli.py -f urls.txt -t 60 -p profiles -ch
>>>>>>> 754b2a60be2389570ea0309ab9e73827e58f3b45
```

## Command Options

| Flag | Description | Default |
|------|-------------|---------|
<<<<<<< HEAD
| `-uc` | Category of URLs to crawl (eu or usa) | - |
=======
| `-f` | Path to URLs file | - |
>>>>>>> 754b2a60be2389570ea0309ab9e73827e58f3b45
| `-u` | Single URL to crawl | - |
| `-t` | Time to spend on each website (seconds) | 60 |
| `-p` | Profiles directory | `./profiles` |
| `-ch` | Chromium path (.exe) | - |
| `-vpn` | Work with vpn (ProtonVPN is the only choice currently) | - |

## Prerequisites

- **Chromium Browser**: Add the chromium browser path to the variable `chromium_path` inside the `helpers\essentials.py` file, and add the `-ch` flag to your command to work withe the chromium browser
- **VPN Configuration**: Add the ProtonVPN path to the variable `vpn_path` inside the `helpers\essentials.py` file, and add the `-vpn` flag to your command
- **URL Format**: URLs don't need protocol prefixes (http/https added automatically)
- **Comments**: Lines starting with `#` are ignored in URL files

## How It Works

The crawler creates isolated browser profiles for each website domain. When visiting a site:
<<<<<<< HEAD

0. **VPN Connection**: In case this option is chosen, the VPN connection is established, and once the script execution is terminated the VPN process is killed
1. **Profile Selection**: Uses or creates a dedicated profile directory for the domain
2. **Initial Navigation**: Loads the website to establish domain context
3. **Websites Navigation**: For each website visited the crawler waits for the duration set, for the user to login, create a new account, or do operations in the website, and the crawling continues by either hitting enter (in case of success), or writing a comment (in case of failure or issue), or the wait duration is up and then a comment is required to pass to the next website if any
4. **Cookie Restoration**: Applies previously saved cookies from earlier sessions
5. **Data Collection**: Captures all network requests and cookies during the visit
6. **Data Persistence**: Saves all collected data to JSON files in the profile directory and also in a `data` folder for easier esploitation, and also save the state of the crawler in the `masterfile.csv` file:

| id | url | crawling status | number of cookies | number of requests | last successful crawl | comment |
|----|-----|-----------------|-------------------|--------------------|-----------------------|---------|
| int | website url | done/failed | int | int | date | string |
=======
0. **VPN Connection**: In case this option is chosen, the VPN connection is established, and once the script execution is terminated the VPN process is killed
1. **Profile Selection**: Uses or creates a dedicated profile directory for the domain
2. **Initial Navigation**: Loads the website to establish domain context
3. **Cookie Restoration**: Applies previously saved cookies from earlier sessions
4. **Data Collection**: Captures all network requests and cookies during the visit
5. **Data Persistence**: Saves all collected data to JSON files in the profile directory
>>>>>>> 754b2a60be2389570ea0309ab9e73827e58f3b45

## Output Structure

```
profiles/
└── website_com/
    ├── data.json          # Captured cookies, requests & metadata
    └── user_data/         # Chrome profile data for this website
```

## Logs

- Current logs: `crawler.log`
- Archived logs: `logs/` directory (rotated automatically)

The crawler maintains complete separation between website sessions while preserving authentication states through cookie persistence, making it ideal for repeated visits to authenticated websites.
