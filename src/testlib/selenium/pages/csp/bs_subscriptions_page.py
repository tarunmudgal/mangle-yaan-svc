from src.testlib.selenium.locators.csp import bs_subscriptions_page
from src.testlib.selenium.pages.csp.base_page import BasePage


class SubscriptionsPage(BasePage):
    def __init__(self, driver, timeout=30):
        self.current_url = driver.current_url
        self.commerce_sub_locators = bs_subscriptions_page.CommerceSubscriptionLocators
        super().__init__(driver, self.current_url, timeout=timeout)

    def goto_subscriptions_page(self):        
        subscriptions_page_link = self.find_element(self.commerce_sub_locators.NAV_SUBSCRIPTIONS)
        if subscriptions_page_link:
            subscriptions_page_link.click()
            self.wait_for_element(self.commerce_sub_locators.TXT_SUBSCRIPTIONS)
            assert self.find_element(self.commerce_sub_locators.TXT_SUBSCRIPTIONS).text == "Subscriptions", "Subscriptions page is not working as expected"
            assert self.if_element_exists(
                self.commerce_sub_locators.TXT_ERROR
            ), "could not find 503 error locator={}".format(self.commerce_sub_locators.TXT_ERROR)
            assert self.if_element_exists(
                self.commerce_sub_locators.TXT_ERROR_MSG
            ), "could not find error msg locator={}".format(self.commerce_sub_locators.TXT_ERROR_MSG)
            assert self.if_element_exists(
                self.commerce_sub_locators.BTN_BACK_TO_HOME_PAGE
            ), "could not find Back to Vmware cloud services locator={}".format(self.commerce_sub_locators.BTN_BACK_TO_HOME_PAGE)
            
        else:
            mylog.error(
                "Subscription page could not be located using locator={}".format(
                    self.commerce_sub_locators.NAV_SUBSCRIPTIONS
                )
            )

        return None
