from selenium.webdriver.common.by import By


class CommerceSubscriptionLocators:
    NAV_SUBSCRIPTIONS = (By.XPATH, "//span[contains(text(),'Subscriptions')]")
    TXT_SUBSCRIPTIONS = (By.XPATH, "//h2[contains(text(),'Subscriptions')]")
    BTN_BACK_TO_HOME_PAGE = (
        By.XPATH,
        "//button[contains(text(),'Back to VMware cloud services')]",
    )
    TXT_ERROR = (By.XPATH, "//div[contains(text(),'503 ERROR')]")
    TXT_ERROR_MSG = (
        By.XPATH,
        "//p[contains(text(),'VMware Cloud commerce Services is undergoing sched')]",
    )
