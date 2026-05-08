#!/usr/bin/env python3
"""
Microsoft Windows Direct Download Link Generator (Playwright)
Author: kelexine (https://github.com/kelexine)

Uses Playwright browser automation to extract JavaScript-generated direct download links.
Includes user-agent rotation and random delays to avoid rate limiting.
"""

import logging
import re
import random
import time
from typing import Optional, Dict, List
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

logger = logging.getLogger(__name__)


class MicrosoftPlaywrightDownloader:
    """Generate direct download links using Playwright browser automation"""
    
    DOWNLOAD_PAGE = "https://www.microsoft.com/en-us/software-download/windows11"
    
    # Pool of 10 different user agents for rotation
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 Edg/118.0.2088.76',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0'
    ]
    
    # Track which agents have been used (class-level for global rotation)
    _agent_pool = []
    _agent_index = 0
    
    def __init__(self, headless: bool = True, timeout: int = 60000, min_delay: float = 1.0, max_delay: float = 3.0, language: str = "French"):
        """
        Initialize Playwright downloader

        Args:
            headless: Run browser in headless mode
            timeout: Page load timeout in milliseconds
            min_delay: Minimum delay between actions (seconds)
            max_delay: Maximum delay between actions (seconds)
            language: Language label as displayed in the Microsoft dropdown (e.g. "French", "English (United States)")
        """
        self.headless = headless
        self.timeout = timeout
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.language = language
        
        # Initialize agent pool if empty
        if not MicrosoftPlaywrightDownloader._agent_pool:
            MicrosoftPlaywrightDownloader._agent_pool = self.USER_AGENTS.copy()
            random.shuffle(MicrosoftPlaywrightDownloader._agent_pool)
    
    def _get_next_user_agent(self) -> str:
        """Get next user agent in round-robin fashion"""
        # Get current agent from pool
        agent = MicrosoftPlaywrightDownloader._agent_pool[MicrosoftPlaywrightDownloader._agent_index]
        
        # Move to next agent
        MicrosoftPlaywrightDownloader._agent_index += 1
        
        # If we've used all agents, reshuffle and reset
        if MicrosoftPlaywrightDownloader._agent_index >= len(MicrosoftPlaywrightDownloader._agent_pool):
            logger.debug("🔄 All user agents used, reshuffling pool...")
            random.shuffle(MicrosoftPlaywrightDownloader._agent_pool)
            MicrosoftPlaywrightDownloader._agent_index = 0
        
        logger.debug(f"🎭 Using user agent: {agent[:50]}...")
        return agent
    
    def _random_delay(self, min_override: Optional[float] = None, max_override: Optional[float] = None):
        """Add random delay between actions"""
        min_delay = min_override if min_override is not None else self.min_delay
        max_delay = max_override if max_override is not None else self.max_delay
        
        delay = random.uniform(min_delay, max_delay)
        logger.debug(f"⏱️  Waiting {delay:.2f}s...")
        time.sleep(delay)
    
    def get_windows11_link(self) -> Optional[str]:
        """
        Get direct download link for Windows 11 ISO using browser automation
        
        Returns:
            Direct download URL or None
        """
        logger.info(f"🌐 Launching Playwright browser automation...")
        logger.info(f"💡 This will interact with Microsoft's page to extract the download link")
        
        try:
            with sync_playwright() as p:
                # Get next user agent from rotation pool
                user_agent = self._get_next_user_agent()
                
                # Launch browser
                logger.debug(f"Starting Chromium (headless={self.headless})...")
                browser = p.chromium.launch(headless=self.headless)
                context = browser.new_context(user_agent=user_agent)
                page = context.new_page()
                page.set_default_timeout(self.timeout)  # Ensure configured timeout applies to all actions
                
                # Navigate to download page
                logger.info(f"📥 Navigating to: {self.DOWNLOAD_PAGE}")
                page.goto(self.DOWNLOAD_PAGE, wait_until='domcontentloaded', timeout=self.timeout)
                
                # Step 1: Wait for and select product edition dropdown
                logger.info(f"⏳ Waiting for product edition dropdown (#product-edition)...")
                page.wait_for_selector('#product-edition', timeout=self.timeout)
                
                # Random delay before selection to mimic human behavior
                self._random_delay(0.5, 1.5)
                
                # Select Windows 11 multi-edition ISO (value="3262")
                logger.info(f"✅ Selecting Windows 11 multi-edition (value=3262)...")
                page.select_option('#product-edition', value='3262')
                
                self._random_delay(0.5, 1.0)
                
                # Step 2: Click the confirm button (#submit-product-edition)
                logger.info(f"🖱️  Clicking submit button (#submit-product-edition)...")
                page.click('#submit-product-edition')
                
                # Wait for network activity to settle
                self._random_delay(2.0, 4.0)
                
                # Step 3: Wait for language dropdown to appear
                logger.info(f"⏳ Waiting for language dropdown (#product-languages)...")
                page.wait_for_selector('#product-languages', timeout=self.timeout)
                
                # Get all available languages for logging
                language_options = page.locator('#product-languages option').all_text_contents()
                logger.info(f"🌍 Found {len(language_options)} language options")
                
                self._random_delay(0.5, 1.5)
                
                # Step 4: Select the requested language
                # NOTE: We select by label to ensure we get the correct language regardless of list order
                logger.info(f"✅ Selecting language: {self.language}...")

                # Try the requested label, with sensible fallbacks for French / English
                fallback_labels = {
                    'French': ['Français', 'French (France)'],
                    'English': ['English (United States)', 'English International'],
                    'English (United States)': ['English International'],
                }.get(self.language, [])

                attempted = [self.language] + fallback_labels
                last_error = None
                selected = False
                for label in attempted:
                    try:
                        page.select_option('#product-languages', label=label)
                        logger.info(f"✅ Selected language label: {label}")
                        selected = True
                        break
                    except Exception as e:
                        logger.warning(f"Could not select '{label}': {e}")
                        last_error = e

                if not selected:
                    available = page.locator('#product-languages option').all_text_contents()
                    logger.error(f"❌ No matching language label found. Available: {available}")
                    raise last_error if last_error else RuntimeError("Language selection failed")
                
                self._random_delay(0.5, 1.0)
                
                # Step 5: Click the second confirm button (#submit-sku)
                logger.info(f"🖱️  Clicking language submit button (#submit-sku)...")
                page.click('#submit-sku')
                
                # Wait for download link generation
                self._random_delay(2.0, 4.0)
                
                # Step 6: Wait for download button to appear
                logger.info(f"⏳ Waiting for download button (a.btn.btn-primary)...")
                page.wait_for_selector('a.btn.btn-primary', timeout=self.timeout)
                
                # Extract the download link - filter for "64-bit" text to get ISO (not Installation Assistant)
                logger.info(f"🔍 Looking for 64-bit download button...")
                download_button = page.locator('a.btn.btn-primary').filter(has_text='64-bit').first
                download_url = download_button.get_attribute('href')
                
                if not download_url:
                    logger.error("❌ Download button has no href")
                    browser.close()
                    return None
                
                logger.info(f"✅ Successfully extracted download link!")
                logger.info(f"🔗 URL: {download_url[:100]}...")
                
                # Verify it's an ISO link
                if '.iso' in download_url.lower():
                    logger.info(f"✅ Confirmed: URL contains .iso")
                else:
                    logger.warning(f"⚠️  Warning: URL doesn't contain .iso")
                
                browser.close()
                return download_url
                
        except PlaywrightTimeout as e:
            logger.error(f"❌ Timeout waiting for page element: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Error during browser automation: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return None
    
    def get_all_versions(self) -> List[Dict]:
        """
        Get Windows 11 version with direct download link
        
        Returns:
            List of dicts with version info and download URLs
        """
        logger.info("📋 Fetching Windows 11 direct download link via Playwright...")
        
        versions = []
        
        # Get direct link
        direct_url = self.get_windows11_link()
        
        if direct_url:
            # Extract version from URL if possible
            version_match = re.search(r'(\d{2}H\d)', direct_url)
            version = version_match.group(1) if version_match else "Latest"
            
            # Extract build number if present
            build_match = re.search(r'(\d{5}\.\d+)', direct_url)
            build_number = build_match.group(1) if build_match else "Latest"
            
            versions.append({
                'version': version,
                'title': f'Windows 11 {version}',
                'iso_url': direct_url,
                'source': 'microsoft_playwright',
                'detected_date': datetime.now().isoformat(),
                'build_number': build_number,
                'build_id': f'msft-playwright-{version.lower()}-{datetime.now().strftime("%Y%m%d")}',
                'architecture': 'amd64',
                'channel': 'retail',
                'language': 'en-us'
            })
            
            logger.info(f"✅ Successfully created release entry for {version}")
        
        return versions


def test_playwright_download():
    """Test Playwright-based direct download link extraction"""
    print("\n" + "=" * 70)
    print("Testing Playwright Browser Automation")
    print("=" * 70 + "\n")
    
    downloader = MicrosoftPlaywrightDownloader(headless=True)
    
    print("🌐 Starting browser automation...")
    print("⏳ This may take 10-30 seconds...\n")
    
    link = downloader.get_windows11_link()
    
    print()
    if link:
        print(f"✅ SUCCESS!")
        print(f"\nDirect Download URL:")
        print(f"{link}\n")
        
        # Verify it's a direct ISO link
        if link.lower().endswith('.iso'):
            print(f"✅ URL ends with .iso - confirmed direct link")
        elif '.iso' in link.lower():
            print(f"✅ URL contains .iso - likely direct link with parameters")
        else:
            print(f"⚠️  URL doesn't appear to be an ISO link")
        
        # Try to get file size
        try:
            import requests
            response = requests.head(link, timeout=10, allow_redirects=True)
            if 'content-length' in response.headers:
                size_gb = int(response.headers['content-length']) / (1024**3)
                print(f"✅ ISO Size: {size_gb:.2f} GB")
            else:
                print(f"ℹ️  Could not determine file size (link may be time-limited)")
        except Exception as e:
            print(f"ℹ️  Could not verify file size: {e}")
        
    else:
        print(f"❌ FAILED to get direct download link")
        print(f"\nCheck the logs above for details.")
    
    print("\n" + "=" * 70 + "\n")


if __name__ == '__main__':
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Fetch a fresh direct Windows 11 ISO download URL from Microsoft.")
    parser.add_argument('--language', default='French',
                        help="Language label as shown in the MS dropdown (default: French). Examples: French, English (United States), Spanish, German.")
    parser.add_argument('--test', action='store_true',
                        help="Run the verbose self-test instead of just printing the URL.")
    parser.add_argument('--quiet', action='store_true',
                        help="Suppress logging on stderr; only print the URL on stdout.")
    args = parser.parse_args()

    log_level = logging.WARNING if args.quiet else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        stream=sys.stderr,
    )

    if args.test:
        test_playwright_download()
        sys.exit(0)

    downloader = MicrosoftPlaywrightDownloader(headless=True, language=args.language)
    url = downloader.get_windows11_link()
    if not url:
        print("ERROR: failed to retrieve direct download URL", file=sys.stderr)
        sys.exit(1)
    # Stdout = URL only, so callers can capture it cleanly.
    print(url)
