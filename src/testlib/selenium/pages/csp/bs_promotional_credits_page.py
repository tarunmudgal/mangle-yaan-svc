from src.testlib.selenium.locators.csp import bs_promotional_credits_page
from src.testlib.selenium.pages.csp.base_page import BasePage


class PromotionalCreditsPage(BasePage):
    def __init__(self, driver, timeout=30):
        self.current_url = driver.current_url
        self.commerce_credits_locators = bs_promotional_credits_page.CommercePromotionalCreditsLocators
        super().__init__(driver, self.current_url, timeout=timeout)

    def goto_promotional_credits_page(self):        
        promotional_credits_page_link = self.find_element(self.commerce_credits_locators.NAV_CREDITS)
        if promotional_credits_page_link:
            promotional_credits_page_link.click()
            self.wait_for_element(self.commerce_credits_locators.TXT_CREDITS)
            assert self.find_element(self.commerce_credits_locators.TXT_CREDITS).text == "Promotional Credits", "Promotional Credits page is not working as expected"
            
        else:
            mylog.error(
                "Subscription page could not be located using locator={}".format(
                    self.commerce_locators.NAV_SUBSCRIPTIONS
                )
            )
