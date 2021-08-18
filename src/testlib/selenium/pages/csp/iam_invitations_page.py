from src.testlib.selenium.locators.csp import iam_invitations_page
from src.testlib.selenium.pages.csp.base_page import BasePage


class InvitationsPage(BasePage):
    def __init__(self, driver, timeout=30):
        self.current_url = driver.current_url
        self.iam_invitations_locators = iam_invitations_page.IdentityAndAccessInvitationsLocators
        super().__init__(driver, self.current_url, timeout=timeout)

    def goto_invitations_page(self):
        groups_page_link = self.find_element(self.iam_invitations_locators.NAV_PENDING_INVITATIONS)
        if groups_page_link:
            groups_page_link.click()
            self.wait_for_element(self.iam_invitations_locators.TXT_PENDING_INVITATIONS)
            assert self.find_element(self.iam_invitations_locators.TXT_PENDING_INVITATIONS).text == "Pending Invitations", "Pending Invitations page is not working as expected"
            
            # assert self.if_element_exists(
            #     self.iam_invitations_locators.BTN_SEND_INVITATION
            # ), "could not find add a user locator={}".format(self.iam_invitations_locators.BTN_SEND_INVITATION)

        else:
            mylog.error(
                "Groups page could not be located using locator={}".format(
                    self.iam_invitations_locators.NAV_PENDING_INVITATIONS
                )
            )
