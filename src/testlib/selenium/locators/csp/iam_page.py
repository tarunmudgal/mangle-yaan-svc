
from selenium.webdriver.common.by import By

class IdentityAndAccessLocators:
    IAM = (By.XPATH, "//div/button/div")
    Active_users = (By.XPATH, "//span[contains(.,'Active Users')]")
    Active_users_text = (By.XPATH, "//h2[contains(text(),'Active Users')]")
    Invitations = (By.XPATH, "//a[contains(.,'Pending Invitations')]")
    groups = (By.XPATH, "//span[contains(.,'Groups')]") 

