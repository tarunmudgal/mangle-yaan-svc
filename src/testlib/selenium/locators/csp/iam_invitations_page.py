from selenium.webdriver.common.by import By


class IAMInvitationsLocators:
    NAV_PENDING_INVITATIONS = (By.XPATH, "//span[contains(text(),'Pending Invitations')]")
    BTN_SEND_INVITATION = (By.XPATH, "//button[contains(text(),'Add a user')]")
    TXT_PENDING_INVITATIONS = (By.XPATH, "//h2[contains(text(),'Pending Invitations')]")
