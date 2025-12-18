# Examples

This directory contains example tools to help you get started with OpenWebUI tool development.

## Available Examples

### 1. Calculator (`calculator.py`)
A simple calculator that performs basic arithmetic operations.

**Features:**
- Addition, subtraction, multiplication, division
- Support for parentheses and order of operations
- Input validation and error handling
- Safe expression evaluation

**Usage:**
```
calculate("2 + 2")
calculate("(10 + 5) * 2")
calculate("100 / 4")
```

### 2. Text Analyzer (`text_analyzer.py`)
Analyzes text and provides comprehensive statistics.

**Features:**
- Character, word, sentence counting
- Average word length and sentence length
- Reading time estimation
- Longest word detection
- Paragraph and line counting

**Usage:**
```
analyze_text("Your text here...")
```

## Learning Path

1. **Start Simple** - Look at `calculator.py` to understand basic tool structure
2. **Add Complexity** - Study `text_analyzer.py` to see more advanced features
3. **Use Templates** - Check the `templates/` directory for starting points
4. **Read Documentation** - Review `docs/DEVELOPMENT.md` for detailed guidance

## Testing Examples

You can test these examples in Open WebUI:

1. Copy the entire tool code
2. Go to Open WebUI → Settings → Tools
3. Click "Add Tool" or "+"
4. Paste the code and save
5. Try using the tool in a chat!

## Modifying Examples

Feel free to modify these examples to learn:
- Add new features
- Change the output format
- Add configuration options (Valves)
- Implement async operations
- Add progress indicators

## Next Steps

After understanding these examples:
1. Browse the `templates/` directory for tool templates
2. Read `docs/BEST_PRACTICES.md` for quality guidelines
3. Check `docs/DEVELOPMENT.md` for comprehensive development guide
4. Create your own tool and share it!

## Contributing

Found a bug or have an improvement? See [CONTRIBUTING.md](../CONTRIBUTING.md) for how to contribute.
