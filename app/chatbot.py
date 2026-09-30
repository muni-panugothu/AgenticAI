import os
import json

from dotenv import load_dotenv
from groq import Groq

from app.tool_registry import (
    tools,
    tool_definitions
)

# Pydantic Validation
from pydantic import ValidationError
from app.validation.tool_registry import (
    tool_input_models
)

# Long-Term Memory
from app.services.memory_service import (
    get_memories,
    save_memory
)


# Embedding service for long-term memory
from app.services.embedding_service import (
    create_embedding
)



# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# GROQ CLIENT
# ============================================================

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


# ============================================================
# CONFIGURATION
# ============================================================

MODEL = "openai/gpt-oss-20b"

MAX_AGENT_STEPS = 10

MAX_SAME_TOOL_FAILURES = 3

MAX_TOOL_RESULT_CHARS = 12000

# Conversation memory limit
MAX_CONVERSATION_MESSAGES = 20

# Long-term memory limit
MAX_LONG_TERM_MEMORIES = 10

# Temporary user ID
# Later this should come from your authenticated user
USER_ID = "muni"


# ============================================================
# CONVERSATION MEMORY
# ============================================================

conversation_history = []


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are an AI Software Engineer assistant.

You have access to these tools:

1. calculator
2. get_current_time
3. read_file
4. search_code
5. web_search


============================================================
TOOL RULES
============================================================

Calculator:

Use calculator for mathematical calculations.


Time:

Use get_current_time when the user asks for the current
time or date.


Files:

Use read_file when the user asks about the contents
of a project file.


Code:

Use search_code when the user asks to find something
inside the project source code.


Web:

Use web_search when:

- The user explicitly says "search the web"
- The user says "search online"
- The user asks for latest information
- The user asks for current information
- The user asks for today's news
- The user asks about recent releases
- The user asks about current versions
- The user asks about current documentation
- The answer depends on information that may have changed


============================================================
IMPORTANT WEB RULES
============================================================

If the user explicitly asks you to search the web,
you MUST call web_search.

Do not answer a web-search request from internal
knowledge alone.

After receiving search results:

- Analyze them.
- Do not expose raw HTML.
- Do not invent facts.
- If results are insufficient, perform another search.
- Do not repeatedly search using the same or nearly
  identical query.
- If the web_search tool repeatedly fails, stop trying
  and explain that the search tool could not retrieve
  the required information.
- Then provide a final natural-language answer.


============================================================
PROJECT INVESTIGATION
============================================================

For project investigation:

- Search relevant source files.
- Read relevant files.
- Analyze the results.
- Use additional tools when necessary.
- Never invent source-code contents.


============================================================
CONVERSATION MEMORY
============================================================

You can see previous messages from the current conversation.

Use previous messages when they are relevant to the
user's current question.

Conversation memory only lasts while this application
is running.


============================================================
LONG-TERM MEMORY
============================================================

You may also receive persistent information about the user
from the long-term memory database.

Use long-term memory when it is relevant to the user's
current request.

Do not invent information that is not present in memory.

Long-term memory persists after the application is restarted.


============================================================
MEMORY RULE
============================================================

When the user explicitly says:

"Remember that ..."

save that information as long-term memory.

Do not automatically save every normal conversation message
as long-term memory.

Only explicit "remember that" requests should be saved at
this stage.


============================================================
FINAL ANSWER
============================================================

Always provide a final answer after tool execution.

Do not expose internal tool-selection reasoning.

Do not expose raw tool output unless it is directly
useful to the user.
"""


# ============================================================
# LIMIT TOOL RESULT
# ============================================================

def limit_tool_result(result):

    if isinstance(result, (dict, list)):

        result = json.dumps(
            result,
            ensure_ascii=False
        )

    else:

        result = str(result)


    if len(result) <= MAX_TOOL_RESULT_CHARS:

        return result


    return (
        result[:MAX_TOOL_RESULT_CHARS]
        + "\n\n"
        "[Tool result truncated because it was too large.]"
    )


# ============================================================
# EXECUTE TOOL
# ============================================================

def execute_tool(tool_name, tool_arguments):

    print(
        f"\n[Tool selected: {tool_name}]"
    )

    print(
        f"[Arguments: {tool_arguments}]"
    )


    # ========================================================
    # FIND TOOL
    # ========================================================

    tool_function = tools.get(
        tool_name
    )

    if tool_function is None:

        print(
            f"[Tool not found: {tool_name}]"
        )

        return {
            "success": False,
            "error": f"Tool not found: {tool_name}"
        }


    # ========================================================
    # FIND VALIDATION MODEL
    # ========================================================

    input_model = tool_input_models.get(
        tool_name
    )

    if input_model is None:

        print(
            f"[Validation model not found: {tool_name}]"
        )

        return {
            "success": False,
            "error": (
                f"No validation model "
                f"found for tool: {tool_name}"
            )
        }


    # ========================================================
    # VALIDATE TOOL ARGUMENTS
    # ========================================================

    try:

        validated_arguments = input_model(
            **tool_arguments
        )

        print(
            "[Arguments validated successfully]"
        )

    except ValidationError as e:

        print(
            "[Validation error]"
        )

        print(e)

        return {
            "success": False,
            "error": "Invalid tool arguments",
            "details": e.errors()
        }


    # ========================================================
    # EXECUTE TOOL
    # ========================================================

    try:

        result = tool_function(
            **validated_arguments.model_dump()
        )


        result = limit_tool_result(
            result
        )


        print(
            f"[Tool result size: "
            f"{len(result)} characters]"
        )


        print(
            f"[Tool result preview]: "
            f"{result[:1000]}"
        )


        return {
            "success": True,
            "result": result
        }


    except Exception as e:

        print(
            f"[Tool execution error]: {e}"
        )

        return {
            "success": False,
            "error": "Tool execution error",
            "details": str(e)
        }


# ============================================================
# ADD MESSAGE TO CONVERSATION MEMORY
# ============================================================

def add_to_conversation_memory(
    role,
    content
):

    conversation_history.append({

        "role": role,

        "content": content

    })


    # ========================================================
    # LIMIT MEMORY SIZE
    # ========================================================

    if len(conversation_history) > MAX_CONVERSATION_MESSAGES:

        del conversation_history[
            :-MAX_CONVERSATION_MESSAGES
        ]


# ============================================================
# GET CONVERSATION MEMORY
# ============================================================

def get_conversation_memory():

    return conversation_history.copy()


# ============================================================
# CLEAR CONVERSATION MEMORY
# ============================================================

def clear_conversation_memory():

    conversation_history.clear()

    print(
        "[Conversation memory cleared]"
    )


# ============================================================
# LOAD LONG-TERM MEMORY
# ============================================================

def load_long_term_memory(
    user_id
):

    print(
        "\n[Loading long-term memory...]"
    )

    result = get_memories(
        user_id=user_id,
        limit=MAX_LONG_TERM_MEMORIES
    )


    if not result.get(
        "success",
        False
    ):

        print(
            "[Long-term memory unavailable]"
        )

        return []


    memories = result.get(
        "memories",
        []
    )


    print(
        f"[Long-term memories loaded: "
        f"{len(memories)}]"
    )


    return memories


# ============================================================
# BUILD LONG-TERM MEMORY CONTEXT
# ============================================================

def build_memory_context(
    memories
):

    if not memories:

        return ""


    memory_lines = []


    for item in memories:

        memory = item.get(
            "memory"
        )

        if memory:

            memory_lines.append(
                f"- {memory}"
            )


    if not memory_lines:

        return ""


    return (
        "Known information about the user "
        "from long-term memory:\n\n"
        + "\n".join(memory_lines)
    )


# ============================================================
# SAVE EXPLICIT LONG-TERM MEMORY
# ============================================================

def try_save_explicit_memory(
    user_message,
    user_id
):

    text = user_message.strip()


    prefix = "remember that "


    # ========================================================
    # CHECK WHETHER USER EXPLICITLY REQUESTED MEMORY
    # ========================================================

    if not text.lower().startswith(
        prefix
    ):

        return False


    # ========================================================
    # EXTRACT MEMORY
    # ========================================================

    memory = text[
        len(prefix):
    ].strip()


    if not memory:

        return False


    print(
        "\n[Explicit memory request detected]"
    )


    print(
        f"[Memory content: {memory}]"
    )


    # ========================================================
    # CREATE EMBEDDING
    # ========================================================

    try:

        print(
            "[Creating memory embedding...]"
        )


        embedding = create_embedding(
            memory
        )


        print(
            "[Memory embedding created successfully]"
        )


    except Exception as e:

        print(
            f"[Memory embedding failed]: {e}"
        )

        return False


    # ========================================================
    # SAVE MEMORY + EMBEDDING
    # ========================================================

    result = save_memory(

        user_id=user_id,

        memory=memory,

        embedding=embedding

    )


    if result.get(
        "success",
        False
    ):

        print(
            "[Long-term memory saved successfully]"
        )

        return True


    print(
        "[Long-term memory save failed]"
    )


    return False


# ============================================================
# CHAT WITH AI
# ============================================================

def chat_with_ai(
    user_message
):

    # ========================================================
    # SAVE EXPLICIT LONG-TERM MEMORY
    # ========================================================

    memory_saved = try_save_explicit_memory(

        user_message,

        USER_ID

    )


    # ========================================================
    # ADD USER MESSAGE TO CONVERSATION MEMORY
    # ========================================================

    add_to_conversation_memory(

        "user",

        user_message

    )


    # ========================================================
    # LOAD LONG-TERM MEMORY
    # ========================================================

    long_term_memories = (
        load_long_term_memory(
            USER_ID
        )
    )


    # ========================================================
    # BUILD MEMORY CONTEXT
    # ========================================================

    memory_context = (
        build_memory_context(
            long_term_memories
        )
    )


    # ========================================================
    # CREATE LLM MESSAGES
    # ========================================================

    messages = [

        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }

    ]


    # ========================================================
    # ADD LONG-TERM MEMORY
    # ========================================================

    if memory_context:

        messages.append({

            "role": "system",

            "content": memory_context

        })


    # ========================================================
    # ADD CONVERSATION MEMORY
    # ========================================================

    messages.extend(
        get_conversation_memory()
    )


    # ========================================================
    # TOOL FAILURE TRACKING
    # ========================================================

    tool_failure_counts = {}


    # ========================================================
    # AGENT LOOP
    # ========================================================

    for step in range(
        MAX_AGENT_STEPS
    ):

        print(
            f"\n[Agent step "
            f"{step + 1}/"
            f"{MAX_AGENT_STEPS}]"
        )


        print(
            "[Calling LLM...]"
        )


        # ====================================================
        # CALL LLM
        # ====================================================

        try:

            response = client.chat.completions.create(

                model=MODEL,

                messages=messages,

                tools=tool_definitions,

                tool_choice="auto"

            )

        except Exception as e:

            print(
                f"[LLM error]: {e}"
            )

            return (
                "The AI model request failed: "
                f"{e}"
            )


        # ====================================================
        # GET RESPONSE MESSAGE
        # ====================================================

        response_message = (
            response.choices[0].message
        )


        # ====================================================
        # FINAL ANSWER
        # ====================================================

        if not response_message.tool_calls:

            print(
                "[No more tools needed]"
            )


            final_answer = (
                response_message.content
                or
                "I could not generate a response."
            )


            # ================================================
            # SAVE AI RESPONSE TO CONVERSATION MEMORY
            # ================================================

            add_to_conversation_memory(

                "assistant",

                final_answer

            )


            return final_answer


        # ====================================================
        # TOOL CALLS FOUND
        # ====================================================

        print(
            f"\n[LLM selected "
            f"{len(response_message.tool_calls)} "
            f"tool(s)]"
        )


        # ====================================================
        # SAVE ASSISTANT TOOL-CALL MESSAGE
        # ====================================================

        messages.append(
            response_message
        )


        # ====================================================
        # EXECUTE TOOLS
        # ====================================================

        for tool_call in (
            response_message.tool_calls
        ):

            tool_name = (
                tool_call.function.name
            )


            # =================================================
            # PARSE TOOL ARGUMENTS
            # =================================================

            try:

                tool_arguments = json.loads(

                    tool_call.function.arguments

                )


                print(
                    f"[Parsed arguments: "
                    f"{tool_arguments}]"
                )


            except json.JSONDecodeError as e:

                print(
                    f"[JSON parsing error]: {e}"
                )


                tool_result = {

                    "success": False,

                    "error":
                        "Invalid tool arguments",

                    "details":
                        str(e)

                }


                messages.append({

                    "role": "tool",

                    "tool_call_id":
                        tool_call.id,

                    "name":
                        tool_name,

                    "content":
                        json.dumps(
                            tool_result,
                            ensure_ascii=False
                        )

                })


                continue


            # =================================================
            # EXECUTE TOOL
            # =================================================

            tool_result = execute_tool(

                tool_name,

                tool_arguments

            )


            # =================================================
            # TRACK TOOL FAILURES
            # =================================================

            if not tool_result.get(
                "success",
                False
            ):

                current_failures = (
                    tool_failure_counts.get(
                        tool_name,
                        0
                    )
                )


                current_failures += 1


                tool_failure_counts[
                    tool_name
                ] = current_failures


                print(
                    f"[Tool failure count: "
                    f"{tool_name} = "
                    f"{current_failures}]"
                )


            else:

                tool_failure_counts[
                    tool_name
                ] = 0


            # =================================================
            # SEND TOOL RESULT TO LLM
            # =================================================

            messages.append({

                "role": "tool",

                "tool_call_id":
                    tool_call.id,

                "name":
                    tool_name,

                "content":
                    json.dumps(
                        tool_result,
                        ensure_ascii=False
                    )

            })


            # =================================================
            # STOP REPEATED FAILURES
            # =================================================

            if (
                tool_failure_counts.get(
                    tool_name,
                    0
                )
                >= MAX_SAME_TOOL_FAILURES
            ):

                print(
                    f"[Stopping agent loop: "
                    f"{tool_name} failed "
                    f"{MAX_SAME_TOOL_FAILURES} times]"
                )


                final_answer = (

                    f"The tool '{tool_name}' "

                    f"failed "
                    f"{MAX_SAME_TOOL_FAILURES} times. "

                    "I could not complete the request."

                )


                add_to_conversation_memory(

                    "assistant",

                    final_answer

                )


                return final_answer


    # ========================================================
    # MAX STEPS REACHED
    # ========================================================

    print(
        "[Maximum agent steps reached]"
    )


    final_answer = (

        "I reached the maximum number of "
        "agent steps before completing the request."

    )


    add_to_conversation_memory(

        "assistant",

        final_answer

    )


    return final_answer