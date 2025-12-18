# Testing Guide for OpenWebUI Tools

Guide for testing your OpenWebUI tools effectively.

## Manual Testing

### Pre-Testing Checklist

Before testing, ensure:
- [ ] All required metadata is present in docstring
- [ ] No hardcoded secrets or API keys
- [ ] Code follows Python syntax rules
- [ ] All imports are available in OpenWebUI
- [ ] Type hints are correct

### Testing in Open WebUI

1. **Copy your tool code**
2. **Open WebUI → Settings → Tools**
3. **Click "Add Tool" or "+"**
4. **Paste the code**
5. **Save the tool**
6. **Test in chat**

### Basic Test Cases

For every tool, test these scenarios:

#### 1. Normal Operation
```
Input: Valid, expected input
Expected: Correct output
```

#### 2. Empty Input
```
Input: "" or nothing
Expected: Error message or prompt for input
```

#### 3. Invalid Input Type
```
Input: Wrong type of data
Expected: Helpful error message
```

#### 4. Very Long Input
```
Input: Text > 10,000 characters
Expected: Error or truncation with warning
```

#### 5. Special Characters
```
Input: Text with special chars: @#$%^&*()
Expected: Proper handling or validation error
```

#### 6. Edge Cases
```
Input: Boundary values (0, -1, null, etc.)
Expected: Correct handling
```

## Test Scenarios by Tool Type

### API Integration Tools

Test:
- ✅ Valid API key
- ✅ Invalid API key
- ✅ Missing API key
- ✅ Rate limiting
- ✅ Network timeout
- ✅ API error responses
- ✅ Malformed responses

Example:
```python
# Test cases for a weather API tool
1. Valid city: "London" → Weather data
2. Invalid city: "XYZ123" → Error message
3. Empty API key → Configuration error
4. API timeout → Timeout error message
5. Invalid API key → Authentication error
```

### Text Processing Tools

Test:
- ✅ Short text (< 100 chars)
- ✅ Medium text (100-1000 chars)
- ✅ Long text (> 1000 chars)
- ✅ Empty string
- ✅ Only whitespace
- ✅ Special characters
- ✅ Unicode/Emoji
- ✅ Multiple languages

Example:
```python
# Test cases for a text analyzer
1. Normal text: "Hello world" → Analysis
2. Empty: "" → Error
3. Whitespace: "   " → Error
4. Unicode: "Hello 世界 🌍" → Analysis
5. Very long → Should handle or warn
```

### Calculation Tools

Test:
- ✅ Valid expressions
- ✅ Division by zero
- ✅ Very large numbers
- ✅ Very small numbers
- ✅ Invalid syntax
- ✅ Dangerous inputs
- ✅ Overflow scenarios

Example:
```python
# Test cases for a calculator
1. Simple: "2 + 2" → "4"
2. Complex: "(10 + 5) * 2" → "30"
3. Division by zero: "5 / 0" → Error
4. Invalid: "abc" → Error
5. Dangerous: "import os" → Rejected
```

### Data Format Tools

Test:
- ✅ Valid format
- ✅ Invalid format
- ✅ Partial format
- ✅ Empty data
- ✅ Corrupted data
- ✅ Large datasets

Example:
```python
# Test cases for JSON formatter
1. Valid JSON: '{"key": "value"}' → Formatted
2. Invalid JSON: '{key: value}' → Error
3. Empty: '' → Error
4. Nested: Complex object → Formatted
5. Large: 10MB JSON → Handle or warn
```

## Testing with Event Emitters

For async tools with progress updates:

```python
# Test that status updates work
async def test_progress():
    # Should see these messages:
    # 1. "Starting..."
    # 2. "Processing..."
    # 3. "Complete!"
    
    result = await tool.method("input")
```

## Error Testing

### Error Handling Checklist

- [ ] ValueError caught and handled
- [ ] TypeError caught and handled
- [ ] ConnectionError caught and handled
- [ ] TimeoutError caught and handled
- [ ] Generic Exception caught
- [ ] Error messages are user-friendly
- [ ] No stack traces shown to users

### Example Error Tests

```python
# Test error handling
def test_errors():
    # Test 1: ValueError
    result = tool.process("")
    assert "Error" in result
    
    # Test 2: Invalid type
    result = tool.process(123)  # Should be string
    assert "Error" in result
    
    # Test 3: Network error
    # (Mock network failure)
    result = tool.fetch_data()
    assert "connection" in result.lower()
```

## Performance Testing

### Response Time

Acceptable times:
- **Simple operations**: < 1 second
- **API calls**: < 5 seconds
- **Heavy processing**: < 30 seconds

### Memory Usage

Monitor for:
- Memory leaks
- Large data structures
- Caching issues

### Rate Limiting

Test:
- Multiple rapid requests
- Rate limit enforcement
- Rate limit messaging

## Security Testing

### Security Checklist

- [ ] No hardcoded secrets
- [ ] Input sanitization works
- [ ] No code injection possible
- [ ] External URLs validated
- [ ] File paths validated
- [ ] API keys in Valves only
- [ ] No sensitive data in logs

### Security Test Cases

```python
# Test 1: Code injection
input = "'; import os; os.system('rm -rf /')"
# Should be rejected or sanitized

# Test 2: Path traversal
input = "../../../etc/passwd"
# Should be validated

# Test 3: XSS attempt
input = "<script>alert('xss')</script>"
# Should be escaped or rejected
```

## Configuration Testing (Valves)

Test:
- ✅ Default values work
- ✅ Custom values work
- ✅ Invalid values rejected
- ✅ Required fields validated
- ✅ Validation constraints enforced

Example:
```python
# Test Valves
1. Default: No config → Uses defaults
2. Valid: Set valid API key → Works
3. Invalid: Empty required field → Error
4. Out of range: Value > max → Error
5. Wrong type: String for int → Error
```

## Regression Testing

After changes:
- ✅ All previous tests still pass
- ✅ New functionality works
- ✅ No new bugs introduced
- ✅ Performance not degraded

## Documentation Testing

Verify:
- ✅ Examples in docs work
- ✅ Usage instructions are clear
- ✅ All methods documented
- ✅ Parameter descriptions accurate
- ✅ Return values documented

## Test Documentation Template

```python
"""
Test Plan for [Tool Name]

Test Cases:
1. Basic Functionality
   - Input: "sample input"
   - Expected: "expected output"
   - Status: ✅ Pass

2. Error Handling
   - Input: ""
   - Expected: "Error: ..."
   - Status: ✅ Pass

3. Edge Case
   - Input: [edge case]
   - Expected: [expected behavior]
   - Status: ✅ Pass

Known Issues:
- None

Performance:
- Average response time: 0.5s
- Memory usage: Normal

Security:
- All inputs validated: ✅
- No code injection: ✅
- Secrets protected: ✅
"""
```

## Automated Testing (Advanced)

For complex tools, consider:

```python
# Simple test function
def run_tests():
    tests = [
        ("2 + 2", "4"),
        ("10 * 5", "50"),
        ("", "Error"),
    ]
    
    for input_val, expected in tests:
        result = tool.calculate(input_val)
        assert expected in result, f"Failed: {input_val}"
    
    print("All tests passed!")
```

## User Acceptance Testing

Before release:
- [ ] Tool solves the intended problem
- [ ] Instructions are clear
- [ ] Output is useful
- [ ] Error messages are helpful
- [ ] Performance is acceptable
- [ ] No critical bugs

## Testing Checklist Summary

- [ ] Normal operation works
- [ ] All error cases handled
- [ ] Input validation works
- [ ] Edge cases covered
- [ ] Security checks pass
- [ ] Performance acceptable
- [ ] Configuration works
- [ ] Documentation accurate
- [ ] Examples work
- [ ] User feedback positive

## Common Issues and Solutions

### Issue: Tool doesn't load
**Solution:** Check syntax, imports, and metadata

### Issue: Method not found
**Solution:** Verify method is in Tools class

### Issue: Import errors
**Solution:** Check package availability in OpenWebUI

### Issue: Slow performance
**Solution:** Use async, add caching, optimize logic

### Issue: Memory errors
**Solution:** Limit data size, use streaming

## Resources

- [Development Guide](DEVELOPMENT.md)
- [Best Practices](BEST_PRACTICES.md)
- [API Reference](API_REFERENCE.md)
- [Examples](../examples/)
