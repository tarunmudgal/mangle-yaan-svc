from selenium.webdriver.common.by import By


class CommerceOverviewLocators:
    BTN_BILLING_AND_SUBSCRIPTIONS = (By.XPATH, "(//div[contains(.,'Billing & Subscriptions')])[4]")
    NAV_OVERVIEW = (By.XPATH, "//span[contains(text(),'Overview')]")
    TXT_OVERVIEW = (By.XPATH, "//h2[contains(text(),'Overview')]")
    TXT_ERROR = (By.XPATH, "//div[contains(text(),'503 ERROR')]")
    TXT_ERROR_MSG = (
        By.XPATH,
        "//p[contains(text(),'VMware Cloud commerce Services is undergoing sched')]",
    )
    BTN_BACK_TO_HOME_PAGE = (
        By.XPATH,
        "//button[contains(text(),'Back to VMware cloud services')]",
    )
