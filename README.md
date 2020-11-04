#MangleYaan 

This is a test framework developed to run resiliency test cases for VMWare CSP product. 

CLI to run mangle-yaan using command line:
python test_runner.py tests/test_commerce_when_am_service_unavailable.py --html=report.html --self-contained-html


# References:

## pytest reporting
https://pypi.org/project/pytest-html/
https://github.com/tarunmudgal/pytest-html-reporter/tree/master/pytest_html_reporter
https://blog.testproject.io/2020/07/15/getting-started-with-testproject-python-sdk/

# ModuleCode.java formatting to module_code.json using https://sed.js.org
--regexp-extended 's/\s*(.*?)\((.*?), (.*?), (.*?)\)/"\2": \{"name": \3, "type": "\1", "path": \4\}/'

# CspCommonErrors.java formatting to csp_common_errors.json using https://sed.js.org
--regexp-extended 's/public static final CspError (.*?) = new CspError\((.*?), (.*?)\).*/"\2": "\1",/'
