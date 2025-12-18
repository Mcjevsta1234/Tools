# Templates

Tool templates to help you quickly create new OpenWebUI tools.

## Available Templates

### 1. Basic Tool (`basic_tool.py`)
The simplest starting point for creating a tool.

**Use when:**
- Creating a simple, single-purpose tool
- You don't need configuration options
- Your tool doesn't make async calls

**Features:**
- Minimal structure
- Basic error handling
- Simple input/output
- Well-documented

**Example use cases:**
- Simple text transformations
- Basic calculations
- String utilities
- Format converters

### 2. Advanced Tool (`advanced_tool.py`)
A comprehensive template with all common features.

**Use when:**
- You need configuration options (API keys, settings)
- Making async API calls
- Need progress updates for long operations
- Want caching or state management

**Features:**
- Valves (configuration) support
- Async/await pattern
- Event emitter for progress updates
- Input validation
- Caching functionality
- Comprehensive error handling

**Example use cases:**
- API integrations
- Web scraping
- File processing
- Database operations
- External service calls

## How to Use Templates

1. **Choose the right template** based on your needs
2. **Copy the template** to your tool file
3. **Update the metadata** in the docstring:
   - title
   - author
   - author_url
   - description
   - version
4. **Rename the class methods** to match your functionality
5. **Implement your logic** in the methods
6. **Test thoroughly** before sharing

## Template Comparison

| Feature | Basic Tool | Advanced Tool |
|---------|-----------|---------------|
| Configuration (Valves) | ❌ | ✅ |
| Async Support | ❌ | ✅ |
| Progress Updates | ❌ | ✅ |
| Caching | ❌ | ✅ |
| Input Validation | Basic | Comprehensive |
| Error Handling | Basic | Comprehensive |
| Complexity | Low | Medium |
| Learning Curve | Easy | Moderate |

## Customization Tips

### Adding Configuration (Valves)

```python
from pydantic import BaseModel, Field

class Tools:
    class Valves(BaseModel):
        YOUR_SETTING: str = Field(
            default="default_value",
            description="Description for users"
        )
    
    def __init__(self):
        self.valves = self.Valves()
```

### Adding Progress Updates

```python
async def your_method(self, prompt: str, __event_emitter__=None):
    if __event_emitter__:
        await __event_emitter__({
            "type": "status",
            "data": {"description": "Processing...", "done": False}
        })
    
    # Your code here
    
    if __event_emitter__:
        await __event_emitter__({
            "type": "status",
            "data": {"description": "Complete!", "done": True}
        })
```

### Adding Input Validation

```python
def validate_input(self, data: str) -> tuple[bool, str]:
    if not data:
        return False, "Input cannot be empty"
    if len(data) > 10000:
        return False, "Input too long"
    return True, ""
```

## Next Steps

1. **Review the examples** in `examples/` directory
2. **Read the development guide** at `docs/DEVELOPMENT.md`
3. **Check best practices** at `docs/BEST_PRACTICES.md`
4. **Start building** your tool!

## Need Help?

- Check the [examples](../examples/) for working implementations
- Read the [development guide](../docs/DEVELOPMENT.md)
- Review [best practices](../docs/BEST_PRACTICES.md)
- Open an issue if you're stuck

## Contributing

Have a template idea? See [CONTRIBUTING.md](../CONTRIBUTING.md) for how to contribute.
