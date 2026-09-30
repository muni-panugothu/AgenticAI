from app.tools.calculator import calculator
from app.tools.time_tool import get_current_time
from app.tools.file_reader import read_file
from app.tools.code_search import search_code
from app.tools.web_search import web_search


# --------------------------------
# Actual Python tools
# --------------------------------

tools = {
    "calculator": calculator,
    "get_current_time": get_current_time,
    "read_file": read_file,
    "search_code": search_code,
    "web_search": web_search
}


# --------------------------------
# Tool definitions for the LLM
# --------------------------------

tool_definitions = [

    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Calculate a mathematical expression.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Mathematical expression to calculate."
                    }
                },
                "required": ["expression"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current date and time.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },

  {
    "type": "function",
    "function": {
        "name": "read_file",
        "description": "Read the contents of a project file. Optionally read a specific line range.",
        "parameters": {
            "type": "object",
            "properties": {

                "file_path": {
                    "type": "string",
                    "description": "Path of the file to read."
                },

                "line_start": {
                    "type": "integer",
                    "description": "Optional starting line number."
                },

                "line_end": {
                    "type": "integer",
                    "description": "Optional ending line number."
                }

            },

            "required": ["file_path"]
        }
    }
},

   
 {
    "type": "function",
    "function": {
        "name": "search_code",

        "description": (
            "Search the project's application source "
            "code for text, function names, classes, "
            "variables, or imports."
        ),

        "parameters": {
            "type": "object",

            "properties": {

                "search_text": {
                    "type": "string",
                    "description": (
                        "Text or function name to search for."
                    )
                },

                "folder_path": {
                    "type": "string",
                    "description": (
                        "Optional project folder to search. "
                        "Defaults to app."
                    )
                }
            },

            "required": [
                "search_text"
            ]
        }
    }
},

   {
    "type": "function",
    "function": {
        "name": "web_search",

        "description": (
            "Search the internet for current, "
            "recent, factual, or external information. "
            "Use this tool when the user explicitly asks "
            "to search the web, asks for latest/current/news "
            "information, or asks about information that may "
            "have changed recently."
        ),

        "parameters": {
            "type": "object",

            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "A concise search query."
                    )
                }
            },

            "required": ["query"]
        }
    }
}
]