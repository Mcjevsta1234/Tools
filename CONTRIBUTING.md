# Contributing to OpenWebUI Tools

Thank you for your interest in contributing to the OpenWebUI Tools repository! This document provides guidelines and instructions for contributing.

## 🎯 Types of Contributions

We welcome several types of contributions:

1. **New Tools** - Submit your custom OpenWebUI tools
2. **Tool Improvements** - Enhance existing tools
3. **Bug Fixes** - Fix issues in existing tools
4. **Documentation** - Improve documentation and guides
5. **Examples** - Add helpful examples and tutorials

## 📋 Before You Start

1. **Check existing tools** - Make sure your tool doesn't duplicate existing functionality
2. **Review the templates** - Use the tool templates in `templates/` directory
3. **Read the documentation** - Familiarize yourself with the development guidelines

## 🔧 Submitting a New Tool

### 1. Tool Requirements

Your tool should:
- ✅ Follow the OpenWebUI tool structure
- ✅ Include clear documentation
- ✅ Have descriptive names and descriptions
- ✅ Handle errors gracefully
- ✅ Include example usage
- ✅ Be well-commented
- ✅ Follow security best practices

### 2. Tool Structure

```python
"""
title: Tool Name
author: Your Name
author_url: https://github.com/yourusername
description: Brief description of what the tool does
required_open_webui_version: 0.3.0
version: 1.0.0
license: MIT
"""

class Tools:
    def __init__(self):
        pass
    
    # Your tool methods here
```

### 3. File Organization

Place your tool in the appropriate category:
- `tools/productivity/` - Productivity tools
- `tools/web/` - Web-related tools
- `tools/data/` - Data processing tools
- `tools/utilities/` - General utilities
- `tools/integrations/` - Third-party integrations

### 4. Naming Convention

- Use descriptive, lowercase filenames with underscores
- Example: `web_scraper.py`, `calculator_advanced.py`

### 5. Documentation

Each tool should include:
- Clear title and description in the docstring
- Usage examples in comments
- Parameter descriptions
- Return value documentation
- Any API keys or configuration needed

## 🐛 Reporting Issues

When reporting issues:
1. Check if the issue already exists
2. Provide a clear description
3. Include steps to reproduce
4. Specify the Open WebUI version
5. Share relevant error messages

## 📝 Pull Request Process

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-tool`)
3. **Add your tool** in the appropriate category
4. **Update README.md** if adding a new category
5. **Commit your changes** (`git commit -m 'Add amazing tool'`)
6. **Push to your fork** (`git push origin feature/amazing-tool`)
7. **Open a Pull Request**

### PR Guidelines

- Provide a clear title and description
- Reference any related issues
- Include screenshots or examples if applicable
- Ensure your code follows the style guidelines
- Update documentation as needed

## ✅ Code Style

- Use clear, descriptive variable names
- Add comments for complex logic
- Follow PEP 8 for Python code
- Keep functions focused and single-purpose
- Handle errors gracefully

## 🔒 Security Guidelines

- Never hardcode API keys or secrets
- Validate and sanitize all inputs
- Be cautious with external API calls
- Document any security considerations
- Follow the principle of least privilege

## 📖 Documentation Standards

- Write clear, concise documentation
- Include code examples
- Explain parameters and return values
- Document any prerequisites or dependencies
- Keep documentation up-to-date

## 🧪 Testing

Before submitting:
1. Test your tool in Open WebUI
2. Verify all features work as expected
3. Test error handling
4. Check with different input types
5. Ensure no conflicts with other tools

## 💬 Getting Help

If you need help:
- Check the [documentation](docs/)
- Review existing tools for examples
- Open an issue with your question
- Be specific about what you're trying to achieve

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## 🙏 Thank You!

Your contributions help make this repository valuable for the entire Open WebUI community!
