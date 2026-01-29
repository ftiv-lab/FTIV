---
description: Run tests using the project's standard Python 3.14 environment
---

To ensure tests run in the correct environment (Python 3.14), always use the virtual environment executable.

1. **Check Virtual Environment**:
   Ensure `.venv314` exists.

2. **Run Pytest**:
   Execute pytest by invoking the python executable in `.venv314` directly.
   
```powershell
.venv314\Scripts\python.exe -m pytest
```

3. **(Optional) Run Specific Test**:
   To run a specific test file:
```powershell
.venv314\Scripts\python.exe -m pytest path/to/test_file.py
```
// turbo-all
