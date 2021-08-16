
from src.testlib.selenium.locators.csp import commerce_page
from src.testlib.selenium.pages.csp.base_page import BasePage


class BillingAndSubscriptionsPage(BasePage):
    def __init__(self, driver, timeout=30):
        self.current_url = driver.current_url
        self.commerce_locators = commerce_page.CommerceLocators
        super().__init__(driver, self.current_url, timeout=timeout)

    def goto_subscriptions_page(self):
        billingpage_element = self.find_element(self.commerce_locators.BillingAndSubscriptions)
        if billingpage_element:
            billingpage_element.click()
            subscription_element = self.find_element(self.commerce_locators.Subscriptions)
            if subscription_element:
                subscription_element.click()
                error_msg = self.find_element(self.commerce_locators.Subscription_text).text
                return error_msg
            else:
                print("Subscription element not found")
        
        return None



    