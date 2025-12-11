# Cursor & Agent Settings Recommendations for MLS Comp Bot

Based on your project structure and patterns, here are recommended Cursor settings:

## Recommended Cursor Settings

### 1. **Agent Settings** (Cursor Settings → Agent)

#### Model Selection
- **Primary Model**: Use Claude Sonnet 4.5 or GPT-4 for complex API integration tasks
- **Fallback**: GPT-3.5 for simpler tasks
- **Reason**: Your project involves complex API integrations, HTML parsing, and data extraction that benefit from stronger models

#### Context Window
- **Enable**: "Use full context window"
- **Reason**: Your codebase has many files and the bot needs to understand relationships between:
  - `bot.py` (orchestration)
  - `attom_connector.py` (ATTOM API)
  - `alternative_apis.py` (multiple APIs)
  - `models.py` (data structures)
  - `app.py` (Flask routes)

#### Codebase Indexing
- **Enable**: "Index codebase for better context"
- **Reason**: Helps the agent understand:
  - API fallback chains
  - Data flow from API → Property model → Web interface
  - Error handling patterns
  - Validation functions

### 2. **Editor Settings** (Cursor Settings → Editor)

#### Auto-Complete
- **Enable**: "Show inline suggestions"
- **Suggestion Delay**: 100ms
- **Reason**: Helps with consistent patterns (API calls, error handling, logging)

#### Code Actions
- **Enable**: "Suggest on type"
- **Enable**: "Auto-import"
- **Reason**: Your project uses many imports (requests, BeautifulSoup, Pydantic, Flask)

### 3. **AI Chat Settings**

#### Chat Behavior
- **Context Awareness**: "Full project context"
- **Code References**: "Include file paths"
- **Reason**: When discussing API issues, the agent needs to see:
  - Which connector is being used
  - How data flows through the system
  - What error handling exists

#### Response Style
- **Verbosity**: "Detailed" (for complex API issues)
- **Code Examples**: "Always include"
- **Reason**: API integration requires understanding of:
  - Request/response formats
  - Error handling
  - Fallback logic

### 4. **File-Specific Settings**

#### Python Files
- **Linter**: Pylint or Ruff (for type checking)
- **Formatter**: Black or autopep8
- **Type Checking**: Enable mypy hints
- **Reason**: Your code uses type hints extensively (Pydantic models, function signatures)

#### HTML/JavaScript Files
- **Linter**: ESLint
- **Formatter**: Prettier
- **Reason**: `templates/index.html` has inline JavaScript that should be consistent

### 5. **Project-Specific Recommendations**

#### Create `.cursorrules` File
I've created a `.cursorrules` file with project-specific guidelines. This helps the agent:
- Understand your API fallback patterns
- Know which validation functions to use
- Follow your error handling conventions
- Use consistent logging patterns

#### Ignore Patterns (`.cursorignore`)
Add these to avoid indexing unnecessary files:
```
# Test files (unless debugging)
test_*.py
*_test.py

# Logs
*.log
flask_app.log

# Debug files
*_debug.json
*_results.txt

# Reports (generated)
reports/*.pdf

# Cache
__pycache__/
*.pyc
```

#### Workspace Settings (`.vscode/settings.json`)
```json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "python.analysis.typeCheckingMode": "basic",
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true
  },
  "files.associations": {
    "*.html": "html"
  }
}
```

## Agent Behavior Recommendations

### When Working on API Integration
- **Always check**: Which API is being used (ATTOM, Estated, Oxylabs)
- **Always verify**: API is enabled in settings before calling
- **Always implement**: Fallback chain logic
- **Always validate**: Extracted data before using

### When Working on Data Extraction
- **Always use**: Validation helper functions (`_is_valid_cooling_type`, etc.)
- **Always filter**: Invalid placeholder values
- **Always log**: What was extracted for debugging
- **Always handle**: Missing data gracefully (None is acceptable)

### When Working on Web Interface
- **Always include**: All Property model fields in JSON responses
- **Always filter**: Invalid values in frontend JavaScript
- **Always show**: Loading states for long operations
- **Always handle**: API errors gracefully

## Suggested Workflow

1. **Before making changes**: Ask the agent to review related files
2. **When adding API calls**: Ask the agent to check existing patterns
3. **When extracting data**: Ask the agent to verify validation logic
4. **When debugging**: Ask the agent to check logs and error handling

## Quick Commands for Agent

- "Check the API fallback chain for [property field]"
- "Show me how [API] handles errors"
- "What validation is applied to [data field]?"
- "How does the web interface display [field]?"
- "Review the error handling in [file]"

## Summary

Your project benefits from:
- ✅ Full context awareness (many interconnected files)
- ✅ Strong model selection (complex API logic)
- ✅ Codebase indexing (understand patterns)
- ✅ Type checking (Pydantic models)
- ✅ Detailed responses (API integration complexity)

The `.cursorrules` file I created will help guide the agent to follow your project's patterns and conventions.

