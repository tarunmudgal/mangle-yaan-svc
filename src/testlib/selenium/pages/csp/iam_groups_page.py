from src.testlib.selenium.locators.csp import iam_groups_page
from src.testlib.selenium.pages.csp.base_page import BasePage


class GroupsPage(BasePage):
    def __init__(self, driver, timeout=30):
        self.current_url = driver.current_url
        self.iam_group_locators = iam_groups_page.IdentityAndAccessGroupsLocators
        super().__init__(driver, self.current_url, timeout=timeout)

    def goto_groups_page(self):
        groups_page_link = self.find_element(self.iam_group_locators.NAV_GROUPS)
        if groups_page_link:
            groups_page_link.click()
            self.wait_for_element(self.iam_group_locators.TXT_GROUPS)
            assert self.find_element(self.iam_group_locators.TXT_GROUPS).text == "Groups", "Groups page is not working as expected"
            assert self.if_element_exists(
                self.iam_group_locators.NAV_GROUPS_SEARCH
            ), "could not find Groups search locator={}".format(self.iam_group_locators.NAV_GROUPS_SEARCH)
            
            assert self.if_element_exists(
                self.iam_group_locators.BTN_ADD_GROUPS
            ), "could not find add groups locator={}".format(self.iam_group_locators.BTN_ADD_GROUPS)

        else:
            mylog.error(
                "Groups page could not be located using locator={}".format(
                    self.iam_group_locators.NAV_GROUPS
                )
            )
