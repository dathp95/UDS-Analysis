PROJECT RULES

Architecture
GUI → Controller → Service → Core → Utils
You are also a Senior PySide6 UI Architect.


Before every function, generate a task header.

The header must contain:

- Function name
- Purpose
- Inputs
- Outputs
- Called by
- Calls
- Side effects
- Responsibility
- Limitations

Never omit this header.

Every function must explicitly state what it DOES NOT DO.

Example:

Responsibility:
    Parse BLF frames.

Does NOT:
    - Decode ISO-TP.
    - Build transactions.
    - Export Excel.
    - Update GUI.


Function Rules
- One function = one responsibility.
- Maximum 40 lines.
- Maximum 3 nesting levels.
- Use descriptive names.
- Add type hints.
- Add docstrings.

Main
- No business logic.
- No calculations.
- No parsing.
- Only initialize and call modules.

Controller
- Coordinate workflow only.
- Never parse BLF.
- Never calculate response time.
- Never export Excel.

Core
- Contains all business logic.

Services
- Combine Core modules into complete workflows.

GUI
- No calculations.
- No file parsing.
- No Excel export.
- Only update UI and call Controller.

File Naming
*_parser.py
*_builder.py
*_service.py
*_manager.py
*_controller.py
*_window.py
*_widget.py
*_dialog.py

Coding Style
- PEP8
- snake_case
- DRY
- SOLID
- No duplicated code
- Use logging instead of print()

Before finishing
- Review architecture.
- Review function length.
- Review naming.
- Review code duplication.
- Refactor if needed.

Before implementing any GUI:

1. Explain the layout hierarchy.
2. List all widgets to be created.
3. List all new files.
4. Explain the responsibility of each widget.
5. Explain the signal flow.
6. Wait for approval before generating code.

Architecture
- MVC
- Modular
- Reusable widgets

MainWindow
- Create layouts only
- Create widgets only
- Connect signals only

Widgets
- One widget = one responsibility
- Independent and reusable

Controller
- Handle all business logic
- Handle all workflows

Core
- No GUI dependency

Layout
- Responsive
- Qt Layout only
- No fixed coordinates

Styling
- Windows 11 Fluent Design
- Rounded corners
- Light/Dark theme
- Centralized ThemeManager

Signals
- Use Qt Signal/Slot
- Widgets never call Controller directly

Folder Structure
gui/
widgets/
theme/
controllers/

Every new widget must be placed in its own file.

Do not create large classes.
Split responsibilities whenever appropriate.