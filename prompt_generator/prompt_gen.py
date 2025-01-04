import re

from extractor.extractor import extract_interface_info

# Define a list of excluded C library functions
EXCLUDED_FUNCTIONS = {"strcmp", "fprintf", "malloc", "free", "memcpy", "strlen", "printf","endTimer","__errno_location"}


def extract_static_or_macro_functions(file_path):
    """
    Extract the names of all static or macro-defined functions in a C file.
    Args:
        file_path (str): Path to the C source file.
    Returns:
        set: A set of function names defined as static or using macros.
    """
    static_functions = set()
    # Regex pattern to match static or macro-defined functions
    function_pattern = re.compile(
        r'\b(static|[\w_]+_ATTR_[\w_]+)\b[\s\S]*?\b(\w+)\s*\(', re.MULTILINE
    )

    try:
        with open(file_path, 'r') as file:
            content = file.read()
            matches = function_pattern.finditer(content)
            for match in matches:
                # The function name is captured in the second group
                static_functions.add(match.group(2))
    except FileNotFoundError:
        raise FileNotFoundError(f"Source file '{file_path}' not found.")
    except Exception as e:
        raise Exception(f"Error reading the source file: {e}")

    return static_functions


def filter_interfaces(interfaces, file_path):
    """
    Filter out standard C library functions and static/macro-defined functions from the interfaces.
    Args:
        interfaces (list): List of interface dictionaries.
        file_path (str): Path to the C source file.
    Returns:
        list: Filtered interfaces.
    """
    static_or_macro_functions = extract_static_or_macro_functions(file_path)
    return [
        interface for interface in interfaces
        if interface["function_name"] not in EXCLUDED_FUNCTIONS
        and interface["function_name"] not in static_or_macro_functions
    ]



def generate_gpt_prompt(interfaces, project_name, target, test_driver_model_code_path):
    """
    Generate a single GPT prompt based on the filtered interface information
    and project-specific details using a provided code template.

    Args:
        interfaces (list): List of filtered interface information.
        project_name (str): Name of the project.
        target (str): Target being tested.
        test_driver_model_code_path (str): File path to the code template for the test driver.

    Returns:
        str: A GPT-friendly prompt for generating a unified test driver.
    """
    # Read the code template from the file
    try:
        with open(test_driver_model_code_path, "r") as file:
            test_driver_model_code = file.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Template file '{test_driver_model_code_path}' not found.")
    except Exception as e:
        raise Exception(f"Error reading the template file: {e}")

    # Add general project context to the prompt
    prompt = (
        "You are a code assistant specializing in fuzz testing. Your task is to create a unified test driver program "
        "using LibFuzzer to test functions in the project. Below are the project details:\n\n"
    )

    # Insert the project-specific information
    prompt += f"project_name: {project_name}\n\n"
    prompt += f"target: {target}\n\n"

    # Explain the purpose of the test driver
    prompt += (
        "The test driver program should:\n"
        "1. Be compatible with LibFuzzer.\n"
        "2. Test the following functions:\n\n"
    )

    # Add interface details
    for interface in interfaces:
        function_name = interface["function_name"]
        parameters = interface["parameters"]

        # Add function name and parameter details
        prompt += f"### Function Name: {function_name}\n"
        prompt += "Parameters:\n"
        for param in parameters:
            param_type = param["type"]
            param_name = param["name"]
            prompt += f"- {param_type} {param_name}\n"
        prompt += "\n"

    # Add code template guidance
    prompt += (
        "Use the following code template as a guide for structuring the test driver:\n\n"
        f"{test_driver_model_code}\n\n"
    )

    # Provide additional guidance on generating the driver
    prompt += (
        "Based on the above information, generate a single test driver program that:\n"
        "1. Implements a LibFuzzer-compatible entry point (LLVMFuzzerTestOneInput).\n"
        "2. Fuzzes all the above functions by:\n"
        "   - Extracting parameter values from the fuzzed input.\n"
        "   - Calling each function with appropriate parameters.\n"
        "3. Incorporates project-specific constraints and best practices.\n"
        "4. Handles edge cases and invalid inputs gracefully.\n\n"
        "Provide the complete C code for the test driver. Don't generate anything other than the C code."
    )

    return prompt


if __name__ == "__main__":
    file_path = "../targets/libxml2-2.13.4/xmllint.c"
    template_path = "test_driver_template.c"  # Path to the test driver template file

    # Extract the interfaces from the source file
    interfaces = extract_interface_info(file_path)

    # Filter out excluded functions
    filtered_interfaces = filter_interfaces(interfaces,'../targets/libxml2-2.13.4/xmllint.c')

    # Generate the GPT prompt
    prompt = generate_gpt_prompt(filtered_interfaces, "libxml2-2.13.4", "xmllint", "../targets/libxml2-2.13.4/fuzz_driver.c")

    # Save to a file for inspection or further usage
    with open("gpt_prompt.txt", "w") as f:
        f.write(prompt)

    print("Filtered prompt generated and saved to gpt_prompt.txt.")
