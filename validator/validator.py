import os
import subprocess

from refiner.cov_extractor import check_coverage

def validate_driver(driver_file_path: str, compile_command: list) -> str:
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
    current_file_path = os.path.dirname(os.path.abspath(__file__))
    log_file_path = current_file_path + '/../outputs/temp/error_logs/raw_error_log.txt'
    dir_path = os.path.dirname(log_file_path)

    # 创建并初始化普通日志文件
    try:
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

    # Step 1: Check if the driver file exists and is not empty
    if not os.path.exists(driver_file_path):
        with open(log_file_path, 'a') as log_file:
            log_file.write(f"Driver file {driver_file_path} does not exist.\n")
        return "Compilation Error"

    if os.path.getsize(driver_file_path) == 0:
        with open(log_file_path, 'a') as log_file:
            log_file.write(f"Driver file {driver_file_path} is empty.\n")
        return "Compilation Error"

    # Step 2: Try to compile the driver code
    try:
        os.chdir(os.path.dirname(driver_file_path))
        subprocess.check_output(compile_command, stderr=subprocess.STDOUT)  # 将stderr合并到stdout中
    except subprocess.CalledProcessError as e:
        error_message = e.output.decode() if e.output else "No output captured"
        with open(log_file_path, 'a') as log_file:
            log_file.write(f"Compilation error for {driver_file_path}: {e}\n")
            log_file.write(f"Error details: {error_message}\n")
        return "Compilation Error"

    # Step 3: Try to run the driver code
    try:
        env = os.environ.copy()
        env["LLVM_PROFILE_FILE"] = "default.profraw"
        # 运行命令
        subprocess.check_call(['./driver', '-max_total_time=60'], env=env)
    except subprocess.CalledProcessError as e:
        with open(log_file_path, 'a') as log_file:
            log_file.write(f"Runtime error for {driver_file_path}: {e}\n")
        return "Runtime Error"

    # Step 4: Generate the coverage report using llvm-cov
    coverage_report_dir_path = current_file_path + '/../outputs/temp/coverage/'
    # 创建并初始化普通日志文件
    if not os.path.exists(coverage_report_dir_path):
        print(f"Directory {coverage_report_dir_path} does not exist. Creating...")
        os.makedirs(coverage_report_dir_path, exist_ok=True)  # 确保安全创建
    else:
        print(f"Directory {coverage_report_dir_path} already exists.")
    coverage_report_path = current_file_path + '/../outputs/temp/coverage/raw_coverage.txt'
    if not os.path.exists(coverage_report_path):
        with open(coverage_report_path, 'w'):  # 创建一个空文件
            pass

    try:
        with open(coverage_report_path, 'w') as report_file:
            subprocess.check_call([
                'llvm-profdata', 'merge', '-sparse', 'default.profraw', '-o', 'default.profdata'
            ], stdout=report_file)
            subprocess.check_call([
                'echo', '"Detailed report:\n"'
            ], stdout=report_file)
            subprocess.check_call([
                'llvm-cov','show', './driver',
                '-instr-profile=default.profdata',
            ], stdout=report_file)
            subprocess.check_call([
                'echo', '"Summary report:\n"'
            ], stdout=report_file)
            subprocess.check_call([
                'llvm-cov', 'report', './driver',
                '-instr-profile=default.profdata',
            ], stdout=report_file)
    except subprocess.CalledProcessError as e:
        with open(log_file_path, 'a') as log_file:
            log_file.write(f"Coverage report generation failed for {driver_file_path}: {e}\n")
        return "Coverage Generation Failed"

    # Step 5: Check if the coverage meets the required threshold
    try:
        coverage = check_coverage(coverage_report_path)
        if isinstance(coverage, str) and "Error" in coverage:
            with open(log_file_path, 'a') as log_file:
                log_file.write(f"Error extracting coverage for {driver_file_path}: {coverage}\n")
            return "Coverage Extraction Failed"

        if not coverage:
            with open(log_file_path, 'a') as log_file:
                log_file.write(f"Coverage is too low for {driver_file_path}: {coverage}%\n")
            return "Low Coverage"

    except Exception as e:
        with open(log_file_path, 'a') as log_file:
            log_file.write(f"Error while checking coverage for {driver_file_path}: {e}\n")
        return "Coverage Check Failed"

    return "Valid Driver"