import logging

from validator.validator import Validator

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Example: target function and target file
    target_function = "main"  # Replace with your function name
    target_file = "D:\\文件\\大三上\\软件测试\\llm-fuzz-driver\\targets\\unzipped\\"  # Replace with your file path

    # Initialize the Validator and perform fuzzing validation
    validator = Validator(target_file)
    coverage = validator.validate_fuzzing(target_function)

    if coverage > 0:
        print(f"Fuzzing completed with {coverage}% code coverage.")
    else:
        print("Fuzzing failed to produce meaningful coverage.")