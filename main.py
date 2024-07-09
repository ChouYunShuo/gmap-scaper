from playwright.sync_api import sync_playwright
from dataclasses import dataclass, asdict, field
import pandas as pd
import argparse
import os
from datetime import datetime

@dataclass
class Business:
    """Holds business data"""
    name: str = None
    address: str = None
    website: str = None
    phone_number: str = None
    reviews_count: int = None
    reviews_average: float = None

@dataclass
class BusinessList:
    """Holds list of Business objects and saves to both excel and csv"""
    business_list: list[Business] = field(default_factory=list)
    save_at: str = 'output'

    def dataframe(self):
        """Transform business_list to pandas dataframe"""
        return pd.json_normalize(
            (asdict(business) for business in self.business_list), sep="_"
        )

    def save_to_excel(self, filename):
        """Saves pandas dataframe to excel (xlsx) file"""
        if not os.path.exists(self.save_at):
            os.makedirs(self.save_at)
        self.dataframe().to_excel(f"{self.save_at}/{filename}.xlsx", index=False)

    def save_to_csv(self, filename):
        """Saves pandas dataframe to csv file"""
        if not os.path.exists(self.save_at):
            os.makedirs(self.save_at)
        self.dataframe().to_csv(f"{self.save_at}/{filename}.csv", index=False)

def scrape_listings(page, total):
    listings = []
    previously_counted = 0
    while True:
        page.mouse.wheel(0, 10000)
        page.wait_for_timeout(3000)

        current_count = page.locator('//a[contains(@href, "https://www.google.com/maps/place")]').count()
        if current_count >= total:
            listings = page.locator('//a[contains(@href, "https://www.google.com/maps/place")]').all()[:total]
            break
        elif current_count == previously_counted:
            listings = page.locator('//a[contains(@href, "https://www.google.com/maps/place")]').all()
            break
        else:
            previously_counted = current_count
    return listings

def scrape_business_details(page, listings):
    business_list = BusinessList()
    name_xpath = '//h1[contains(@class, "DUwDvf")]'
    address_xpath = '//button[@data-item-id="address"]//div[contains(@class, "fontBodyMedium")]'
    website_xpath = '//a[@data-item-id="authority"]//div[contains(@class, "fontBodyMedium")]'
    phone_number_xpath = '//button[contains(@data-item-id, "phone:tel:")]//div[contains(@class, "fontBodyMedium")]'
    review_count_xpath = '//button[contains(@jsaction,"reviewChart.moreReviews")]//span'
    reviews_average_xpath = '//div[contains(@jsaction,"reviewChart.moreReviews")]//div[@role="img"]'

    for listing in listings:
        try:
            listing.click()
            page.wait_for_timeout(5000)

            business = Business()
            business.name = page.locator(name_xpath).inner_text() if page.locator(name_xpath).count() > 0 else ""
            business.address = page.locator(address_xpath).inner_text() if page.locator(address_xpath).count() > 0 else ""
            business.website = page.locator(website_xpath).inner_text() if page.locator(website_xpath).count() > 0 else ""
            business.phone_number = page.locator(phone_number_xpath).inner_text() if page.locator(phone_number_xpath).count() > 0 else ""
            business.reviews_count = int(page.locator(review_count_xpath).inner_text().split()[0].replace(',', '')) if page.locator(review_count_xpath).count() > 0 else 0
            business.reviews_average = float(page.locator(reviews_average_xpath).get_attribute('aria-label').split()[0].replace(',', '.')) if page.locator(reviews_average_xpath).count() > 0 else 0.0

            business_list.business_list.append(business)
        except Exception as e:
            print(f'Error occurred: {e}')
    return business_list

def merge_files(timestamp, search_for):
    """Merge all CSV and XLSX files with the same search_for name"""
    print(f"Merging all {search_for} files...")
    output_dir = 'output'
    search_pattern = search_for.replace(' ', '_')
    
    # Merge CSV files
    csv_files = [os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.endswith(f'{search_pattern}.csv')]
    df_list = [pd.read_csv(file) for file in csv_files]
    if df_list:
        merged_df = pd.concat(df_list, ignore_index=True).drop_duplicates()
        merged_df.to_csv(f"{output_dir}/merged_{timestamp}_{search_pattern}.csv", index=False)
    
    # Merge XLSX files
    xlsx_files = [os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.endswith(f'{search_pattern}.xlsx')]
    df_list = [pd.read_excel(file) for file in xlsx_files]
    if df_list:
        merged_df = pd.concat(df_list, ignore_index=True).drop_duplicates()
        merged_df.to_excel(f"{output_dir}/merged_{timestamp}_{search_pattern}.xlsx", index=False)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--search", type=str, required=True)
    parser.add_argument("-t", "--total", type=int, default=1000)
    args = parser.parse_args()

    search_list = [args.search]
    total = args.total
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        for search_for in search_list:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            print(f"Scraping: {search_for}")
            page.goto("https://www.google.com/maps", timeout=60000)
            page.wait_for_timeout(3000)
            page.fill('//input[@id="searchboxinput"]', search_for)
            page.keyboard.press("Enter")
            page.wait_for_timeout(5000)
            page.hover('//a[contains(@href, "https://www.google.com/maps/place")]')

            listings = scrape_listings(page, total)
            business_list = scrape_business_details(page, listings)

            business_list.save_to_excel(f"{timestamp}_{search_for.replace(' ', '_')}")
            business_list.save_to_csv(f"{timestamp}_{search_for.replace(' ', '_')}")

            merge_files(timestamp, search_for)

        browser.close()

if __name__ == "__main__":
    main()
