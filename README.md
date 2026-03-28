# Smart To-Do List - PRD Manager (Pro Edition)

A professional-grade, modular task management application for Linux, engineered specifically for Product Requirements Documents (PRD) and technical project management.

## 🚀 Advanced Features

### 📝 Markdown Requirements
- **Formatted Specifications**: Use standard Markdown (`**bold**`, `*italic*`, `` `code` ``) in task descriptions.
- **Live Preview**: Toggle between an editor and a formatted Pango-markup preview to visualize complex requirements.

### 📋 Sub-task Checklists
- **Granular Tracking**: Break down large PRD sections into actionable sub-tasks.
- **Progress Visualization**: View completion status (e.g., `📋 3/5`) directly in the main task list.
- **In-place Management**: Add, complete, or remove sub-tasks without leaving the detail view.

### 🧘 Focus Mode & Pomodoro
- **Distraction-Free Writing**: Hide the task list to focus exclusively on the current requirement.
- **Built-in Timer**: Integrated 25-minute Pomodoro timer to manage deep work sessions.
- **UI Optimization**: Minimalist interface state designed for high-concentration drafting.

### 📜 Audit Log (Audit Trail)
- **Version History**: Every change to a task's status, priority, or description is automatically logged.
- **Git-style Tracking**: Know exactly what changed and when with a dedicated history pane.
- **Accountability**: Essential for maintaining a clear record of requirement evolution over time.

## 🛠️ Project Architecture

The program follows a clean, modular architecture for maximum maintainability:
- `smart_todo.py`: Application lifecycle and UI orchestration.
- `models.py`: Strict data definitions using Python `dataclasses`.
- `database.py`: SQLite layer with automated schema migrations and audit logging.
- `widgets.py`: Reusable custom GTK4/Adwaita components for checklists, history, and markdown.

## 📦 Installation

### Prerequisites
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1 libsqlite3-dev
```

### Setup
```bash
chmod +x smart_todo.py
./smart_todo.py
```

## ⌨️ Focus Mode Usage
1. Select a complex requirement from the list.
2. Toggle **Focus Mode** in the header.
3. The sidebar will disappear, and the Pomodoro timer will begin.
4. Use the **Preview** toggle to review your formatted PRD specification.

## 🤝 Contributing
Contributions are welcome! Please ensure all UI changes are implemented as reusable widgets in `widgets.py` and data schema changes include migrations in `database.py`.

---
**Smart To-Do List** - Engineered for clarity, built for focus.
