# Extract the error log file

def extract_error_log(file_path: str) -> str:
    """
    Extract the error log from the given file, and return it.
    """
    try:
        with open(file_path, 'r') as file:
            error_log = file.read()
        return error_log
    except Exception as e:
        return f"Error reading log file: {str(e)}"