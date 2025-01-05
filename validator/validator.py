# Validate the input driver. If the driver is valid, return True; otherwise, report the error and return False.
import os
import subprocess
import logging

from refiner.cov_extractor import check_coverage

def validate_driver(driver_file_name: str) -> str:
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
    log_file_path = '../outputs/temp/error_logs/raw_error_log.txt'
    driver_file_path = f'../outputs/temp/candidate_fuzz_drivers/{driver_file_name}'
    dir_path = os.path.dirname(log_file_path)
    try:
        # 确保目录存在
        if not os.path.exists(dir_path):
            print(f"Directory {dir_path} does not exist. Creating...")
            os.makedirs(dir_path, exist_ok=True)  # 确保安全创建
        else:
            print(f"Directory {dir_path} already exists.")

        # 确保能够创建文件
        with open(log_file_path, 'w') as file:
            file.write("")
            print(f"File {log_file_path} created and initialized.")

    except Exception as e:
        print(f"An error occurred: {e}")

    # Configure the logger
    logging.basicConfig(filename='your_log_file.log', level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

    # Step 1: Check if the driver file exists and is not empty
    if not os.path.exists(driver_file_path):
        raise FileNotFoundError(f"Driver file {driver_file_path} does not exist.")
    if os.path.getsize(driver_file_path) == 0:
        raise ValueError(f"Driver file {driver_file_path} is empty.")

    # Step 2: Try to compile the driver code
    compile_command = [
        "clang", "-g", "-fsanitize=fuzzer", "-fsanitize=address", "-std=c11", "-fprofile-instr-generate",
        "-fcoverage-mapping",
        "-o", "fuzz_driver", driver_file_path, "-I/usr/include/libxml2", "-L/usr/lib/x86_64-linux-gnu", "-lxml2"
    ]
    try:
        subprocess.check_output(compile_command, stderr=subprocess.STDOUT)  # 将stderr合并到stdout中
    except subprocess.CalledProcessError as e:
        error_message = e.output.decode() if e.output else "No output captured"
        logging.error(f"Compilation error for {driver_file_path}: {e}")
        logging.error(f"Error details: {error_message}")
        return "Compilation Error"

    # Step 3: Try to run the driver code
    try:
        subprocess.check_call(["./driver"])
    except subprocess.CalledProcessError as e:
        logging.error(f"Runtime error for {driver_file_path}: {e}")
        return "Runtime Error"

    # Step 4: Generate the coverage report using llvm-cov
    coverage_report_path = 'outputs/temp/coverage/raw_coverage.txt'
    if not os.path.exists(coverage_report_path):
        with open(coverage_report_path, 'w'):  # 创建一个空文件
            pass

    try:
        with open(coverage_report_path, 'w') as report_file:
            subprocess.check_call([
                'llvm-cov', 'report', './fuzz_driver',
                '-instr-profile=default.profdata'
            ], stdout=report_file)
    except subprocess.CalledProcessError as e:
        logging.error(f"Coverage report generation failed for {driver_file_path}: {e}")
        return "Coverage Generation Failed"

    # Step 5: Check if the coverage meets the required threshold
    try:
        coverage = check_coverage(coverage_report_path)
        if isinstance(coverage, str) and "Error" in coverage:
            logging.error(f"Error extracting coverage for {driver_file_path}: {coverage}")
            return "Coverage Extraction Failed"

        if not coverage:
            logging.error(f"Coverage is too low for {driver_file_path}: {coverage}%")
            return "Low Coverage"

    except Exception as e:
        logging.error(f"Error while checking coverage for {driver_file_path}: {e}")
        return "Coverage Check Failed"

    return "Valid Driver"