

# def read_file(file_path):

#     try:
#         with open(file_path, "r", encoding="utf-8") as file:
#             content = file.read()

#         return content
#     except Exception as e:

#         return f"Error:{e}"

#     except Exception as e:
#         return f"Error:{e}"


def read_file(
    file_path,
    line_start=None,
    line_end=None
):

    try:

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as file:

            lines = file.readlines()

        # Read the complete file
        if line_start is None and line_end is None:

            return {
                "success": True,
                "file_path": file_path,
                "content": "".join(lines)
            }

        # Convert line number to zero-based index
        start = (
            line_start - 1
            if line_start
            else 0
        )

        end = (
            line_end
            if line_end
            else len(lines)
        )

        selected_lines = lines[start:end]

        return {
            "success": True,
            "file_path": file_path,
            "line_start": line_start,
            "line_end": line_end,
            "content": "".join(selected_lines)
        }

    except FileNotFoundError:

        return {
            "success": False,
            "error": f"File not found: {file_path}"
        }

    except Exception as e:

        return {
            "success": False,
            "error": f"Error reading file: {str(e)}"
        }