
from selenium.webdriver.common.by import By

class IdentityAndAccessLocators:
    IAM = (By.CSS_SELECTOR, "css=.ng-tns-c160-4 > .nav-group-text")
    Active_users = (By.XPATH, "//span[contains(.,'Active Users')]")
    Invitations = (By.XPATH, "//a[contains(.,'Pending Invitations')]")
    groups = (By.XPATH, "//span[contains(.,'Groups')]") 

