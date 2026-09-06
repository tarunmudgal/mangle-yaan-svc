# UI Automation Architecture

While MangleYaan is primarily an API and backend-focused chaos testing tool, some resiliency validations require confirming that the end-user interface remains functional during a fault. To achieve this, the framework utilizes **Selenium WebDriver**, structured using the **Page Object Model (POM)** pattern.

The UI automation components are housed in `src/testlib/selenium/`.

## The Page Object Model (POM)

POM is a design pattern that creates an object repository for web UI elements. Under this model, for each web page in the application, there is a corresponding Page Class. 

This approach prevents code duplication and makes tests highly readable and maintainable.

### 1. Locators (`src/testlib/selenium/locators/`)
Locators are constants that define how to find specific elements on the DOM (e.g., by ID, XPath, CSS Selector).
- **Why separate them?** If the UI changes and a button's ID changes, you only need to update the locator in one place, rather than in every test that clicks that button.

### 2. Elements (`src/testlib/selenium/elements/`)
Elements represent the actual interactions with the localized web components (e.g., clicking, typing text).
- These classes wrap the basic Selenium `find_element` calls and add robustness (like explicit waits to ensure an element is clickable before attempting interaction).

### 3. Pages (`src/testlib/selenium/pages/`)
Pages combine Locators and Elements to represent a complete view (like a Login Page or a Dashboard).
- A Page class contains high-level business logic methods. For example, a `LoginPage` class would have a method `login(username, password)` which internally calls the elements to type the credentials and click the submit button.

By structuring UI tests this way, the main test logic in MangleYaan remains extremely clean, simply invoking methods like `dashboard.verify_service_healthy()` while a chaos fault is actively running.
