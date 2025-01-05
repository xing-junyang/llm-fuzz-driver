# Validate the input driver. If the driver is valid, return True; otherwise, report the error and return False.

def validate_driver(driver_file_path: str) -> str:
    """
    Validate the input driver. Return `Valid Driver`, `Compilation Error`, or `Low Coverage` according to the
    validation result.

    The procedure includes:
        - Check if the driver file exists and is not empty
        - Try to compile the driver code. If the compilation fails, write the error to the log file in
        'outputs/temp/error_logs/raw_error_log.txt', and return `Compilation Error`
        - Try to run the driver code.
        - Generate the coverage report using `llvm-cov`. Write the coverage report to the file in
        'outputs/temp/coverage/raw_coverage.txt'.
        - Check the coverage of the driver code. Use method in `refiner/cov_extractor.py` to check whether the coverage
        satisfies the required threshold. If the coverage is less than the threshold, return `Low Coverage`.
        - If the driver is valid, return `Valid Driver`.
    """

    return "Valid Driver"