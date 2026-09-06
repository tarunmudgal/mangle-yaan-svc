# Results Reporting

Effective chaos engineering relies heavily on visibility and historical trends. MangleYaan utilizes a combination of **Allure Reports** and **AWS S3** to provide robust result reporting.

## Allure Reports

The framework integrates with `pytest` plugins (specifically Allure) to generate rich, interactive HTML reports.

- **Granular Details**: Allure captures step-by-step test execution, showing exactly when a fault was injected, when the system was validated, and any logs or screenshots captured during the process.
- **Trend Generation**: Allure natively supports tracking historical trends. By fetching the previous run's data before generating the current report, the framework visualizes pass/fail trends over time directly in the HTML output.

## AWS S3 Upload & MaximGun Updates

The heavy lifting of report distribution is handled at the end of the `test_runner.py` execution block, utilizing the `S3Client` (`lib/aws/s3.py`).

1. **Test Completion**: Once `pytest` finishes executing the resiliency suites, the framework generates the final Allure HTML directory.
2. **Trend Sync**: The framework downloads previous trend data from the designated S3 bucket, merges it with the current run, and generates the new report.
3. **Upload to S3**: The final HTML report and logs are uploaded to an AWS S3 bucket (`upload_files_to_s3` method) configured via `my.json`. This makes the report accessible via a static URL.
4. **MaximGun Notification**: Finally, the MangleYaan agent uses the `MGClient` to notify MaximGun that the task is `COMPLETED`. It passes the generated S3 report URL back to MaximGun, ensuring that the orchestrator UI always links to the latest execution results.
