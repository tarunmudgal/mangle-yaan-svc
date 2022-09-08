from selenium.webdriver.common.by import By


class IAMGroupsLocators:
    BTN_IDENTITY_AND_ACCESS_MANAGEMENT = (By.XPATH, "//div/button/div")
    NAV_GROUPS = (By.XPATH, "//span[@class='nav-text'][contains(.,'Groups')]")
    TXT_GROUPS = (By.XPATH, "//h2[contains(.,'Groups')]")
    NAV_GROUPS_SEARCH = (By.XPATH, "//input[contains(@data-test-id,'search-input')]")
    BTN_ADD_GROUPS = (By.XPATH, "//button[@data-test-id='add-groups'][contains(.,'Add Groups')]")
