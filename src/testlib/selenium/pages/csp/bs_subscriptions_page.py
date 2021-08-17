from src.testlib.selenium.locators.csp import bs_subscriptions_page
from src.testlib.selenium.pages.csp.base_page import BasePage


class SubscriptionsPage(BasePage):
    def __init__(self, driver, timeout=30):
        self.current_url = driver.current_url
        self.commerce_locators = bs_subscriptions_page.CommerceLocators
        super().__init__(driver, self.current_url, timeout=timeout)

    def goto_subscriptions_page(self):
        billing_subscriptions_btn = self.find_element(
            self.commerce_locators.BTN_BILLING_AND_SUBSCRIPTIONS
        )
        if billing_subscriptions_btn:
            billing_subscriptions_btn.click()
            subscriptions_page_link = self.find_element(self.commerce_locators.NAV_SUBSCRIPTIONS)
            if subscriptions_page_link:
                subscriptions_page_link.click()
                self.wait_for_element(self.commerce_locators.TXT_SUBSCRIPTION)
                error_msg = self.find_element(self.commerce_locators.TXT_SUBSCRIPTION).text
                return error_msg
            else:
                mylog.error(
                    "Subscription page could not be located using locator={}".format(
                        self.commerce_locators.NAV_SUBSCRIPTIONS
                    )
                )

        return None
