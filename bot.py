import sqlite3
from selenium import webdriver


###########
# Globals #
###########

YEAR = '2014'             # update me
TYPE = 'Individual HSA'   # update me
DATABASE = 'data.sqlite'  # update me

STARTING_URL = 'http://healthrates.doi.nv.gov/Wizard.aspx?type=Small%20Group'


########
# Code #
########

def create_database_and_tables():
    con = sqlite3.connect(DATABASE)
    with con:
        cur = con.cursor()
        try:
            cur.execute(
                """
                CREATE TABLE links(
                    id INTEGER PRIMARY KEY, url TEXT)
                """
            )
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

    # perform search
    driver.find_element_by_xpath(
        "//select[@name='type']/option[text()='"+TYPE+"']").click()
    driver.find_element_by_xpath(
        "//select[@name='planyear']/option[text()='"+YEAR+"']").click()
    driver.find_element_by_tag_name('form').submit()

    # find all links and add each to the DB
    first_element = driver.find_element_by_xpath(
        '//*[@id="resultsBox"]/div[5]')
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
    con = sqlite3.connect(DATABASE)
    with con:
        cur = con.cursor()
        cur.execute(
            """
            INSERT INTO links(url) VALUES(?)
            """, (single_link,)
        )


def grab_links_from_database():
    """
    Grab all data from the links table.
    """
    con = sqlite3.connect(DATABASE)
    with con:
        cur = con.cursor()
        cur.execute('SELECT * FROM links WHERE id')
        all_database_rows = len(cur.fetchall())
        cur.execute('SELECT * FROM links WHERE id')
        starting_row_id = int(cur.fetchone()[0])
        for x in range(starting_row_id, all_database_rows+1):
            cur.execute('SELECT * FROM links WHERE id=?', (x,))
            link = cur.fetchone()
            data_object = get_relevant_data(link[1])
            if data_object:
                add_relevant_data_to_database(data_object)


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

    - returning a list of dicts
    """

    all_data = {}

    driver = webdriver.Firefox()
    driver.get(link)

    # grab plan name and carrier, add to dict
    try:
        plan_name = driver.find_element_by_tag_name('h2').text
        carrier = driver.find_element_by_xpath(
            '//*[@id="secondary-wrapper"]/section/div/h3[1]').text
        all_data['Plan Name'] = str(plan_name)
        all_data['Carrier'] = str(carrier)

        # grab remaining data, add to dict
        plan_data = driver.find_elements_by_class_name('planData')
        all_data[str(plan_data[0].text)] = str(plan_data[1].text)    # plan year
        all_data[str(plan_data[2].text)] = str(plan_data[3].text)    # market seg
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
    except:
        driver.quit()
        pass


def add_relevant_data_to_database(all_data_object):
    """
    Given the 'all_data' object, this function adds the data to the database.
    """
    print all_data_object
    con = sqlite3.connect(DATABASE)
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


def main():

    # create databases
    create_database_and_tables()

    # grab links, add to database
    get_all_data()

    # get links from database, grab relevant data, and then add to database
    grab_links_from_database()

if __name__ == '__main__':
    main()
