from selenium.webdriver.common.by import By


class CommercePaymentLocators:
    NAV_PAYMENTS = (By.XPATH, "//span[contains(.,'Manage Payment Methods')]")
    TXT_PAYMENTS = (By.XPATH, "//h2[contains(.,'Manage Payment Methods')]")
    TXT_ERROR = (By.XPATH, "//div[@class='error-code'][contains(.,'503 ERROR')]")
    TXT_ERROR_MSG = (
        By.XPATH,
        "//p[@class='message'][contains(.,'VMware Cloud commerce Services is undergoing scheduled maintenance right now.')]",
    )
    BTN_BACK_TO_HOME_PAGE = (
        By.XPATH,
        "//button[contains(.,'Back to VMware cloud services')]",
    )
