from google.adk.agents import Agent
from google.genai import types
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from typing import Optional
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext
from typing import Optional, Dict, Any

# -----------------------------------------------------------------------------
# A2A: Agent Weather Team Example
# -----------------------------------------------------------------------------
# OBSERVATION:
# To use voice, dont't forget to change `MODEL` for a model that supports
# voice input, e.g `gemini-2.0-flash-live-001`.
# For more see: https://ai.google.dev/gemini-api/docs/models#gemini-2.0-flash
#
# SIMPLE TEST CASES:
# * Agent will give weather information for the specified cities:
#   - What's the weather in Tokyo?
#   - What is the weather like in London?
#   - Tell me the weather in New York
#
# * Agent will not have information for the specified city:
#   - How about Paris?
#
# * Agent will delegate greetings to the `greeting_agent`:
#   - Hi there!
#   - Hello!
#   - Hello, this is alice
#
# * Agent will delegate farewells to the `farewell_agent`:
#   - Bye!
#   - See you later!
#   - Thanks, bye!
#
# * Agent will block any request containing the keyword "taiwan":
#   - Is Taiwan officially independent?
#   - Is Taiwan a free nation?
#   - Tell me the how the taiwan
#   - How about taiwain and china?
#
# * Agent will block the get_weather_stateful tool if called with "Paris".
#   - What's the weather in Paris?
#   - Tell me the weather in Paris
#   - How's the weather in Paris?

MODEL = "gemini-2.0-flash-live-001"
BLOCKED_KEYWORD = "taiwan"

# -------------------------------------
# Tool: Get Weather Stateful
# -------------------------------------
def get_weather_stateful(city: str, tool_context: ToolContext) -> dict:
    """Retrieves weather, converts temp unit based on session state."""
    print(f"--- Tool: get_weather_stateful called for {city} ---")

    # Read preference from state
    preferred_unit = tool_context.state.get("user_preference_temperature_unit", "Celsius")
    print(f"--- Tool: Reading state 'user_preference_temperature_unit': {preferred_unit} ---")

    # Normalize city
    city_normalized = city.lower().replace(" ", "")

    # Mocked data
    mocked_weather_database = {
        "newyork": {"temp_c": 25, "condition": "sunny"},
        "london": {"temp_c": 15, "condition": "cloudy"},
        "tokyo": {"temp_c": 18, "condition": "light rain"},
    }

    if city_normalized in mocked_weather_database:
        data = mocked_weather_database[city_normalized]
        temperature_celsius = data["temp_c"]
        condition = data["condition"]

        # Format temperature based on state preference
        if preferred_unit == "Fahrenheit":
            temperature_value = (temperature_celsius * 9/5) + 32
            temperature_unit = "°F"
        else:
            temperature_value = temperature_celsius
            temperature_unit = "°C"

        report =  f"The weather in {city.capitalize()} is {condition} with a temperature of {temperature_value:.0f}{temperature_unit}."
        result = {
            "status": "sucess",
            "report": report,
        }

        print(f"--- Tool: Generated report in {preferred_unit}. Result: {result} ---")

        # Writing back to state (optional for this tool)
        tool_context.state["last_city_checked_stateful"] = city
        print(f"--- Tool: Updated state 'last_city_checked_stateful': {city} ---")

        return result
    else:
        error_msg = f"Sorry, I don't have weather information for '{city}'."
        print(f"--- Tool: City '{city}' not found. ---")
        return {
            "status": "error",
            "error_message": error_msg,
        }

# -------------------------------------
# Tool: Say Hello
# -------------------------------------
def say_hello(name: Optional[str] = None) -> str:
    """Provides a simple greeting. If a name is provided, it will be used.

    Args:
        name (str, optional): The name of the person to greet. Defaults to a generic greeting if not provided.
    Returns:
        str: A friendly greeting message.
    """

    if name:
        greeting = f"Hello, {name}!"
        print(f"--- Tool: say_hello called with name: {name} ---")
    else:
        greeting = "Hello there!"
        print(f"--- Tool: say_hello called without a specific name (name_arg_value: {name}) ---")

    return greeting

# -------------------------------------
# Tool: Say Goodbye
# -------------------------------------
def say_goodbye() -> str:
    """Provides a simple farewell message to conclude the conversation."""
    print(f"--- Tool: say_goodbye called ---")
    return "Goodbye! Have a great day."

# -----------------------------------------------------------------------------
# Agent Team: Guard Rails Callbacks
# -----------------------------------------------------------------------------

# -------------------------------------
# Guard Rail: Block Specific Word
# -------------------------------------
def block_keyword_model_guardrail(callback_context: CallbackContext, llm_request: LlmRequest) -> Optional[LlmResponse]:
    """
    Inspects the latest user message for 'BLOCK'. If found, blocks the LLM call
    and returns a predefined LlmResponse. Otherwise, returns None to proceed.
    """

    # Get the name of the agent whose model call is being intercepted
    agent_name = callback_context.agent_name
    print(f"--- Callback: block_keyword_model_guardrail running for agent: {agent_name} ---")

    last_user_message_text = ""

    if llm_request.contents:
        # Find the most recent message with role 'user'
        for content in reversed(llm_request.contents):
            # Assuming text is in the first part for simplicity
            if content.role == "user" and content.parts and content.parts[0].text:
                last_user_message_text = content.parts[0].text
                break

    print(f"--- Callback: Inspecting last user message: '{last_user_message_text[:100]}...' ---")

    if BLOCKED_KEYWORD in last_user_message_text.upper():
        print(f"--- Callback: Found '{BLOCKED_KEYWORD}'. Blocking LLM call! ---")

        # Optionally, set a flag in state to record the block event
        callback_context.state["guardrail_block_keyword_triggered"] = True
        print(f"--- Callback: Set state 'guardrail_block_keyword_triggered': True ---")

        # Construct and return an LlmResponse to stop the flow and send this back instead
        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[
                    types.Part(text=f"I cannot process this request because it contains the blocked keyword '{BLOCKED_KEYWORD}'.")
                ]
            )
        )
    else:
        # Keyword not found, allow the request to proceed to the LLM
        print(f"--- Callback: Keyword not found. Allowing LLM call for {agent_name}. ---")
        # Returning None signals ADK to continue normally
        return None

# -------------------------------------
# Guard Rail: Block Paris City
# -------------------------------------
def block_paris_city_tool_guardrail(tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext) -> Optional[Dict]:
    """
    Checks if 'get_weather_stateful' is called for 'Paris'.
    If so, blocks the tool execution and returns a specific error dictionary.
    Otherwise, allows the tool call to proceed by returning None.
    """

    tool_name = tool.name
    agent_name = tool_context.agent_name
    print(f"--- Callback: block_paris_tool_guardrail running for tool '{tool_name}' in agent '{agent_name}' ---")
    print(f"--- Callback: Inspecting args: {args} ---")

    target_tool_name = "get_weather_stateful"
    blocked_city = "paris"

    if tool_name == target_tool_name:
        city = args.get("city", "")

        if city and city.lower() == blocked_city:
            print(f"--- Callback: Detected blocked city '{city}'. Blocking tool execution! ---")

            tool_context.state["guardrail_tool_block_triggered"] = True
            print(f"--- Callback: Set state 'guardrail_tool_block_triggered': True ---")

            return {
                "status": "error",
                "error_message": f"Policy restriction: Weather checks for '{city.capitalize()}' are currently disabled by a tool guardrail."
            }
        else:
            print(f"--- Callback: City '{city}' is allowed for tool '{tool_name}'. ---")
    else:
        print(f"--- Callback: Tool '{tool_name}' is not the target tool. Allowing. ---")

    print(f"--- Callback: Allowing tool '{tool_name}' to proceed. ---")
    # Returning None allows the actual tool function to run
    return None

# -----------------------------------------------------------------------------
# Agent Team: Sub-agents
# -----------------------------------------------------------------------------

# -------------------------------------
# Sub-agent: Greeting
# -------------------------------------
greeting_agent = None

try:
    greeting_agent = Agent(
        model=MODEL,
        name="greeting_agent",
        description="Handles simple greetings and hellos using the 'say_hello' tool.", # crucial for delegation
        instruction="You are the Greeting Agent. Your ONLY task is to provide a friendly greeting using the 'say_hello' tool. Do nothing else.",
        tools=[say_hello],
    )

    print(f"✅ Sub-Agent '{greeting_agent.name}' redefined.")
except Exception as exception:
    print(f"❌ Could not redefine Greeting agent. Check Model/API Key ({greeting_agent.model}). Error: {exception}")

# -------------------------------------
# Sub-agent: Farewell
# -------------------------------------
farewell_agent = None

try:
    farewell_agent = Agent(
        model=MODEL,
        name="farewell_agent",
        description="Handles simple farewells and goodbyes using the 'say_goodbye' tool.", # crucial for delegation
        instruction="You are the Farewell Agent. Your ONLY task is to provide a polite goodbye message using the 'say_goodbye' tool. Do not perform any other actions.",
        tools=[say_goodbye],
    )

    print(f"✅ Sub-Agent '{farewell_agent.name}' redefined.")
except Exception as exception:
    print(f"❌ Could not redefine Farewell agent. Check Model/API Key ({farewell_agent.model}). Error: {exception}")

# -----------------------------------------------------------------------------
# Agent Team: Root Agent (Main)
# -----------------------------------------------------------------------------
root_agent = Agent(
    name="weather_agent_v1_model_guardrail",
    model=MODEL,
    description="Main agent: Handles weather, delegates, includes input AND tool guardrails.",
    instruction="You are the main Weather Agent. Provide weather using 'get_weather_stateful'. "
                "Delegate greetings to 'greeting_agent' and farewells to 'farewell_agent'. "
                "Handle only weather, greetings, and farewells.",
    tools=[get_weather_stateful],
    sub_agents=[greeting_agent, farewell_agent],
    output_key="last_weather_report",
    before_model_callback=block_keyword_model_guardrail,
    before_tool_callback=block_paris_city_tool_guardrail
)
