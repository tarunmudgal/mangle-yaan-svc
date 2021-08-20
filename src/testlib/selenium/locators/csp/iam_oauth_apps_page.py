from selenium.webdriver.common.by import By


class IAMOauthAppsLocators:
    NAV_OAUTH_APPS = (By.XPATH, "//span[contains(text(),'OAuth Apps')]")
    TXT_OAUTH_APPS = (By.XPATH, "//h2[contains(text(),'OAuth Apps')]")
    BTN_ADD_APP = (By.XPATH, "//button[contains(text(),'Add App')]")

