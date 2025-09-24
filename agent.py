"""
Agent-as-Coder: Bank Statement Parser Generator

"""

import argparse
import os
import sys
from typing import List, Annotated, TypedDict
import operator
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode


# Import the custom tools
from tools import (
    analyze_pdf_structure, 
    test_parser_in_docker, 
    save_parser_to_file
)


class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]

def agent_node(state: AgentState, llm_with_tools):
    """The 'thinker' node that calls the LLM to decide the next action."""
    response = llm_with_tools.invoke(state['messages'])
    return {"messages": [response]}

def should_continue(state: AgentState):
    """Conditional edge to decide whether to continue or end."""
    if state['messages'][-1].tool_calls:
        return "continue"
    return "end"

def create_master_prompt(target_bank: str) -> str:
    """Creates the initial, detailed instruction for the agent."""
    pdf_path = Path("data") / target_bank / f"{target_bank} sample.pdf"

    return f"""
    You are an expert AI data engineer. Your mission is to create a Python parser for the bank statement of `{target_bank}`. You will operate in a self-correcting loop until the generated parser is perfect.

    Here is your plan and the tools you must use in order:
    
    1. ANALYZE: Your first step is to understand the PDF's structure. Call the `analyze_pdf_structure` tool with the path: `{pdf_path}`.

    2. GENERATE & TEST:
        a. Based on the analysis, write a Python parser function. The code must be a single function `parse(pdf_path: str) -> pd.DataFrame` using pandas and pdfplumber.
        b. Then, call the `test_parser_in_docker` tool. Pass the complete Python code you just generated to the `generated_parser_code` argument and `{target_bank}` to the `target_bank` argument.

    3. REFINE:
        a. The test tool will return a result. If the result contains "SUCCESS", the test has passed.
        b. If the result contains "FAILURE", you MUST analyze the error message and traceback. Determine the source of the error. If the error is in your generated parser, rewrite it. If the error seems to be in the testing process itself or in reading the data, report the issue.
        c. Go back to step 2b and test the new, corrected code. You have a maximum of 3 attempts.
        d. If you failed in 3 attempts, you will end the process. Respond with something like "Failed to create parser for {target_bank}. Exiting now..."

    4. SAVE & FINISH:
        a. Once the test passes and you see the "SUCCESS" message, your final task is to call the `save_parser_to_file` tool.
        b. Pass the final, correct version of your Python code to `final_parser_code` and `{target_bank}` to `target_bank`.
        c. After you recieve the success message from the save tool, YOUR MISSION IS COMPLETE. Do not call any more tools. To end the process, simply respond with a final message like "Parser for {target_bank} created and saved successfully."
    """

def main():
    """CLI entry point and agent runner."""
    parser = argparse.ArgumentParser(description="Agent-as-Coder: Bank Statement Parser Generator")
    parser.add_argument("--target", required=True, help="Target bank (e.g., icici)")
    args = parser.parse_args()

    load_dotenv()
    if not os.getenv("GOOGLE_API_KEY"):
        print("Error: GOOGLE_API_KEY environment variable is not set.", file=sys.stderr)
        return 1
    
    print(f"Initializing agent for target: {args.target}")

    # Initializing the list of tools
    tools = [
        analyze_pdf_structure,
        test_parser_in_docker,
        save_parser_to_file
    ]
    tool_node = ToolNode(tools)

    llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro", temperature=0)
    llm_with_tools = llm.bind_tools(tools)

    # Define the graph
    workflow = StateGraph(AgentState)
    workflow.add_node("agent", lambda state: agent_node(state, llm_with_tools))
    workflow.add_node("tools", tool_node)

    workflow.set_entry_point("agent")
    workflow.add_conditional_edges("agent", should_continue, {"continue": "tools", "end": END})
    workflow.add_edge("tools", "agent")

    app = workflow.compile()

    # Invoke the agent
    master_prompt = create_master_prompt(args.target)
    initial_state = {"messages": [HumanMessage(content=master_prompt)]}

    print("Agent starting its work... Follow the stream of events below.")
    for event in app.stream(initial_state, {"recursion_limit": 15}):
        for key, value in event.items():
            print(f"\n--- {key.upper()} ---")
            if key == 'agent':
                if value['messages'][-1].tool_calls:
                    tool_name = value['messages'][-1].tool_calls[0]['name']
                    print(f"LLM Decision: Call tool '{tool_name}'")
                else:
                    print("LLM Decision: End work")
            elif key == 'tools':
                tool_outputs = "\n".join([f"Tool Output: {str(msg.content)[:500]}..." for msg in value['messages']])
                print(tool_outputs)

    print("\n Agent has finished its work.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
    


