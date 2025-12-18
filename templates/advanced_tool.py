"""
title: Advanced Tool Template
author: Your Name
author_url: https://github.com/yourusername
description: Advanced template with configuration, async support, and event emitters
required_open_webui_version: 0.3.0
version: 1.0.0
license: MIT
"""

from pydantic import BaseModel, Field
from typing import Optional, Callable, Any


class Tools:
    """
    Advanced tool template with Valves (configuration) and async support
    """

    class Valves(BaseModel):
        """
        Configuration options for the tool.
        Users can set these in the Open WebUI interface.
        """
        API_KEY: str = Field(
            default="",
            description="API key for external service"
        )
        MAX_RESULTS: int = Field(
            default=10,
            description="Maximum number of results to return",
            ge=1,
            le=100
        )
        TIMEOUT: int = Field(
            default=30,
            description="Timeout in seconds for API calls",
            ge=5,
            le=120
        )
        ENABLE_CACHE: bool = Field(
            default=True,
            description="Enable result caching"
        )

    def __init__(self):
        """
        Initialize the tool with configuration
        """
        self.valves = self.Valves()
        self.cache = {}

    async def process_async(
        self,
        prompt: str,
        __user__: dict = {},
        __event_emitter__: Optional[Callable[[dict], Any]] = None
    ) -> str:
        """
        Async method for long-running operations with progress updates.

        Args:
            prompt: The user's input text
            __user__: Dictionary containing user information
            __event_emitter__: Event emitter for status updates

        Returns:
            str: Processed result
        """
        try:
            # Validate configuration
            if not self.valves.API_KEY:
                return "Error: API_KEY not configured. Please set it in tool settings."

            # Emit start status
            if __event_emitter__:
                await __event_emitter__({
                    "type": "status",
                    "data": {
                        "description": "Starting process...",
                        "done": False
                    }
                })

            # Your async processing logic here
            result = await self._perform_operation(prompt)

            # Emit completion status
            if __event_emitter__:
                await __event_emitter__({
                    "type": "status",
                    "data": {
                        "description": "Process complete!",
                        "done": True
                    }
                })

            return result

        except Exception as e:
            if __event_emitter__:
                await __event_emitter__({
                    "type": "status",
                    "data": {
                        "description": f"Error: {str(e)}",
                        "done": True
                    }
                })
            return f"Error: {str(e)}"

    async def _perform_operation(self, prompt: str) -> str:
        """
        Internal method for performing the actual operation.

        Args:
            prompt: Input text to process

        Returns:
            str: Processed result
        """
        # Implement your logic here
        return f"Processed: {prompt}"

    def validate_input(self, input_data: str) -> tuple[bool, str]:
        """
        Validate user input.

        Args:
            input_data: Input to validate

        Returns:
            tuple[bool, str]: (is_valid, error_message)
        """
        if not input_data:
            return False, "Input cannot be empty"

        if len(input_data) > 10000:
            return False, "Input too long (max 10000 characters)"

        return True, ""

    def get_from_cache(self, key: str) -> Optional[str]:
        """
        Get cached result if caching is enabled.

        Args:
            key: Cache key

        Returns:
            Optional[str]: Cached result or None
        """
        if not self.valves.ENABLE_CACHE:
            return None

        return self.cache.get(key)

    def set_cache(self, key: str, value: str):
        """
        Store result in cache if caching is enabled.

        Args:
            key: Cache key
            value: Value to cache
        """
        if self.valves.ENABLE_CACHE:
            self.cache[key] = value
