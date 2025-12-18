"""
title: Basic Tool Template
author: Your Name
author_url: https://github.com/yourusername
description: A simple template for creating OpenWebUI tools
required_open_webui_version: 0.3.0
version: 1.0.0
license: MIT
"""


class Tools:
    """
    Basic tool template with essential structure
    """

    def __init__(self):
        """
        Initialize the tool.
        Set up any initial state or configuration here.
        """
        pass

    def example_method(
        self,
        prompt: str,
        __user__: dict = {},
        __event_emitter__=None
    ) -> str:
        """
        Example method that processes user input.

        Args:
            prompt: The user's input text
            __user__: Dictionary containing user information (id, name, email, role)
            __event_emitter__: Optional event emitter for status updates

        Returns:
            str: Processed result as a string

        Example:
            >>> tool = Tools()
            >>> result = tool.example_method("Hello, world!")
            >>> print(result)
        """
        try:
            # Your processing logic here
            result = f"Processed: {prompt}"
            
            return result

        except Exception as e:
            return f"Error: {str(e)}"
