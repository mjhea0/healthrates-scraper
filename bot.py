from selenium import webdriver


###############
### Globals ###
###############


DATABASE_NAME = 'links.db'
DATABASE2_NAME = 'data.db'
STARTING_URL = 'http://healthrates.doi.nv.gov/Wizard.aspx?type=Small%20Group'


############
### Code ###
############


def get_all_data():
    driver = webdriver.Firefox()
    driver.get(STARTING_URL)
    driver.find_element_by_class_name('rates_review_button_submit').click()
    driver.find_element_by_tag_name('form').submit()
    driver.quit()


def main():

    get_all_data()


if __name__ == '__main__':
    main()
