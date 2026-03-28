#!/usr/bin/env python3
"""
Smart To-Do List Application
Main application entry point with Roadmap and Planning
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Gio, GLib, Adw

import sys
import os
from models import Task, TaskFilter, Status, Priority
from database import Database
from widgets import (
    TaskRowWidget, TaskDetailWidget, StatsWidget, 
    RoadmapView, PlanningView, AddTaskWindow
)
from export_utils import PRDExporter

Adw.init()

class SmartTodoApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.example.smarttodo", flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.db = Database()
        self.current_filter = TaskFilter()
        self.pomodoro_seconds = 25 * 60
        self.timer_id = None
        
    def do_activate(self):
        self.window = Adw.ApplicationWindow(application=self)
        self.window.set_title("PRD Manager & Roadmap")
        self.window.set_default_size(1200, 800)
        
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.window.set_content(self.main_box)
        
        self.create_header_bar()
        self.create_main_content()
        self.refresh_all_views()
        self.window.present()

    def create_header_bar(self):
        self.header = Adw.HeaderBar()
        self.main_box.append(self.header)
        
        # Add Task Button
        add_btn = Gtk.Button.new_from_icon_name("list-add-symbolic")
        add_btn.set_tooltip_text("Add Requirement")
        add_btn.connect("clicked", self.show_add_task_dialog)
        self.header.pack_start(add_btn)
        
        # Focus Mode Toggle
        self.focus_btn = Gtk.ToggleButton(label="Focus")
        self.focus_btn.connect("toggled", self.on_focus_toggled)
        self.header.pack_start(self.focus_btn)
        
        # Timer Label
        self.timer_label = Gtk.Label(label="25:00")
        self.timer_label.set_margin_start(10)
        self.header.pack_start(self.timer_label)

        # Export Button
        export_btn = Gtk.Button.new_from_icon_name("document-save-symbolic")
        export_btn.set_tooltip_text("Export PRD")
        export_btn.connect("clicked", self.on_export_clicked)
        self.header.pack_end(export_btn)

        # View Switcher (Middle)
        self.view_switcher = Adw.ViewSwitcher()
        self.header.set_title_widget(self.view_switcher)

    def create_main_content(self):
        self.stack = Adw.ViewStack()
        self.view_switcher.set_stack(self.stack)
        self.main_box.append(self.stack)
        
        # 1. Tasks View (List + Details)
        self.paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        self.paned.set_position(350)
        
        self.list_scroll = Gtk.ScrolledWindow()
        self.task_list = Gtk.ListBox()
        self.task_list.connect("row-activated", self.on_task_selected)
        self.list_scroll.set_child(self.task_list)
        self.paned.set_start_child(self.list_scroll)
        
        self.detail_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.paned.set_end_child(self.detail_container)
        
        tasks_page = self.stack.add_titled(self.paned, "tasks", "Tasks")
        tasks_page.set_icon_name("format-list-bulleted-symbolic")
        
        # 2. Roadmap View
        self.roadmap_view = RoadmapView(self.db)
        roadmap_page = self.stack.add_titled(self.roadmap_view, "roadmap", "Roadmap")
        roadmap_page.set_icon_name("appointment-soon-symbolic")
        
        # 3. Planning View
        self.planning_view = PlanningView(self.db)
        planning_page = self.stack.add_titled(self.planning_view, "planning", "Plan")
        planning_page.set_icon_name("view-grid-symbolic")
        
        # 4. Dashboard View
        self.stats_view = StatsWidget(self.db)
        dash_page = self.stack.add_titled(self.stats_view, "dash", "Dashboard")
        dash_page.set_icon_name("org.gnome.Usage-symbolic")

    def on_export_clicked(self, _):
        """Handle PRD export with file chooser"""
        dialog = Gtk.FileChooserNative(
            title="Export PRD Document",
            transient_for=self.window,
            action=Gtk.FileChooserAction.SAVE,
            accept_label="_Save",
            cancel_label="_Cancel"
        )
        
        # Add filters
        filter_md = Gtk.FileFilter()
        filter_md.set_name("Markdown (.md)")
        filter_md.add_pattern("*.md")
        dialog.add_filter(filter_md)
        
        filter_txt = Gtk.FileFilter()
        filter_txt.set_name("Plain Text (.txt)")
        filter_txt.add_pattern("*.txt")
        dialog.add_filter(filter_txt)
        
        dialog.set_current_name("Product_Requirements_Document.md")
        dialog.connect("response", self.on_export_response)
        dialog.show()

    def on_export_response(self, dialog, response_id):
        if response_id == Gtk.ResponseType.ACCEPT:
            file = dialog.get_file()
            if not file:
                return
            
            file_path = file.get_path()
            tasks = self.db.get_all_tasks()
            
            if file_path.endswith(".md"):
                content = PRDExporter.generate_markdown(tasks)
            else:
                content = PRDExporter.generate_text(tasks)
                
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                
                toast = Adw.Toast.new(f"Exported to {os.path.basename(file_path)}")
                self.window.add_toast(toast)
            except Exception as e:
                print(f"Export error: {e}")
                toast = Adw.Toast.new(f"Export failed: {str(e)}")
                self.window.add_toast(toast)

    def on_focus_toggled(self, btn):
        active = btn.get_active()
        self.list_scroll.set_visible(not active)
        if active:
            self.start_pomodoro()
        else:
            self.stop_pomodoro()

    def start_pomodoro(self):
        self.pomodoro_seconds = 25 * 60
        self.timer_id = GLib.timeout_add_seconds(1, self.update_timer)

    def stop_pomodoro(self):
        if self.timer_id:
            GLib.source_remove(self.timer_id)
            self.timer_id = None
        self.timer_label.set_text("25:00")

    def update_timer(self):
        if self.pomodoro_seconds <= 0:
            self.timer_label.set_text("Break!")
            return False
        self.pomodoro_seconds -= 1
        mins, secs = divmod(self.pomodoro_seconds, 60)
        self.timer_label.set_text(f"{mins:02d}:{secs:02d}")
        return True

    def refresh_all_views(self):
        self.refresh_task_list()
        self.roadmap_view.refresh()
        self.planning_view.refresh()
        self.stats_view.refresh()

    def refresh_task_list(self):
        while row := self.task_list.get_first_child():
            self.task_list.remove(row)
        tasks = self.db.get_all_tasks(self.current_filter)
        for task in tasks:
            self.task_list.append(TaskRowWidget(task, on_toggle=self.on_task_toggled))

    def on_task_toggled(self, task_id, completed):
        task = self.db.get_task(task_id)
        task.status = Status.COMPLETED if completed else Status.PENDING
        self.db.update_task(task)
        self.refresh_all_views()

    def on_task_selected(self, listbox, row):
        while child := self.detail_container.get_first_child():
            self.detail_container.remove(child)
        detail = TaskDetailWidget(row.task, self.db, on_update=self.refresh_all_views)
        self.detail_container.append(detail)

    def show_add_task_dialog(self, _):
        dialog = AddTaskWindow(self.window, self.db, on_save=self.refresh_all_views)
        dialog.present()

    def do_shutdown(self):
        self.db.close()
        super().do_shutdown()

if __name__ == "__main__":
    app = SmartTodoApp()
    app.run(sys.argv)
