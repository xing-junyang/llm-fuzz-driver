from candidate_generator.candidate_gen import CandidateGenerator
from extractor.extractor import extract_interface_info
from llm_model.llm_model import generate_fuzz_driver_llm
from prompt_generator.prompt_gen import filter_interfaces, generate_gpt_prompt, generate_compiler_error_prompt, gen_cov_improve_prompt
from validator.validator import validate_driver

if __name__ == "__main__":
    # predefined variables
    project_name = "libxml2"  # Replace with your project name
    target_name = "xmllint"  # Replace with your target name
    target_function = "main"  # Replace with your function name
    target_file = "./targets/unzipped/libxml2-2.13.4/xmllint.c"  # Replace with your file path
    test_driver_model_code_path = "./prompt_generator/model.c" # Default path to the test driver model code
    max_iterations = 10  # Maximum number of iterations for the LLM model

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
            prompt = generate_compiler_error_prompt("outputs/temp/candidate_fuzz_drivers/raw.c", "outputs/temp/error_logs/raw_error_log.txt")
        elif state == "low_cov":
            prompt = gen_cov_improve_prompt("outputs/temp/candidate_fuzz_drivers/raw.c", "outputs/temp/coverage_reports/raw_coverage_report.txt")

        # llm_model
        llm_response = generate_fuzz_driver_llm(prompt)

        # candidate_generator
        api_info = {
            "required_headers": [], # TODO: customize required header files here
        }
        generator = CandidateGenerator()
        driver_code = generator.generate_driver(llm_response, api_info)
        # write the driver code to file: /outputs/temp/candidate_fuzz_drivers/raw.c
        with open("outputs/temp/candidate_fuzz_drivers/raw.c", "w") as file:
            file.write(driver_code)

        # validator
        driver_file_name = 'raw.c'
        result = validate_driver(driver_file_name)

        # check the result, perform refining if necessary
        if result == "Valid Driver":
            print("Driver generated successfully.")
            # move the generated driver to the valid drivers directory '/outputs/validated_fuzz_drivers'
            with open("outputs/validated_fuzz_drivers/valid_driver.c", "w") as file:
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
