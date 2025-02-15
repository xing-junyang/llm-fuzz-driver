import subprocess
import logging
import os

# Ensure the directory exists
os.makedirs('../outputs/temp/cov_log', exist_ok=True)

# Configure logging
logging.basicConfig(filename='../outputs/temp/cov_log/coverage.log', level=logging.INFO, format='%(asctime)s - %(message)s')
def check_coverage(file_path: str) -> bool:
    """
    Check whether the given coverage data satisfies the required threshold.
    .profdata file is used to store the coverage data.
    """
    coverage_percentage = extract_coverage_percentage(file_path)
    required_threshold = 80.0  # Example threshold
    return float(coverage_percentage) >= required_threshold

def extract_coverage_percentage(file_path: str) -> float | str:
    """
    Extract the coverage percentage from the given coverage report, and return it.
    """
    try:
        # Generate the coverage report using llvm-cov
        # llvm_cov_command = [
        #     'llvm-cov', 'report', 'fuzz_driver', '-instr-profile', file_path
        # ]
        # result = subprocess.run(llvm_cov_command, capture_output=True, text=True, check=True)

        with open(file_path, 'r') as file:
            result = file.read()
        # Parse the report to extract the coverage percentage
        coverage_line = None
        for line in result.splitlines():
            if "TOTAL" in line:
                coverage_line = line
                break

        if coverage_line:
            coverage_percentage = (float(coverage_line.split()[3].replace('%', ''))
                                + float(coverage_line.split()[6].replace('%', ''))
                                + float(coverage_line.split()[9].replace('%', ''))
                                + float(coverage_line.split()[12].replace('%', ''))) / 4

            return coverage_percentage
        else:
            return 0.0

    except Exception as e:
        return f"Error extracting coverage percentage: {str(e)}"


if __name__ == "__main__":
    file_path = "../outputs/temp/coverage/raw_coverage.txt"
    coverage = extract_coverage_percentage(file_path)
    print(f"Coverage: {coverage}")