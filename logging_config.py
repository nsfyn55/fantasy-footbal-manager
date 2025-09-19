"""
Simple logging configuration for Fantasy Football Manager
Provides clean separation between logging and terminal output.
"""

import sys
import os


class TerminalOutput:
    """Clean terminal output for user-facing messages only"""
    
    @staticmethod
    def info(message: str):
        """Print informational message to terminal"""
        print(message)
    
    @staticmethod
    def success(message: str):
        """Print success message to terminal"""
        print(f"✓ {message}")
    
    @staticmethod
    def warning(message: str):
        """Print warning message to terminal"""
        print(f"⚠ {message}")
    
    @staticmethod
    def error(message: str):
        """Print error message to terminal"""
        print(f"✗ {message}", file=sys.stderr)
    
    @staticmethod
    def progress(message: str):
        """Print progress message to terminal"""
        print(f"→ {message}")


def get_terminal() -> TerminalOutput:
    """
    Get terminal output handler
    
    Returns:
        TerminalOutput instance
    """
    return TerminalOutput()