from selenium.webdriver.common.by import By


class CommercePaymentLocators:
    NAV_PAYMENTS = (By.XPATH, "//span[contains(text(),'Manage Payment Methods')]")
    TXT_PAYMENTS = (By.XPATH, "//h2[contains(text(),'Manage Payment Methods')]")
    TXT_ERROR = (By.XPATH, "//div[contains(text(),'503 ERROR')]")
    TXT_ERROR_MSG = (
        By.XPATH,
        "//p[contains(text(),'VMware Cloud commerce Services is undergoing sched')]",
    )
    BTN_BACK_TO_HOME_PAGE = (
        By.XPATH,
        "//button[contains(text(),'Back to VMware cloud services')]",
    )
