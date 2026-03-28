# Smart To-Do List - PRD Manager (Pro Edition)

A professional-grade, modular task management application for Linux, engineered specifically for Product Requirements Documents (PRD) and technical project management.

## 🚀 Advanced Features

### 📄 Professional Export
- **Markdown PRD**: Export your entire project as a structured Markdown document, grouped by section with checklist progress and status icons.
- **Plain Text Reports**: Generate quick summary reports for stakeholders or meetings.
- **Native File Dialog**: Integrated Linux file chooser for saving documents anywhere.

### 📅 Roadmap View
- **Timeline Projection**: Automatically groups requirements by their due date month.
- **Visual Strategy**: See how your project evolves over months or view what's in the "Backlog".

### 🗺️ Planning View
- **PRD Sectioning**: Groups tasks by their PRD category (e.g., Requirements, Design, Testing).
- **Structure-First**: Perfect for ensuring every section of your PRD is being actively addressed.

### 📝 Markdown Requirements
- **Formatted Specifications**: Use standard Markdown (`**bold**`, `*italic*`, `` `code` ``) in task descriptions.
- **Live Preview**: Toggle between an editor and a formatted Pango-markup preview.

### 📋 Sub-task Checklists
- **Granular Tracking**: Break down large PRD sections into actionable sub-tasks.
- **Progress Visualization**: View completion status directly in the main task list.

### 🧘 Focus Mode & Pomodoro
- **Distraction-Free Writing**: Hide the task list to focus exclusively on the current requirement.
- **Built-in Timer**: Integrated 25-minute Pomodoro timer.

### 📜 Audit Log (Audit Trail)
- **Version History**: Every change to a task's status, priority, or description is automatically logged.

## 🛠️ Project Architecture

- `smart_todo.py`: UI orchestration with `Adw.ViewStack` and `Adw.ViewSwitcher`.
- `export_utils.py`: Logic for generating document formats (MD, TXT).
- `models.py`: Data definitions.
- `database.py`: SQLite layer with audit logging.
- `widgets.py`: Custom components including `RoadmapView`, `PlanningView`, and `AddTaskWindow`.

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
1. Select a requirement from the list.
2. Toggle **Focus** in the header.
3. The sidebar will disappear, and the Pomodoro timer will begin.

---
**Smart To-Do List** - Engineered for clarity, built for focus.
