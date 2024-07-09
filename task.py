from botasaurus import *
import urllib.parse
from botasaurus import AntiDetectDriver
from botasaurus.browser import browser, Driver
from botasaurus.soupify import soupify


MAX_BROWSERS = 5

@browser(
    block_images=True,
    parallel=MAX_BROWSERS,
    reuse_driver=True,
)
def scrape_places(driver: Driver, link):

    # Visit an individual place and extract data
    def scrape_place_data():
        driver.get(link)

        # Accept Cookies for European users
        if driver.is_in_page("https://consent.google.com/"):
            agree_button_selector = 'form:nth-child(2) > div > div > button'
            driver.click(agree_button_selector)
            driver.get(link)

        # Extract title
        title_selector = 'h1'
        title = driver.text(title_selector)

        # Extract rating
        rating_selector = "div.F7nice > span"
        rating = driver.text(rating_selector)

        # Extract reviews count
        reviews_selector = "div.F7nice > span:last-child"
        reviews_text = driver.text(reviews_selector)
        reviews = int(''.join(filter(str.isdigit, reviews_text))
                      ) if reviews_text else None

        # Extract website link
        website_selector = "a[data-item-id='authority']"
        website = driver.link(website_selector)

        # Extract phone number
        phone_xpath = "//button[starts-with(@data-item-id,'phone')]"
        phone_element = driver.get_element_or_none(phone_xpath)
        phone = phone_element.get_attribute(
            "data-item-id").replace("phone:tel:", "") if phone_element else None

        return {
            "title": title,
            "phone": phone,
            "website": website,
            "reviews": reviews,
            "rating": rating,
            "link": link,
        }
    return scrape_place_data()


@browser(
    data=["restaurants in tampa"],
    block_images=True,
)
def scrape_places_links(driver: Driver, query):

    # Visit Google Maps
    def visit_google_maps():
        encoded_query = urllib.parse.quote_plus(query)
        url = f'https://www.google.com/maps/search/{encoded_query}'
        driver.get(url)

        # Accept Cookies for European users
        if driver.is_in_page("https://consent.google.com/"):
            agree_button_selector = 'form:nth-child(2) > div > div > button'
            driver.click(agree_button_selector)
            driver.google_get(url)

    # Scroll to the end of the places list to get all the places
    def scroll_to_end_of_places_list():
        end_of_list_detected = False

        while not end_of_list_detected:
            # Element that holds the list of places
            places_list_element_selector = '[role="feed"]'
            driver.scroll(places_list_element_selector)
            print('Scrolling...')

            # Check if we've reached the end of the list
            end_of_list_indicator_selector = "p.fontBodyMedium > span > span"
            if driver.exists(end_of_list_indicator_selector):
                end_of_list_detected = True

        print("Successfully scrolled to the end of the places list.")

    def extract_place_links():
        places_links_selector = '[role="feed"] > div > div > a'
        return driver.links(places_links_selector)

    visit_google_maps()
    scroll_to_end_of_places_list()

    # Get all place links
    places_links = extract_place_links()

    # Return the places links to be saved as a output/links file
    filename = 'links'
    return filename, places_links

if __name__ == "__main__":
    links = scrape_places_links()
    scrape_places(links)
