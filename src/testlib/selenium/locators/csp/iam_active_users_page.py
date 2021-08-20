from selenium.webdriver.common.by import By


class IAMActiveUsersLocators:
    BTN_IDENTITY_AND_ACCESS_MANAGEMENT = (By.XPATH, "//div/button/div")
    NAV_ACTIVE_USERS = (By.XPATH, "//span[contains(.,'Active Users')]")
    NAV_ACTIVE_USERS_SEARCH = (By.XPATH, "//input[contains(@data-test-id,'search-input')]")
    BTN_ADD_USER = (By.XPATH, "//span[contains(.,'Add Users')]")
    TXT_ACTIVE_USERS = (By.XPATH, "//h2[contains(text(),'Active Users')]")
