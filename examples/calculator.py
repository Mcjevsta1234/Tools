"""
title: Simple Calculator
author: OpenWebUI Tools
author_url: https://github.com/open-webui
description: A simple calculator for basic arithmetic operations
required_open_webui_version: 0.3.0
version: 1.0.0
license: MIT
"""


class Tools:
    """
    Simple calculator tool that performs basic arithmetic operations.
    Supports addition, subtraction, multiplication, and division.
    """

    def __init__(self):
        pass

    def calculate(
        self,
        expression: str,
        __user__: dict = {},
        __event_emitter__=None
    ) -> str:
        """
        Calculate the result of a mathematical expression.

        Args:
            expression: Mathematical expression (e.g., "2 + 2", "10 * 5")
            __user__: User information dictionary
            __event_emitter__: Optional event emitter

        Returns:
            str: Result of the calculation or error message

        Examples:
            - "2 + 2" -> "Result: 4"
            - "10 * 5" -> "Result: 50"
            - "(8 + 2) / 2" -> "Result: 5.0"
        """
        try:
            # Validate input
            if not expression or not isinstance(expression, str):
                return "Error: Please provide a valid mathematical expression"

            # Remove any potentially dangerous operations
            if any(keyword in expression.lower() for keyword in ['import', 'exec', 'eval', '__']):
                return "Error: Invalid expression"

            # Clean the expression
            expression = expression.strip()

            # Allowed characters for math operations
            allowed_chars = set('0123456789+-*/().% ')
            if not all(c in allowed_chars for c in expression):
                return "Error: Expression contains invalid characters. Use only numbers and operators (+, -, *, /, %, ())"

            # Calculate the result using eval (safe with our validation)
            result = eval(expression)

            # Format the result
            if isinstance(result, float) and result.is_integer():
                result = int(result)

            return f"**Result:** `{expression}` = **{result}**"

        except ZeroDivisionError:
            return "Error: Cannot divide by zero"
        except SyntaxError:
            return "Error: Invalid mathematical expression"
        except Exception as e:
            return f"Error: {str(e)}"
