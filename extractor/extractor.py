import os

# may use `pip install libclang` to install the package
from clang.cindex import Index, CursorKind

context_lines = 5 # Number of context lines around the function call

def extract_interface_info(file_path):
    """
    Extract function call information within the main function of a C file using Clang.
    Args:
        file_path (str): Path to the C file.
    Returns:
        list: A list of interface information, where each item is a dictionary:
            [
                {
                    "function_name": "processData",
                    "parameters": [
                        {"type": "const char*", "name": "input"},
                        {"type": "int", "name": "flag"}
                    ],
                    "seen_line": [10, 20, 30]
                },
                ...
            ]
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    index = Index.create()

    # build ast
    translation_unit = index.parse(file_path)
    if not translation_unit:
        raise RuntimeError("Failed to parse the file with Clang.")

    # extracted interface information
    interface_info = []

    # find the main function
    for node in translation_unit.cursor.get_children():
        if node.kind == CursorKind.FUNCTION_DECL and node.spelling == "main":
            # parse function calls within the main function
            interface_info = parse_main_function(node)
            break

    if not interface_info:
        raise ValueError("Main function or function calls not found.")

    return interface_info

def parse_function_calls(node, function_calls, function_calls_signature):
    """
    Recursively parse function calls in the AST.
    Args:
        node (clang.cindex.Cursor): Current AST node
        function_calls (list): List to store function call information
        function_calls_signature (set): Set to track unique function signatures
    """
    for child in node.get_children():
        if child.kind == CursorKind.CALL_EXPR:
            # Handle function pointer calls
            function_name = child.spelling
            if not function_name:
                function_name = '(Anonymous Function)'

            parameters = []
            seen_line = [child.location.line]

            # parameter types and names
            for arg in child.get_arguments():
                param_type = arg.type.spelling
                param_name = arg.spelling
                parameters.append({"type": param_type, "name": param_name})

            call_signature = (
                function_name,
                tuple((_param["type"]) for _param in parameters)
            )

            if call_signature not in function_calls_signature:
                function_calls_signature.add(call_signature)
                function_calls.append({
                    "function_name": function_name,
                    "parameters": parameters,
                    "seen_line": seen_line,
                })
            else:
                # append the line number to the existing function call
                for call in function_calls:
                    if call["function_name"] == function_name:
                        call["seen_line"].append(child.location.line)
                        break

        # recursively parse child nodes
        parse_function_calls(child, function_calls, function_calls_signature)

def parse_main_function(main_node):
    """
    Parse function call information within the main function. There are two main cases:
    1. The main function contains function calls directly.
    2. The main function contains a single function, and the function contains the actual function calls.
    Args:
        main_node (clang.cindex.Cursor): AST node of the main function.
    Returns:
        list: A list of function call information.
    """
    function_calls = []
    function_calls_signature = set()

    # parse the main function normally
    parse_function_calls(main_node, function_calls, function_calls_signature)

    # If the function_calls only contains a single function, that means the main function is actually in that function
    if len(function_calls) == 1:
        function_name = function_calls[0]["function_name"]
        index = Index.create()
        translation_unit = index.parse(file_path)
        for node in translation_unit.cursor.get_children():
            if node.kind == CursorKind.FUNCTION_DECL and node.spelling == function_name:
                # parse function calls within the actual main function
                function_calls = []
                function_calls_signature = set()
                parse_function_calls(node, function_calls, function_calls_signature)
                break
    return function_calls


def get_context_lines(file_path, line_number):
    """
    Get the context lines around a specific line number in a file.
    Args:
        file_path (str): Path to the file.
        line_number (int): Line number to get the context.
    Returns:
        list: A list of context lines. Note that the target line is at the index of `context_lines + 1`.
    """
    with open(file_path, "r") as f:
        lines = f.readlines()
    start_line = max(0, line_number - context_lines - 1)
    end_line = min(len(lines), line_number + context_lines)
    return lines[start_line:end_line]

# Run this Demo!
# This will extract the interface information from the provided C file and output to a file.
# You may have to extract the C file from the target project first.
if __name__ == "__main__":
    file_path = "../targets/unzipped/libjpeg-turbo-3.0.4/djpeg.c"  # Replace with your C file path
    try:
        interfaces = extract_interface_info(file_path)
        # Output to file
        with open("output.txt", "w") as f:
            for interface in interfaces:
                f.write(f"Function Name: {interface['function_name']}\n")
                f.write("Parameters:\n")
                for param in interface["parameters"]:
                    f.write(f"  - {param['type']} {param['name']}\n")
                f.write("Seen in Line: ")
                for line in interface["seen_line"]:
                    f.write(f"{line} ")
                f.write("\n")
                f.write("Examples (With context around function call):\n")
                for line in interface["seen_line"]:
                    for i, context_line in enumerate(get_context_lines(file_path, line), start=1):
                        if i == context_lines + 1: f.write(f"->  {line}: {context_line}")
                        else: f.write(f"    {line - context_lines + i}: {context_line}")
                    f.write("\n")
                f.write("\n")
    except Exception as e:
        print("Error:", e)
