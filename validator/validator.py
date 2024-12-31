import subprocess
import logging
from extractor.extractor import extract_interface_info  # Importing the extractor functions
from prompt_generator.prompt_gen import generate_gpt_prompt, filter_interfaces  # Updated import for filtering
from llm_model.llm_model import generate_fuzz_driver_llm  # Importing the function from llm_model.py
from candidate_generator.candidate_gen import CandidateGenerator  # Assumes candidate_gen.py provides a class to generate fuzzing drivers

class Validator:
    def __init__(self, target_file: str, llvm_cov_path: str = 'llvm-cov'):
        self.target_file = target_file
        self.llvm_cov_path = llvm_cov_path
        self.logger = logging.getLogger(__name__)

    def generate_fuzz_driver(self, target_function: str) -> list:
        """
        Generate multiple fuzz testing driver variants using extracted API information.
        """
        try:
            # Step 1: Extract API information using the APIExtractor (from extractor.py)
            api_info = extract_interface_info(self.target_file)

            # Step 2: Filter out excluded functions (from prompt_gen.py)
            filtered_api_info = filter_interfaces(api_info)

            # Step 3: Generate prompt using the updated generate_gpt_prompt (from prompt_gen.py)
            prompt = generate_gpt_prompt(filtered_api_info, self.target_file)

            # Step 4: Use LLM to generate fuzz driver code based on the prompt
            llm_response = generate_fuzz_driver_llm(prompt)

            if not llm_response:
                raise Exception("Failed to generate fuzz driver from LLM response.")

            # Step 5: Generate multiple fuzz driver variants using the CandidateGenerator (from candidate_gen.py)
            candidate_gen = CandidateGenerator()
            fuzz_drivers = candidate_gen.generate_multiple_variants(llm_response, filtered_api_info)

            if not fuzz_drivers:
                raise Exception("Failed to generate fuzz driver variants.")

            self.logger.info(f"{len(fuzz_drivers)} fuzz driver variants generated successfully.")
            return fuzz_drivers

        except Exception as e:
            self.logger.error(f"Error generating fuzz drivers: {str(e)}")
            raise

    def compile_with_coverage(self, fuzz_driver: str) -> str:
        """
        Compile fuzz driver and target file with coverage instrumentation.
        """
        try:
            # Compile the fuzz driver with target file
            compile_command = [
                'clang', '-g', '-fsanitize=fuzzer', '-fprofile-instr-generate',
                '-fcoverage-mapping', '-o', 'fuzz_driver', self.target_file, '-c', '-std=c++11'
            ]

            # Write fuzz driver to a temporary file
            with open("fuzz_driver.cpp", "w") as file:
                file.write(fuzz_driver)

            compile_command.append("fuzz_driver.cpp")

            # Execute compilation
            subprocess.run(compile_command, check=True)
            self.logger.info("Fuzz driver compiled with coverage.")

            return 'fuzz_driver'

        except Exception as e:
            self.logger.error(f"Error compiling fuzz driver: {str(e)}")
            raise

    def run_fuzzing_and_measure_coverage(self, driver_file: str) -> float:
        """
        Run fuzz testing and measure code coverage.
        """
        try:
            # Run the fuzz driver
            run_command = ['./fuzz_driver']
            subprocess.run(run_command, check=True)
            self.logger.info("Fuzz driver executed.")

            # Generate coverage report using llvm-cov
            llvm_cov_command = [
                self.llvm_cov_path, 'gcov', 'fuzz_driver.profraw'
            ]
            subprocess.run(llvm_cov_command, check=True)

            # Get the coverage report
            coverage_command = ['llvm-cov', 'report', 'fuzz_driver']
            result = subprocess.run(coverage_command, capture_output=True, text=True)
            self.logger.info("Coverage report generated.")

            # Parse the report to extract the coverage percentage
            coverage_line = None
            for line in result.stdout.splitlines():
                if "Total" in line:
                    coverage_line = line
                    break

            if coverage_line:
                coverage_percentage = float(coverage_line.split()[3].replace('%', ''))
                self.logger.info(f"Code coverage: {coverage_percentage}%")
                return coverage_percentage
            else:
                self.logger.error("Coverage data not found in the report.")
                return 0.0

        except Exception as e:
            self.logger.error(f"Error during fuzzing and coverage measurement: {str(e)}")
            return 0.0

    def validate_fuzzing(self, target_function: str) -> float:
        """
        Full validation process: generate fuzz driver variants, compile, run fuzzing, and measure coverage for all variants.
        """
        fuzz_drivers = self.generate_fuzz_driver(target_function)
        total_coverage = 0.0
        for fuzz_driver in fuzz_drivers:
            compiled_driver = self.compile_with_coverage(fuzz_driver)
            coverage_percentage = self.run_fuzzing_and_measure_coverage(compiled_driver)
            total_coverage += coverage_percentage

        # Return average coverage across all variants
        return total_coverage / len(fuzz_drivers) if fuzz_drivers else 0.0

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Example: target function and target file
    target_function = "main"  # Replace with your function name
    target_file = "D:\\文件\\大三上\\软件测试\\llm-fuzz-driver\\targets\\unzipped\\libjpeg-turbo-3.0.4\\djpeg.c"  # Replace with your file path

    # Initialize the Validator and perform fuzzing validation
    validator = Validator(target_file)
    coverage = validator.validate_fuzzing(target_function)

    if coverage > 0:
        print(f"Fuzzing completed with {coverage}% code coverage.")
    else:
        print("Fuzzing failed to produce meaningful coverage.")