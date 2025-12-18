"""
title: Text Analyzer
author: OpenWebUI Tools
author_url: https://github.com/open-webui
description: Analyze text to count words, characters, sentences, and provide statistics
required_open_webui_version: 0.3.0
version: 1.0.0
license: MIT
"""

import re
from typing import Optional, Callable, Any


class Tools:
    """
    Text analysis tool that provides statistics about input text.
    """

    def __init__(self):
        pass

    def analyze_text(
        self,
        text: str,
        __user__: dict = {},
        __event_emitter__: Optional[Callable[[dict], Any]] = None
    ) -> str:
        """
        Analyze text and return comprehensive statistics.

        Args:
            text: The text to analyze
            __user__: User information dictionary
            __event_emitter__: Optional event emitter

        Returns:
            str: Formatted analysis results
        """
        try:
            if not text or not isinstance(text, str):
                return "Error: Please provide text to analyze"

            # Calculate statistics
            char_count = len(text)
            char_no_spaces = len(text.replace(" ", "").replace("\n", "").replace("\t", ""))
            
            # Word count
            words = text.split()
            word_count = len(words)
            
            # Sentence count (approximate)
            sentences = re.split(r'[.!?]+', text)
            sentences = [s.strip() for s in sentences if s.strip()]
            sentence_count = len(sentences)
            
            # Line count
            lines = text.split('\n')
            line_count = len(lines)
            
            # Average word length
            avg_word_length = char_no_spaces / word_count if word_count > 0 else 0
            
            # Average words per sentence
            avg_words_per_sentence = word_count / sentence_count if sentence_count > 0 else 0
            
            # Find longest word
            longest_word = max(words, key=len) if words else ""
            
            # Paragraph count (double newlines)
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
            paragraph_count = len(paragraphs)

            # Format results
            result = f"""# Text Analysis Results

## Basic Statistics
- **Total Characters:** {char_count:,}
- **Characters (no spaces):** {char_no_spaces:,}
- **Words:** {word_count:,}
- **Sentences:** {sentence_count:,}
- **Lines:** {line_count:,}
- **Paragraphs:** {paragraph_count:,}

## Averages
- **Average Word Length:** {avg_word_length:.2f} characters
- **Average Words per Sentence:** {avg_words_per_sentence:.2f}

## Additional Info
- **Longest Word:** "{longest_word}" ({len(longest_word)} characters)
"""

            # Estimated reading time (average 200 words per minute)
            reading_time_minutes = word_count / 200
            if reading_time_minutes < 1:
                reading_time = f"{int(reading_time_minutes * 60)} seconds"
            else:
                reading_time = f"{reading_time_minutes:.1f} minutes"
            
            result += f"- **Estimated Reading Time:** {reading_time}\n"

            return result

        except Exception as e:
            return f"Error analyzing text: {str(e)}"
