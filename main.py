import json
import os
import sys

from candidate_generator.candidate_gen import CandidateGenerator
from extractor.extractor import extract_interface_info
from llm_model.llm_model import generate_fuzz_driver_llm
from prompt_generator.prompt_gen import filter_interfaces, generate_gpt_prompt, generate_compiler_error_prompt, \
    gen_cov_improve_prompt
from validator.validator import validate_driver

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python main.py <config_file_path> <prebuild_shell_path>")
        sys.exit(1)

    # run the prebuild shell commands
    prebuild_shell_path = sys.argv[2]  # Path to the prebuild shell script
    if not os.path.exists(prebuild_shell_path):
        print(f"Error: Prebuild shell script not found at {prebuild_shell_path}")
        sys.exit(1)
    os.system(f"cd {os.path.dirname(prebuild_shell_path)}"
              f"&& bash {os.path.basename(prebuild_shell_path)}")

    # predefined variables
    json_file_path = sys.argv[1]  # Path to the json file containing the configuration
    if not os.path.exists(json_file_path):
        print(f"Error: Configuration file not found at {json_file_path}")
        sys.exit(1)
    with open(json_file_path, "r") as json_file:
        config = json.load(json_file)
    project_name = config["project_name"]
    target_name = config["target_name"]
    target_function = config["target_function"]
    target_file = config["target_file"]
    test_driver_model_code_path = config["test_driver_model_code_path"]
    max_iterations = config["max_iterations"]
    compile_command = config["compile_command"]
    current_file_path = os.path.dirname(os.path.abspath(__file__))

    # extractor
    api_info = extract_interface_info(target_file)
    filtered_api_info = filter_interfaces(api_info, target_file)

    state = "init"

    for i in range(max_iterations):
        # prompt_generator
        prompt = ""
        if state == "init":
            prompt = generate_gpt_prompt(filtered_api_info, project_name, target_name, test_driver_model_code_path)
        elif state == "compile_err":
            with open(current_file_path + "/outputs/temp/candidate_fuzz_drivers/raw.c", "r") as file:
                invalid_driver_code = file.read()
            prompt = generate_compiler_error_prompt(invalid_driver_code,project_name, target_name, current_file_path+"/outputs/temp/error_logs/raw_error_log.txt")
        elif state == "low_cov":
            with open(current_file_path + "/outputs/temp/candidate_fuzz_drivers/raw.c", "r") as file:
                invalid_driver_code = file.read()
            prompt = gen_cov_improve_prompt(invalid_driver_code,project_name, target_name,
                                            current_file_path+"/outputs/temp/coverage/raw_coverage.txt")

        # llm_model
        llm_response = generate_fuzz_driver_llm(prompt)

        # candidate_generator
        api_info = {
            "required_headers": [],  # TODO: customize required header files here
        }
        generator = CandidateGenerator()
        driver_code = generator.generate_driver(llm_response, api_info)
        # write the driver code to file: /outputs/temp/candidate_fuzz_drivers/raw.c
        output_path = current_file_path + '/outputs/temp/candidate_fuzz_drivers/raw.c'
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(current_file_path + "/outputs/temp/candidate_fuzz_drivers/raw.c", "w") as file:
            file.write(driver_code)

        # validator
        # copy the generated driver to the target directory and set the driver_file_path
        target_directory = os.path.dirname(target_file)
        driver_file_path = current_file_path + "/" + target_directory + "/driver.c"
        os.system(f"cp {current_file_path}/outputs/temp/candidate_fuzz_drivers/raw.c {driver_file_path}")
        result = validate_driver(driver_file_path, compile_command)

        # check the result, perform refining if necessary
        if result == "Valid Driver":
            print("Driver generated successfully.")
            # move the generated driver to the valid drivers directory '/outputs/validated_fuzz_drivers'
            with open(current_file_path + "/outputs/validated_fuzz_drivers/valid_driver.c", "w") as file:
                file.write(driver_code)
            state = "success"
            break
        elif result == "Compilation Error":
            print("Compilation error. Trying again...")
            state = "compile_err"
        elif result == "Low Coverage":
            print("Low coverage. Trying again...")
            state = "low_cov"

    if state != "success":
        print("Failed to generate a valid driver in the given number of iterations.")
