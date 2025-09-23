"""
Agent-as-Coder: Bank Statement Parser Generator

"""

import argparse
import os
import sys
from typing import List

from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

# Import the custom tools
from tools import analyze_pdf_structure, test_parser_in_docker, save_parser_to_file


class AgentState(dict):
    """State management for the agent"""
    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)
        self.setdefault('messages', [])

    @property
    def messages(self) -> List(BaseMessage):
        return self['messages']
    
    @messages.setter
    def messages(self, value: List[BaseMessage]):
        self['messages'] = value
