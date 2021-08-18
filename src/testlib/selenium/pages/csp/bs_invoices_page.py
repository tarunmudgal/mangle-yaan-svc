from src.testlib.selenium.locators.csp import bs_invoices_page
from src.testlib.selenium.pages.csp.base_page import BasePage


class InvoicesPage(BasePage):
    def __init__(self, driver, timeout=30):
        self.current_url = driver.current_url
        self.commerce_invoice_locators = bs_invoices_page.CommerceInvoicesLocators
        super().__init__(driver, self.current_url, timeout=timeout)

    def goto_invoices_page(self):        
        invoices_page_link = self.find_element(self.commerce_invoice_locators.NAV_INVOICES)
        if invoices_page_link:
            invoices_page_link.click()
            assert self.if_element_exists(
                self.commerce_invoice_locators.TXT_ERROR
            ), "could not find 503 error locator={}".format(self.commerce_invoice_locators.TXT_ERROR)
            assert self.if_element_exists(
                self.commerce_invoice_locators.TXT_ERROR_MSG
            ), "could not find error msg locator={}".format(self.commerce_invoice_locators.TXT_ERROR_MSG)
            assert self.if_element_exists(
                self.commerce_invoice_locators.BTN_BACK_TO_HOME_PAGE
            ), "could not find Back to Vmware cloud services locator={}".format(self.commerce_invoice_locators.BTN_BACK_TO_HOME_PAGE)
            
        else:
            mylog.error(
                "Invoices & Statements page could not be located using locator={}".format(
                    self.commerce_invoice_locators.NAV_INVOICES
                )
            )

        return None
