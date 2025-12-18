# Tool Development Guide

This guide will help you create high-quality tools for Open WebUI.

## 📚 Table of Contents

- [Tool Basics](#tool-basics)
- [Tool Structure](#tool-structure)
- [Valves (Configuration)](#valves-configuration)
- [Methods and APIs](#methods-and-apis)
- [Best Practices](#best-practices)
- [Testing](#testing)

## Tool Basics

### What is an OpenWebUI Tool?

OpenWebUI tools are Python classes that extend the functionality of Open WebUI. They can:
- Process data
- Make API calls
- Interact with external services
- Perform calculations
- Access web resources
- And much more!

### Minimum Requirements

- Python 3.11+
- Open WebUI 0.3.0+
- Valid tool structure with required metadata

## Tool Structure

### Basic Template

```python
"""
title: Tool Name
author: Your Name
author_url: https://github.com/yourusername
description: What your tool does
required_open_webui_version: 0.3.0
version: 1.0.0
license: MIT
"""

class Tools:
    def __init__(self):
        """Initialize the tool"""
        pass
    
    def example_method(self, prompt: str, **kwargs) -> str:
        """
        Example tool method
        
        Args:
            prompt: The user's input
            **kwargs: Additional arguments
            
        Returns:
            str: The result
        """
        return f"Processed: {prompt}"
```

### Required Metadata

In the docstring at the top of your file:

- `title`: Display name of your tool
- `author`: Your name
- `author_url`: Your website or GitHub profile
- `description`: Brief description of functionality
- `required_open_webui_version`: Minimum Open WebUI version
- `version`: Tool version (semantic versioning)
- `license`: License type (e.g., MIT)

## Valves (Configuration)

Valves allow users to configure your tool. Use them for API keys, settings, and options.

```python
from pydantic import BaseModel, Field

class Tools:
    class Valves(BaseModel):
        API_KEY: str = Field(
            default="",
            description="Your API key"
        )
        MAX_RESULTS: int = Field(
            default=10,
            description="Maximum number of results"
        )
        ENABLE_CACHE: bool = Field(
            default=True,
            description="Enable result caching"
        )
    
    def __init__(self):
        self.valves = self.Valves()
```

## Methods and APIs

### Available Context

Your tool methods receive context through `__user__` and `__event_emitter__`:

```python
def process(
    self,
    prompt: str,
    __user__: dict = {},
    __event_emitter__=None
) -> str:
    # Access user info
    user_id = __user__.get("id")
    user_name = __user__.get("name")
    
    # Emit events (show progress)
    if __event_emitter__:
        await __event_emitter__({
            "type": "status",
            "data": {"description": "Processing...", "done": False}
        })
    
    return result
```

### Event Emitter Types

```python
# Status update
await __event_emitter__({
    "type": "status",
    "data": {"description": "Processing...", "done": False}
})

# Show message
await __event_emitter__({
    "type": "message",
    "data": {"content": "Here's the result..."}
})

# Complete status
await __event_emitter__({
    "type": "status",
    "data": {"description": "Done!", "done": True}
})
```

## Best Practices

### 1. Error Handling

```python
def safe_method(self, prompt: str) -> str:
    try:
        result = risky_operation(prompt)
        return result
    except ValueError as e:
        return f"Invalid input: {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"
```

### 2. Input Validation

```python
def validate_input(self, data: str) -> bool:
    if not data or not isinstance(data, str):
        return False
    if len(data) > 10000:
        return False
    return True
```

### 3. Type Hints

```python
def process_data(
    self,
    input_text: str,
    max_length: int = 100
) -> dict[str, any]:
    return {
        "processed": input_text[:max_length],
        "length": len(input_text)
    }
```

### 4. Documentation

```python
def complex_function(self, data: str, options: dict) -> list:
    """
    Process data with custom options.
    
    This function takes input data and processes it according to
    the specified options. It returns a list of processed items.
    
    Args:
        data: The input data to process
        options: Dictionary of processing options
            - "format": Output format (default: "json")
            - "limit": Maximum results (default: 100)
    
    Returns:
        List of processed items
        
    Example:
        >>> tool.complex_function("test", {"format": "json"})
        [{"result": "processed"}]
    """
    pass
```

### 5. Async Support

```python
async def async_method(self, prompt: str, __event_emitter__=None) -> str:
    """Async method for long-running operations"""
    
    if __event_emitter__:
        await __event_emitter__({
            "type": "status",
            "data": {"description": "Starting...", "done": False}
        })
    
    result = await long_running_task(prompt)
    
    if __event_emitter__:
        await __event_emitter__({
            "type": "status",
            "data": {"description": "Complete!", "done": True}
        })
    
    return result
```

## Testing

### Manual Testing Checklist

- [ ] Tool loads without errors
- [ ] All methods work as expected
- [ ] Error handling works correctly
- [ ] Configuration valves work
- [ ] Documentation is clear
- [ ] Examples run successfully
- [ ] No hardcoded secrets

### Test Different Scenarios

1. **Valid inputs** - Normal operation
2. **Invalid inputs** - Error handling
3. **Edge cases** - Empty strings, very long inputs
4. **Missing config** - Undefined API keys
5. **Network issues** - API timeouts

## Advanced Features

### Rate Limiting

```python
import time
from collections import deque

class Tools:
    def __init__(self):
        self.requests = deque()
        self.rate_limit = 10  # requests per minute
    
    def check_rate_limit(self) -> bool:
        now = time.time()
        # Remove requests older than 1 minute
        while self.requests and self.requests[0] < now - 60:
            self.requests.popleft()
        
        if len(self.requests) >= self.rate_limit:
            return False
        
        self.requests.append(now)
        return True
```

### Caching

```python
from functools import lru_cache

class Tools:
    @lru_cache(maxsize=100)
    def cached_operation(self, input_data: str) -> str:
        # Expensive operation
        return process(input_data)
```

## Resources

- [Open WebUI Documentation](https://docs.openwebui.com)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [Pydantic Documentation](https://docs.pydantic.dev/)

## Need Help?

- Check the [examples](../examples/) directory
- Review existing tools in [tools](../tools/) directory
- Open an issue if you're stuck
