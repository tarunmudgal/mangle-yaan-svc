from selenium.webdriver.common.by import By


class CommerceInvoicesLocators:
    NAV_INVOICES = (By.XPATH, "//span[contains(.,'Invoices & Statements')]")
    TXT_INVOICES = (By.XPATH, "//h2[contains(.,'Invoices & Statements')]")
    BTN_INVOICES = (By.XPATH, "//button[contains(.,'Invoices')]")
    BTN_STATEMENTS = (By.XPATH, "//button[contains(.,'Activity Statements')]")
    TXT_ERROR = (By.XPATH, "//div[contains(text(),'503 ERROR')]")
    TXT_ERROR_MSG = (
        By.XPATH,
        "(//div[contains(.,'company Cloud commerce Services is undergoing scheduled maintenance right now.')])[6]",
    )
    BTN_BACK_TO_HOME_PAGE = (
        By.XPATH,
        "//button[contains(text(),'Back to company cloud services')]",
    )
