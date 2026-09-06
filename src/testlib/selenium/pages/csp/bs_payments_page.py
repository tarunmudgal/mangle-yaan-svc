from src.testlib.selenium.locators.csp import bs_payments_page
from src.testlib.selenium.pages.csp.base_page import BasePage


class PaymentsPage(BasePage):
    def __init__(self, driver, timeout=30):
        self.current_url = driver.current_url
        self.commerce_payments_locators = bs_payments_page.CommercePaymentLocators
        super().__init__(driver, self.current_url, timeout=timeout)

    def verify_503_error_when_commerce_down(self):
        assert self.if_element_exists(
            self.commerce_payments_locators.TXT_ERROR
        ), "could not find 503 error locator={}".format(self.commerce_payments_locators.TXT_ERROR)
        assert self.if_element_exists(
            self.commerce_payments_locators.TXT_ERROR_MSG
        ), "could not find error msg locator={}".format(
            self.commerce_payments_locators.TXT_ERROR_MSG
        )
        assert self.if_element_exists(
            self.commerce_payments_locators.BTN_BACK_TO_HOME_PAGE
        ), "could not find Back to company cloud services locator={}".format(
            self.commerce_payments_locators.BTN_BACK_TO_HOME_PAGE
        )

    def goto_payments_page(self):
        payments_page_link = self.find_element(self.commerce_payments_locators.NAV_PAYMENTS)
        if payments_page_link:
            payments_page_link.click()
            self.wait_for_element(self.commerce_payments_locators.TXT_PAYMENTS)
            assert (
                self.find_element(self.commerce_payments_locators.TXT_PAYMENTS).text
                == "Manage Payment Methods"
            ), "Manage Payment Methods page is not working as expected"
            self.verify_503_error_when_commerce_down()
        else:
            mylog.error(
                "Manage Payment Methods page could not be located using locator={}".format(
                    self.commerce_payments_locators.NAV_PAYMENTS
                )
            )
