from selenium.webdriver.common.by import By


class CommerceOverviewLocators:
    BTN_BILLING_AND_SUBSCRIPTIONS = (By.XPATH, "(//div[contains(.,'Billing & Subscriptions')])[4]")
    NAV_OVERVIEW = (By.XPATH, "(//span[contains(.,'Overview')])[1]")
    TXT_OVERVIEW = (By.XPATH, "//h2[contains(.,'Overview')]")
    TXT_ERROR = (By.XPATH, "//div[@class='error-code'][contains(.,'503 ERROR')]")
    TXT_ERROR_MSG = (
        By.XPATH,
        "//p[@class='message'][contains(.,'VMware Cloud commerce Services is undergoing scheduled maintenance right now.')]",
    )
    BTN_BACK_TO_HOME_PAGE = (
        By.XPATH,
        "//button[contains(.,'Back to VMware cloud services')]",
    )
