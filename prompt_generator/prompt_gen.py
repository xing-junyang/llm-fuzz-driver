import json
from extractor.extractor import extract_interface_info, get_context_lines

# Define a list of excluded C library functions
EXCLUDED_FUNCTIONS = {"strcmp", "fprintf", "malloc", "free", "memcpy", "strlen", "printf"}

CONTEXT_LINES = 5  # Number of context lines around the function call


def filter_interfaces(interfaces):
    """
    Filter out standard C library functions from the interfaces.
    Args:
        interfaces (list): List of interface dictionaries.
    Returns:
        list: Filtered interfaces.
    """
    return [
        interface for interface in interfaces
        if interface["function_name"] not in EXCLUDED_FUNCTIONS
    ]


def generate_gpt_prompt(interfaces, file_path):
    """
    Generate a single GPT prompt based on the filtered interface information.
    Args:
        interfaces (list): List of filtered interface information.
        file_path (str): Path to the original C file for extracting context.
    Returns:
        str: A GPT-friendly prompt for generating a unified test driver.
    """
    prompt = (
        "You are a code assistant specializing in fuzz testing. Your task is to create a unified test driver program "
        "using LibFuzzer to test the following functions:\n\n"
    )

    for interface in interfaces:
        function_name = interface["function_name"]
        parameters = interface["parameters"]
        seen_lines = interface["seen_line"]

        # Add function details
        prompt += f"### Function Name: {function_name}\n"
        prompt += "Parameters:\n"
        for param in parameters:
            param_type = param["type"]
            param_name = param["name"]
            prompt += f"- {param_type} {param_name}\n"

        # Add context information
        prompt += "Context:\n"
        for line in seen_lines:
            context = get_context_lines(file_path, line)
            prompt += f"Line {line}:\n"
            for i, context_line in enumerate(context, start=1):
                prefix = "->" if i == CONTEXT_LINES + 1 else "  "
                prompt += f"{prefix} {context_line}"

        prompt += "\n"

    prompt += (
        "Generate a single test driver program that:\n"
        "1. Implements a LibFuzzer-compatible entry point (LLVMFuzzerTestOneInput).\n"
        "2. Fuzzes all the above functions by:\n"
        "   - Extracting parameter values from the fuzzed input.\n"
        "   - Calling each function with appropriate parameters.\n"
        "3. Handles edge cases and invalid inputs gracefully.\n\n"
        "Provide the full CPP code for the test driver. Don't generate anything other than cpp code."
    )

    return prompt


if __name__ == "__main__":
    file_path = "../targets/libxml2-2.13.4/xmllint.c"

    interfaces = extract_interface_info(file_path)

    # Filter out excluded functions
    filtered_interfaces = filter_interfaces(interfaces)

    # Generate the GPT prompt
    prompt = generate_gpt_prompt(filtered_interfaces, file_path)

    # Save to a file for inspection or further usage
    with open("gpt_prompt.txt", "w") as f:
        f.write(prompt)

    print("Filtered prompt generated and saved to gpt_prompt.txt.")
