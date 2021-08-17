from selenium.webdriver.common.by import By


class IdentityAndAccessLocators:
    BTN_IDENTITY_AND_ACCESS_MANAGEMENT = (By.XPATH, "//div/button/div")
    NAV_ACTIVE_USERS = (By.XPATH, "//span[contains(.,'Active Users')]")
    TXT_ACTIVE_USERS = (By.XPATH, "//h2[contains(text(),'Active Users')]")
    NAV_PENDING_INVITATIONS = (By.XPATH, "//a[contains(.,'Pending Invitations')]")
    NAV_GROUPS = (By.XPATH, "//span[contains(.,'Groups')]")
