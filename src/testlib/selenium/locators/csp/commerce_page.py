
from selenium.webdriver.common.by import By

class CommerceLocators:
    BillingAndSubscriptions = (By.XPATH, "(//div[contains(.,'Billing & Subscriptions')])[4]")
    Subscriptions = (By.XPATH, "//span[contains(text(),'Subscriptions')]")
    Subscription_text = (By.XPATH, "//p[contains(text(),'VMware Cloud commerce Services is undergoing sched')]")