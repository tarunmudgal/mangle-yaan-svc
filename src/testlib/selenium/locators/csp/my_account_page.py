from selenium.webdriver.common.by import By


class MyAccountLocators:
    BTN_CSP_USER = (By.CSS_SELECTOR, "#btn-csp-user")
    BTN_MY_ACCOUNT = (By.XPATH, "//span[contains(text(),'My Account')]")
    BTN_PREFERENCES_TAB = (By.XPATH, "//div[1]/user[1]/clr-tabs[1]/ul[1]/li[2]/button[1]")
    BTN_PREFERENCES_LANGUAGE_EDIT = (
        By.XPATH,
        "//body/csp-app[1]/clr-main-container[1]/div[1]/div[1]/div[1]/main[1]/div[1]/user[1]/user-preferences[1]/form[1]/vmw-form-section-container[1]/vmw-form-section[1]/div[1]/div[2]/div[1]/div[1]/button[1]",
    )
    DROP_DOWN_LANGUAGE = (By.CSS_SELECTOR, "#language")
    BTN_PREFERENCES_LANGUAGE_SAVE = (By.XPATH, "//span[contains(text(),'Save')]")
    TXT_MY_ACCOUNT_TITLE = (By.XPATH, "//h1[contains(text(),'My Account')]")
