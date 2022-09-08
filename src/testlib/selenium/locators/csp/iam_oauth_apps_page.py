from selenium.webdriver.common.by import By


class IAMOauthAppsLocators:
    NAV_OAUTH_APPS = (By.XPATH, "(//span[contains(.,'OAuth Apps')])[1]")
    TXT_OAUTH_APPS = (By.XPATH, "//h2[contains(.,'OAuth Apps')]")
    BTN_ADD_APP = (By.XPATH, "//button[contains(.,'Add App')]")
