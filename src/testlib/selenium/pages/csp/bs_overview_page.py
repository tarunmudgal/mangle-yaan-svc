from src.testlib.selenium.locators.csp import bs_overview_page
from src.testlib.selenium.pages.csp.base_page import BasePage


class OverviewPage(BasePage):
    def __init__(self, driver, timeout=30):
        self.current_url = driver.current_url
        self.commerce_overview_locators = bs_overview_page.CommerceOverviewLocators
        super().__init__(driver, self.current_url, timeout=timeout)

    def verify_503_error_when_commerce_down(self):
        assert self.if_element_exists(
            self.commerce_overview_locators.TXT_ERROR
        ), "could not find 503 error locator={}".format(self.commerce_overview_locators.TXT_ERROR)
        assert self.if_element_exists(
            self.commerce_overview_locators.TXT_ERROR_MSG
        ), "could not find error msg locator={}".format(
            self.commerce_overview_locators.TXT_ERROR_MSG
        )
        assert self.if_element_exists(
            self.commerce_overview_locators.BTN_BACK_TO_HOME_PAGE
        ), "could not find Back to company cloud services locator={}".format(
            self.commerce_overview_locators.BTN_BACK_TO_HOME_PAGE
        )

    def goto_overview_page(self):
        billing_subscriptions_btn = self.find_element(
            self.commerce_overview_locators.BTN_BILLING_AND_SUBSCRIPTIONS
        )
        if billing_subscriptions_btn:
            billing_subscriptions_btn.click()
            overview_page_link = self.find_element(self.commerce_overview_locators.NAV_OVERVIEW)
            if overview_page_link:
                overview_page_link.click()
                self.wait_for_element(self.commerce_overview_locators.TXT_OVERVIEW)
                assert (
                    self.find_element(self.commerce_overview_locators.TXT_OVERVIEW).text
                    == "Overview"
                ), "Overview page is not working as expected"

                self.verify_503_error_when_commerce_down()

            else:
                mylog.error(
                    "Overview page could not be located using locator={}".format(
                        self.commerce_overview_locators.NAV_OVERVIEW
                    )
                )
