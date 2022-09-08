from selenium.webdriver.common.by import By


class CommerceSubscriptionLocators:
    NAV_SUBSCRIPTIONS = (By.XPATH, "//span[contains(.,'Subscriptions')]")
    TXT_SUBSCRIPTIONS = (By.XPATH, "//h2[contains(.,'Subscriptions')]")
    BTN_BACK_TO_HOME_PAGE = (
        By.XPATH,
        "//button[contains(.,'Back to VMware cloud services')]",
    )
    TXT_ERROR = (By.XPATH, "//div[@class='error-code'][contains(.,'503 ERROR')]")
    TXT_ERROR_MSG = (
        By.XPATH,
        "//p[contains(.,'VMware Cloud commerce Services is undergoing scheduled maintenance right now.')]",
    )
