from selenium.webdriver.common.by import By


class CommerceLocators:
    BTN_BILLING_AND_SUBSCRIPTIONS = (By.XPATH, "(//div[contains(.,'Billing & Subscriptions')])[4]")
    NAV_SUBSCRIPTIONS = (By.XPATH, "//span[contains(text(),'Subscriptions')]")
    TXT_SUBSCRIPTION = (
        By.XPATH,
        "//p[contains(text(),'VMware Cloud commerce Services is undergoing sched')]",
    )
