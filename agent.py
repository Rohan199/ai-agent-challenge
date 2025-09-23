"""
Agent-as-Coder: Bank Statement Parser Generator

"""

import argparse
import os
import sys
import subprocess
import pandas as pd 
import pdfplumber
from pathlib import Path
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
import json
import traceback

# LLM imports
import google.generativeai as genai

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from typing_extensions import Annotated


class AgentState:
    """State management for the agent"""
    def __init__(self, target_bank: str, pdf_path: str, csv_path: str):
        self.target_bank = target_bank
        self.pdf_path = pdf_path
        self.csv_path = csv_path
        self.pdf_analysis = None
        self.parser_code = None
        self.test_results = None
        self.error_message = None
        self.attempt = 0
        self.max_attempt = 3
        self.success = False

class LLMClient:
    """Gemini LLM client"""
    def __init__(self):
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model = genai.GenerativeModel("gemini-2.5-pro")

    def generate(self, prompt: str) -> str:
        """Generate text using Gemini"""
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error generating response: {str(e)}"

class BankParserAgent
