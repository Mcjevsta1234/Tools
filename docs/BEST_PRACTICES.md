# Best Practices for OpenWebUI Tools

Guidelines for creating robust, secure, and user-friendly OpenWebUI tools.

## 🎯 General Principles

### 1. Single Responsibility
Each tool should do one thing well. If your tool is becoming complex, consider splitting it into multiple tools.

**Good:**
```python
class Tools:
    """Simple calculator for basic math operations"""
    def calculate(self, expression: str) -> float:
        # Single, focused purpose
```

**Avoid:**
```python
class Tools:
    """Calculator, weather, stocks, and translator"""
    # Too many unrelated features
```

### 2. User-Friendly Design
Make tools intuitive and easy to use.

```python
"""
title: Weather Checker
description: Get current weather for any city
"""

class Tools:
    def get_weather(self, city: str) -> str:
        """
        Get weather for a city
        
        Args:
            city: City name (e.g., "New York", "London")
        
        Returns:
            Weather information in readable format
        """
```

### 3. Fail Gracefully
Always handle errors and provide helpful messages.

```python
def process(self, input_data: str) -> str:
    try:
        if not input_data:
            return "Error: Please provide input data"
        
        result = self.perform_operation(input_data)
        return result
        
    except ValueError as e:
        return f"Invalid input: {str(e)}"
    except ConnectionError:
        return "Error: Unable to connect to service. Please try again later."
    except Exception as e:
        return f"Unexpected error: {str(e)}"
```

## 🔒 Security Best Practices

### 1. Never Hardcode Secrets

**Bad:**
```python
API_KEY = "sk-1234567890abcdef"  # Don't do this!
```

**Good:**
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

### 2. Validate All Inputs

```python
def process(self, user_input: str) -> str:
    # Validate type
    if not isinstance(user_input, str):
        return "Error: Input must be a string"
    
    # Validate length
    if len(user_input) > 10000:
        return "Error: Input too long (max 10000 characters)"
    
    # Sanitize input
    sanitized = user_input.strip()
    
    return self.safe_process(sanitized)
```

### 3. Be Careful with External APIs

```python
import httpx

async def safe_api_call(self, url: str) -> dict:
    # Validate URL
    if not url.startswith(("http://", "https://")):
        raise ValueError("Invalid URL")
    
    # Set timeout
    timeout = httpx.Timeout(10.0)
    
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            return {"error": "Request timed out"}
        except httpx.HTTPError as e:
            return {"error": f"HTTP error: {str(e)}"}
```

### 4. Limit Resource Usage

```python
class Tools:
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_REQUESTS_PER_MINUTE = 60
    
    def process_file(self, file_size: int) -> bool:
        if file_size > self.MAX_FILE_SIZE:
            raise ValueError("File too large")
        return True
```

## 📊 Performance Best Practices

### 1. Use Async for I/O Operations

```python
import httpx

class Tools:
    async def fetch_data(self, url: str) -> dict:
        """Use async for network calls"""
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            return response.json()
```

### 2. Cache When Appropriate

```python
from functools import lru_cache
import time

class Tools:
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
    
    def get_cached(self, key: str) -> any:
        if key in self.cache:
            data, timestamp = self.cache[key]
            if time.time() - timestamp < self.cache_ttl:
                return data
        return None
    
    def set_cache(self, key: str, value: any):
        self.cache[key] = (value, time.time())
```

### 3. Avoid Unnecessary Processing

```python
def process(self, data: str) -> str:
    # Early return for empty input
    if not data:
        return ""
    
    # Process only when needed
    if self.needs_processing(data):
        return self.expensive_operation(data)
    
    return data
```

## 📝 Code Quality

### 1. Use Type Hints

```python
from typing import Optional, List, Dict

def process_items(
    self,
    items: List[str],
    options: Optional[Dict[str, any]] = None
) -> Dict[str, List[str]]:
    """Type hints make code clearer and catch errors early"""
    if options is None:
        options = {}
    
    return {
        "processed": [item.upper() for item in items],
        "count": len(items)
    }
```

### 2. Write Clear Documentation

```python
def complex_method(
    self,
    input_data: str,
    threshold: float = 0.5,
    normalize: bool = True
) -> dict:
    """
    Process input data with advanced options.
    
    This method analyzes the input data and returns a structured
    result based on the specified threshold and normalization settings.
    
    Args:
        input_data: The text data to process
        threshold: Confidence threshold (0.0 to 1.0). Results below
                  this value will be filtered out.
        normalize: Whether to normalize the output values to 0-1 range
    
    Returns:
        Dictionary containing:
        - 'results': List of processed items
        - 'confidence': Average confidence score
        - 'metadata': Processing metadata
    
    Raises:
        ValueError: If threshold is not between 0 and 1
        
    Example:
        >>> tool = Tools()
        >>> result = tool.complex_method("test", threshold=0.7)
        >>> print(result['confidence'])
        0.85
    """
    if not 0 <= threshold <= 1:
        raise ValueError("Threshold must be between 0 and 1")
    
    # Implementation here
    pass
```

### 3. Keep Functions Small

```python
# Good: Small, focused functions
def validate_input(self, data: str) -> bool:
    return bool(data and len(data) < 10000)

def sanitize_input(self, data: str) -> str:
    return data.strip().lower()

def process(self, data: str) -> str:
    if not self.validate_input(data):
        return "Invalid input"
    
    sanitized = self.sanitize_input(data)
    return self.transform(sanitized)
```

## 🎨 User Experience

### 1. Provide Progress Updates

```python
async def long_operation(
    self,
    data: str,
    __event_emitter__=None
) -> str:
    steps = ["Parsing", "Processing", "Formatting", "Completing"]
    
    for i, step in enumerate(steps):
        if __event_emitter__:
            await __event_emitter__({
                "type": "status",
                "data": {
                    "description": f"{step}... ({i+1}/{len(steps)})",
                    "done": False
                }
            })
        
        await self.perform_step(step, data)
    
    if __event_emitter__:
        await __event_emitter__({
            "type": "status",
            "data": {"description": "Complete!", "done": True}
        })
    
    return "Operation completed successfully"
```

### 2. Return Formatted Output

```python
def get_results(self, query: str) -> str:
    results = self.search(query)
    
    # Format as readable text
    output = f"# Results for '{query}'\n\n"
    
    for i, result in enumerate(results, 1):
        output += f"{i}. **{result['title']}**\n"
        output += f"   {result['description']}\n\n"
    
    return output
```

### 3. Handle Edge Cases

```python
def divide(self, a: float, b: float) -> str:
    if b == 0:
        return "Error: Cannot divide by zero"
    
    result = a / b
    
    # Handle very large/small results
    if abs(result) > 1e10:
        return f"Result: {result:.2e} (scientific notation)"
    
    return f"Result: {result:.4f}"
```

## 🧪 Testing Guidelines

### Manual Test Checklist

For each tool, test:
- ✅ Normal operation with valid input
- ✅ Empty input
- ✅ Very long input
- ✅ Special characters in input
- ✅ Missing configuration (empty valves)
- ✅ Invalid configuration values
- ✅ Network failures (if applicable)
- ✅ Rate limits (if applicable)

### Test Example Scenarios

```python
# Create test scenarios in your tool comments
"""
Test Scenarios:
1. Normal: calculate("2 + 2") -> "4"
2. Complex: calculate("(5 + 3) * 2") -> "16"
3. Invalid: calculate("abc") -> "Error: Invalid expression"
4. Empty: calculate("") -> "Error: Please provide an expression"
"""
```

## 📚 Documentation Standards

### Tool Docstring Template

```python
"""
title: Tool Name
author: Your Name
author_url: https://github.com/yourusername
description: One-line description of what the tool does
required_open_webui_version: 0.3.0
version: 1.0.0
license: MIT
requirements: requests, beautifulsoup4
"""
```

### README for Complex Tools

For complex tools, include a README in comments:

```python
"""
# Tool Name

## Description
Detailed description of what the tool does and why it's useful.

## Configuration
- API_KEY: Your API key from provider.com
- MAX_RESULTS: Maximum number of results to return (default: 10)

## Usage Examples
1. Basic usage: method("input")
2. Advanced: method("input", option=True)

## Notes
- Requires API key from provider.com
- Rate limited to 100 requests/hour
- Results are cached for 5 minutes
"""
```

## ✅ Pre-Submission Checklist

Before submitting your tool:

- [ ] All secrets are in Valves
- [ ] Error handling is comprehensive
- [ ] Input validation is thorough
- [ ] Documentation is complete
- [ ] Code has type hints
- [ ] Tool is tested with various inputs
- [ ] Performance is acceptable
- [ ] No security vulnerabilities
- [ ] Code is well-commented
- [ ] Follows repository structure

## 🚀 Going Further

### Advanced Patterns

See the [examples](../examples/) directory for advanced patterns including:
- State management
- Multi-step workflows
- Complex data processing
- API integrations
- File handling

### Resources

- [Python Best Practices](https://docs.python-guide.org/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Async Python Guide](https://realpython.com/async-io-python/)
