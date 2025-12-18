# OpenWebUI Tools API Reference

Quick reference for OpenWebUI tool development.

## Tool Structure

### Minimal Tool

```python
"""
title: Tool Name
author: Author Name
author_url: https://github.com/username
description: Brief description
required_open_webui_version: 0.3.0
version: 1.0.0
license: MIT
"""

class Tools:
    def __init__(self):
        pass
    
    def method_name(self, prompt: str) -> str:
        return "result"
```

## Metadata Fields

### Required in Docstring

| Field | Description | Example |
|-------|-------------|---------|
| `title` | Tool display name | `"Web Scraper"` |
| `author` | Creator's name | `"John Doe"` |
| `author_url` | Creator's URL | `"https://github.com/johndoe"` |
| `description` | What the tool does | `"Scrape data from websites"` |
| `required_open_webui_version` | Min version | `"0.3.0"` |
| `version` | Tool version | `"1.0.0"` |
| `license` | License type | `"MIT"` |

### Optional Fields

| Field | Description | Example |
|-------|-------------|---------|
| `requirements` | Python packages | `"requests, beautifulsoup4"` |

## Configuration (Valves)

### Basic Valve Definition

```python
from pydantic import BaseModel, Field

class Tools:
    class Valves(BaseModel):
        API_KEY: str = Field(
            default="",
            description="Your API key"
        )
    
    def __init__(self):
        self.valves = self.Valves()
```

### Valve Field Types

```python
# String
API_KEY: str = Field(default="", description="API key")

# Integer with constraints
MAX_RESULTS: int = Field(default=10, ge=1, le=100, description="Max results")

# Float with constraints
THRESHOLD: float = Field(default=0.5, ge=0.0, le=1.0, description="Threshold")

# Boolean
ENABLE_CACHE: bool = Field(default=True, description="Enable caching")

# List
ALLOWED_DOMAINS: list[str] = Field(default=[], description="Allowed domains")
```

## Method Signatures

### Basic Method

```python
def method_name(self, prompt: str) -> str:
    """Process input and return result"""
    return "result"
```

### With User Context

```python
def method_name(
    self,
    prompt: str,
    __user__: dict = {}
) -> str:
    """
    User dict contains:
    - id: User ID
    - name: User name
    - email: User email
    - role: User role
    """
    user_id = __user__.get("id")
    return f"User {user_id}: result"
```

### With Event Emitter

```python
async def method_name(
    self,
    prompt: str,
    __event_emitter__=None
) -> str:
    """Async method with progress updates"""
    if __event_emitter__:
        await __event_emitter__({
            "type": "status",
            "data": {"description": "Processing...", "done": False}
        })
    
    result = await process(prompt)
    
    if __event_emitter__:
        await __event_emitter__({
            "type": "status",
            "data": {"description": "Done!", "done": True}
        })
    
    return result
```

### Complete Signature

```python
async def method_name(
    self,
    prompt: str,
    __user__: dict = {},
    __event_emitter__=None,
    **kwargs
) -> str:
    """Full featured method"""
    pass
```

## Event Emitter

### Event Types

#### Status Event
```python
await __event_emitter__({
    "type": "status",
    "data": {
        "description": "Processing step 1...",
        "done": False
    }
})
```

#### Message Event
```python
await __event_emitter__({
    "type": "message",
    "data": {
        "content": "Intermediate result..."
    }
})
```

#### Completion Event
```python
await __event_emitter__({
    "type": "status",
    "data": {
        "description": "Complete!",
        "done": True
    }
})
```

## Common Patterns

### Input Validation

```python
def validate(self, input_data: str) -> tuple[bool, str]:
    if not input_data:
        return False, "Input required"
    if len(input_data) > 10000:
        return False, "Input too long"
    return True, ""

def method(self, prompt: str) -> str:
    valid, error = self.validate(prompt)
    if not valid:
        return f"Error: {error}"
    # Process...
```

### Error Handling

```python
def method(self, prompt: str) -> str:
    try:
        result = process(prompt)
        return result
    except ValueError as e:
        return f"Invalid input: {str(e)}"
    except ConnectionError:
        return "Connection failed. Try again."
    except Exception as e:
        return f"Error: {str(e)}"
```

### Caching

```python
from functools import lru_cache

class Tools:
    @lru_cache(maxsize=100)
    def expensive_operation(self, key: str) -> str:
        # Cached result
        return process(key)
```

### Rate Limiting

```python
import time
from collections import deque

class Tools:
    def __init__(self):
        self.requests = deque()
        self.rate_limit = 10  # per minute
    
    def check_rate_limit(self) -> bool:
        now = time.time()
        # Remove old requests
        while self.requests and self.requests[0] < now - 60:
            self.requests.popleft()
        
        if len(self.requests) >= self.rate_limit:
            return False
        
        self.requests.append(now)
        return True
```

### Async HTTP Requests

```python
import httpx

async def fetch(self, url: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=10.0)
        response.raise_for_status()
        return response.json()
```

## Type Hints

### Common Types

```python
from typing import Optional, List, Dict, Union, Any, Callable

def method(
    data: str,                          # String
    count: int,                         # Integer
    ratio: float,                       # Float
    enabled: bool,                      # Boolean
    items: List[str],                   # List of strings
    config: Dict[str, Any],             # Dictionary
    callback: Optional[Callable],        # Optional function
    result: Union[str, int]             # String or int
) -> Dict[str, List[str]]:              # Returns dict
    pass
```

## Import Statements

### Common Imports

```python
# Type hints
from typing import Optional, List, Dict, Any, Callable

# Pydantic for Valves
from pydantic import BaseModel, Field

# Async HTTP
import httpx

# Standard library
import re
import json
import time
from datetime import datetime
from functools import lru_cache
from collections import deque
```

## Return Types

### Formatted Text

```python
def method(self) -> str:
    return """# Heading

**Bold text** and *italic text*

- List item 1
- List item 2

`code snippet`
"""
```

### JSON String

```python
import json

def method(self) -> str:
    data = {"key": "value", "items": [1, 2, 3]}
    return json.dumps(data, indent=2)
```

### Error Messages

```python
def method(self) -> str:
    if error:
        return "❌ Error: Something went wrong"
    return "✅ Success: Operation completed"
```

## Best Practices Summary

1. ✅ Always validate inputs
2. ✅ Handle errors gracefully
3. ✅ Use type hints
4. ✅ Document your code
5. ✅ Never hardcode secrets
6. ✅ Use Valves for configuration
7. ✅ Provide helpful error messages
8. ✅ Use async for I/O operations
9. ✅ Emit progress for long operations
10. ✅ Test thoroughly

## Resources

- [Development Guide](DEVELOPMENT.md)
- [Best Practices](BEST_PRACTICES.md)
- [Examples](../examples/)
- [Templates](../templates/)
