import sqlite3
from selenium import webdriver


###############
### Globals ###
###############

URL_DATABASE = 'urls.sqlite'
DATA_DATABASE = 'data.sqlite'
STARTING_URL = 'http://healthrates.doi.nv.gov/Wizard.aspx?type=Small%20Group'


############
### Code ###
############

def create_url_database():
    con = sqlite3.connect(URL_DATABASE)
    with con:
        cur = con.cursor()
        try:
            cur.execute(
                """
                CREATE TABLE links(
                    id INTEGER PRIMARY KEY, url TEXT)
                """
            )
        except sqlite3.OperationalError:
            pass  # silenced


def create_data_database():
    con = sqlite3.connect(DATA_DATABASE)
    with con:
        cur = con.cursor()
        try:
            cur.execute(
                """
                CREATE TABLE data(
                    id INTEGER PRIMARY KEY,
                    plan_name TEXT,
                    carrier TEXT,
                    metal TEXT,
                    exchange TEXT,
                    county TEXT,
                    cost TEXT,
                    status TEXT,
                    plan_year TEXT,
                    market_sement TEXT,
                    january TEXT,
                    april TEXT,
                    july TEXT,
                    october TEXT,
                    url TEXT,
                    benefist_schedule TEXT
                )
                """
            )
        except sqlite3.OperationalError:
            pass  # silenced


def get_all_data():
    """
    This function navigates to the results page, from the starting URL, and
    grabs all the URLs.
    """
    counter = 1

    # navigate to results page
    driver = webdriver.Firefox()
    driver.get(STARTING_URL)
    driver.find_element_by_class_name('rates_review_button_submit').click()
    driver.find_element_by_tag_name('form').submit()

    # find all links and add each to the DB
    first_element = driver.find_element_by_xpath('//*[@id="resultsBox"]/div[5]')
    all_links = first_element.find_elements_by_xpath('.//*[@href]')
    all_links_length = len(all_links)
    for link in all_links:
        add_link_to_database(link.get_attribute('href'))
        print 'Added link number {0} of {1} to DB'.format(
            counter, all_links_length)
        counter += 1

    driver.quit()


def add_link_to_database(single_link):
    """
    Given a url, update the database.
    """
    con = sqlite3.connect(URL_DATABASE)
    with con:
        cur = con.cursor()
        cur.execute(
            """
            INSERT INTO links(url) VALUES(?)
            """, (single_link,)
        )


def grab_data():
    """
    Grab all data from the links table.
    """
    con = sqlite3.connect(URL_DATABASE)
    with con:
        cur = con.cursor()
        all_links = cur.execute('SELECT * FROM links;')
    return all_links


def get_relevant_data(link):
    """
    Given a link from the links table in the database, scrape relevant data -

        Plan Name
        Carrier
        Metal
        Exchange
        County
        Cost
        Status
        Plan Year
        Market Segment
        January
        April
        July
        October
        URL
        Schedule of Benefits

    - returning a list of dicts
    """
    pass


def main():

    # create databases
    create_url_database()
    create_data_database()

    # grab links, add to database
    # get_all_data()

    # get links from database
    # all_data = grab_data()


if __name__ == '__main__':
    main()
