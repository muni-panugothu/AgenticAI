import os


IGNORE_DIRECTORIES = {
    ".git",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".idea",
    ".vscode",
    "dist",
    "build"
}


SOURCE_EXTENSIONS = (
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".java",
    ".cpp",
    ".c",
    ".cs",
    ".go",
    ".html",
    ".css"
)


def search_code(
    search_text,
    folder_path="app"
):

    results = []

    try:

        if not os.path.exists(folder_path):

            return {
                "success": False,
                "error": f"Folder not found: {folder_path}"
            }

        for root, directories, files in os.walk(
            folder_path
        ):

            # Ignore unnecessary directories
            directories[:] = [
                directory
                for directory in directories
                if directory not in IGNORE_DIRECTORIES
            ]

            for file_name in files:

                if not file_name.endswith(
                    SOURCE_EXTENSIONS
                ):
                    continue

                file_path = os.path.join(
                    root,
                    file_name
                )

                try:

                    with open(
                        file_path,
                        "r",
                        encoding="utf-8",
                        errors="ignore"
                    ) as file:

                        content = file.read()

                    if search_text.lower() in content.lower():

                        results.append(file_path)

                except Exception:
                    continue

        if not results:

            return {
                "success": True,
                "query": search_text,
                "results": [],
                "message": "No matching files found."
            }

        return {
            "success": True,
            "query": search_text,
            "results": results[:30]
        }

    except Exception as e:

        return {
            "success": False,
            "error": f"Code search error: {str(e)}"
        }


# import os

# def search_code( search_text,
#     folder_path="."):
#     results = []

#     for root, directories, files in os.walk(folder_path):
#         for file_name in files:
#             if file_name.endswith((".py", ".js", ".html", ".jsx", ".ts", ".tsx", ".css")):
#                 file_path = os.path.join(root, file_name)
#                 try:
#                     with open(file_path, "r", encoding="utf-8") as file:
#                         content = file.read()
#                     if search_text.lower() in content.lower():
#                         results.append(file_path)
#                 except Exception:
#                     pass

#     if results:
#         return "\n".join(results)
#     return f"No files found containing: {search_text}"










