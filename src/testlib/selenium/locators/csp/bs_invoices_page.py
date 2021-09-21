from selenium.webdriver.common.by import By


class CommerceInvoicesLocators:
    NAV_INVOICES = (By.XPATH, "//span[contains(text(),'Invoices & Statements')]")
    TXT_INVOICES = (By.XPATH, "//h2[contains(text(),'Invoices & Statements')]")
    BTN_INVOICES = (By.XPATH, "//button[@id='clr-tab-link-7']")
    BTN_STATEMENTS = (By.XPATH, "//button[@id='clr-tab-link-6']")
    TXT_ERROR = (By.XPATH, "//div[contains(text(),'503 ERROR')]")
    TXT_ERROR_MSG = (
        By.XPATH,
        "//p[contains(text(),'VMware Cloud commerce Services is undergoing sched')]",
    )
    BTN_BACK_TO_HOME_PAGE = (
        By.XPATH,
        "//button[contains(text(),'Back to VMware cloud services')]",
    )
