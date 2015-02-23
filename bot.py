import os
import sqlite3
import datetime
import logging

from selenium import webdriver


###########
# Globals #
###########

YEAR = '2014'
TYPE = 'Individual HSA'
CREATE_DATABASE = True

COUNTIES = ['Carson City', 'Elko', 'Nye', 'Washoe']
DATABASE = 'data_{0}_{1}.sqlite'.format(YEAR, TYPE.replace(' ', ''))
STARTING_URL = 'http://healthrates.doi.nv.gov/Wizard.aspx?type=Small%20Group'
BAD_LINKS = [
    'http://exchange.nv.gov/',
    'http://healthrates.doi.nv.gov/Default.aspx#',
    'http://www.nevadahealthlink.com/'
]

logging.basicConfig(filename="error.log", level=logging.INFO)
log = logging.getLogger("ex")


########
# Code #
########

def create_database_and_tables():

    print("Creating database...")

    con = sqlite3.connect(DATABASE)
    with con:
        cur = con.cursor()
        try:
            cur.execute(
                """
                CREATE TABLE links(
                    id INTEGER PRIMARY KEY, url TEXT, county_name TEXT)
                """
            )
        except sqlite3.OperationalError:
            log.exception("Error!")
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
                    benefit_schedule TEXT
                )
                """
            )
        except sqlite3.OperationalError:
            log.exception("Error!")


def get_all_data():

    """
    This function navigates to the results page, from the starting URL, and
    grabs all the URLs.
    """

    print("Grabbing links...")

    # driver = webdriver.Firefox()
    driver = webdriver.PhantomJS()

    for county in COUNTIES:

        counter = 1

        # navigate to results page
        driver.get(STARTING_URL)
        driver.find_element_by_class_name('rates_review_button_submit').click()
        driver.find_element_by_tag_name('form').submit()

        # perform search
        driver.find_element_by_xpath(
            "//select[@name='type']/option[text()='"+TYPE+"']").click()
        driver.find_element_by_xpath(
            "//select[@name='planyear']/option[text()='"+YEAR+"']").click()
        driver.find_element_by_xpath(
            "//select[@name='county']/option[text()='"+county+"']").click()

        driver.find_element_by_tag_name('form').submit()

        # find all links and add each to the DB
        first_element = driver.find_element_by_xpath(
            '//*[@id="resultsBox"]/div[5]')
        all_links = first_element.find_elements_by_xpath('.//*[@href]')
        cleaned_links = cleanup_links(all_links)
        all_links_length = len(all_links)
        for link in cleaned_links:
            add_link_to_database(link, county)
            print('Added link # {0} of {1} in {2} county to DB'.format(
                counter, all_links_length, county))
            counter += 1

    driver.quit()


def cleanup_links(all_links_list_of_objects):
    clean_links = []
    for link in all_links_list_of_objects:
        if str(link.get_attribute('href')) != BAD_LINKS[0] and \
           str(link.get_attribute('href')) != BAD_LINKS[1] and \
           str(link.get_attribute('href')) != BAD_LINKS[2]:
            clean_links.append(link.get_attribute('href'))
    return clean_links


def add_link_to_database(single_link, county):

    """
    Given a url, update the database.
    """
    con = sqlite3.connect(DATABASE)
    with con:
        cur = con.cursor()
        cur.execute(
            """
            INSERT INTO links(url, county_name) VALUES(?, ?)
            """, (single_link, county)
        )


def cleanup_database():
    print("Removing bad links...")
    con = sqlite3.connect(DATABASE)
    with con:
        cur = con.cursor()
        for link in BAD_LINKS:
            cur.execute('DELETE FROM links WHERE url=?', (link,))


def grab_links_from_database():

    """
    Grab all data from the links table.
    """

    print("Scraping data...")

    counter = 1

    con = sqlite3.connect(DATABASE)
    with con:
        cur = con.cursor()
        cur.execute('SELECT * FROM links')
        all_database_rows = len(cur.fetchall())
        for row_id in range(1, all_database_rows+1):
            cur.execute('SELECT * FROM links WHERE id=?', (row_id,))
            link = cur.fetchone()
            if link:
                data_object = get_relevant_data(link[1])
                if data_object:
                    print('Added scraped link # {0} of {1} to the DB.'.format(
                        counter, all_database_rows))
                    add_relevant_data_to_database(data_object)
                counter += 1


def get_relevant_data(link):
    """
    Given a link from the links table in the database, scrape relevant data -

        Plan Name
        Carrier
        Metal
        Exchange
        County
        Proposed Cost
        Status
        Plan Year
        Market Segment
        January
        April
        July
        October
        URL
        Schedule of Benefits

    - returning a dict
    """

    all_data = {}

    # driver = webdriver.Firefox()
    driver = webdriver.PhantomJS()
    driver.get(link)

    # grab plan name and carrier, add to dict
    try:
        plan_name = driver.find_element_by_tag_name('h2').text
        carrier = (driver.find_element_by_xpath(
            '//*[@id="secondary-wrapper"]/section/div/h3[1]').text)
        all_data['Plan Name'] = str(plan_name)
        all_data['Carrier'] = str(carrier.encode('utf-8'))

        # grab remaining data, add to dict
        plan_data = driver.find_elements_by_class_name('planData')
        all_data[str(plan_data[0].text)] = str(plan_data[1].text)    # year
        all_data[str(plan_data[2].text)] = str(plan_data[3].text)    # market
        all_data[str(plan_data[5].text)] = str(plan_data[6].text)    # metal
        all_data[str(plan_data[7].text)] = str(plan_data[8].text)    # exchange
        all_data[str(plan_data[10].text)] = str(plan_data[11].text)  # status
        all_data[str(plan_data[12].text)] = str(plan_data[13].text)  # county
        all_data[str(plan_data[14].text)] = str(plan_data[15].text)  # cost
        all_data[str(plan_data[16].text)] = str(plan_data[17].text)  # avg age
        all_data[str(plan_data[20].text)] = str(plan_data[21].text)  # january
        all_data[str(plan_data[22].text)] = str(plan_data[23].text)  # july
        all_data[str(plan_data[24].text)] = str(plan_data[25].text)  # april
        all_data[str(plan_data[26].text)] = str(plan_data[27].text)  # october

        # add pdf link to dict
        pdf_link = driver.find_element_by_xpath(
            '//*[@id="secondary-wrapper"]/section/div/a[1]')
        all_data["Schedule of Benefits"] = str(pdf_link.get_attribute('href'))

        # add url to dict
        all_data["URL"] = str(link)

        driver.quit()
        return all_data
    except Exception as e:
        print(e)
        log.exception("Error!")
        driver.quit()


def add_relevant_data_to_database(all_data_object):

    """
    Given the 'all_data' object, this function adds the data to the database.
    """

    con = sqlite3.connect(DATABASE)
    con.text_factory = str
    with con:
        cur = con.cursor()
        cur.execute(
            """
            INSERT INTO data(
                plan_name,
                carrier,
                metal,
                exchange,
                county,
                cost,
                status,
                plan_year,
                market_sement,
                january,
                april,
                july,
                october,
                url,
                benefit_schedule
            )
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                all_data_object['Plan Name'],
                all_data_object['Carrier'],
                all_data_object['Metal Tier:'],
                all_data_object['Exchange:'],
                all_data_object['County:'],
                all_data_object['Proposed:'],
                all_data_object['Rate Status:'],
                all_data_object['Plan Year:'],
                all_data_object['Market Segment:'],
                all_data_object['January:'],
                all_data_object['April:'],
                all_data_object['July:'],
                all_data_object['October:'],
                all_data_object['URL'],
                all_data_object['Schedule of Benefits'],
            )
        )


def timestamp_database():
    database_without_extension = os.path.splitext(DATABASE)[0]
    now = datetime.datetime.now()
    new_database_name = database_without_extension + '{0}.sqlite'.format(
        now.strftime("%Y-%m-%d_%H:%M"))
    os.rename(DATABASE, new_database_name)
    print("Done!")


def main():

    if CREATE_DATABASE:
        # create database
        create_database_and_tables()

        # grab links, add to database
        get_all_data()

    # get links from database, grab relevant data, and then add to database
    grab_links_from_database()

    # add timestamp once complete
    timestamp_database()

if __name__ == '__main__':
    main()
