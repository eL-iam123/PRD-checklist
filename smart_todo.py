#!/usr/bin/env python3
"""
Smart To-Do List Application
Main application entry point with Focus Mode and Pomodoro
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Gio, GLib, Adw

import sys
from models import Task, TaskFilter, Status, Priority
from database import Database
from widgets import TaskRowWidget, TaskDetailWidget, StatsWidget

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
        self.window.set_title("Smart To-Do List - PRD Manager")
        self.window.set_default_size(1200, 800)
        
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.window.set_content(self.main_box)
        
        self.create_header_bar()
        self.create_main_content()
        self.refresh_task_list()
        self.window.present()

    def create_header_bar(self):
        header = Adw.HeaderBar()
        self.main_box.append(header)
        
        # Add Task
        add_btn = Gtk.Button.new_from_icon_name("list-add-symbolic")
        add_btn.connect("clicked", self.show_add_task_dialog)
        header.pack_start(add_btn)
        
        # Focus Mode Toggle
        self.focus_btn = Gtk.ToggleButton(label="Focus Mode")
        self.focus_btn.connect("toggled", self.on_focus_toggled)
        header.pack_start(self.focus_btn)
        
        # Pomodoro Timer Label
        self.timer_label = Gtk.Label(label="25:00")
        self.timer_label.set_margin_start(10)
        header.pack_start(self.timer_label)

        # Dashboard
        self.dash_btn = Gtk.ToggleButton(label="Dashboard")
        self.dash_btn.connect("toggled", self.on_dash_toggled)
        header.pack_end(self.dash_btn)

    def create_main_content(self):
        self.stack = Gtk.Stack()
        self.main_box.append(self.stack)
        
        # Tasks Paned View
        self.paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        self.paned.set_position(350)
        
        # Left: List
        self.list_box_container = Gtk.ScrolledWindow()
        self.task_list = Gtk.ListBox()
        self.task_list.connect("row-activated", self.on_task_selected)
        self.list_box_container.set_child(self.task_list)
        self.paned.set_start_child(self.list_box_container)
        
        # Right: Details
        self.detail_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.paned.set_end_child(self.detail_container)
        
        self.stack.add_named(self.paned, "tasks")
        
        # Dashboard View
        self.stats_view = StatsWidget(self.db)
        self.stack.add_named(self.stats_view, "dash")

    def on_focus_toggled(self, btn):
        active = btn.get_active()
        self.list_box_container.set_visible(not active)
        if active:
            self.start_pomodoro()
            self.window.add_css_class("focus-mode")
        else:
            self.stop_pomodoro()
            self.window.remove_css_class("focus-mode")

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
        self.refresh_task_list()

    def on_task_selected(self, listbox, row):
        while child := self.detail_container.get_first_child():
            self.detail_container.remove(child)
        detail = TaskDetailWidget(row.task, self.db, on_update=self.refresh_task_list)
        self.detail_container.append(detail)

    def on_dash_toggled(self, btn):
        self.stack.set_visible_child_name("dash" if btn.get_active() else "tasks")
        if btn.get_active(): self.stats_view.refresh()

    def show_add_task_dialog(self, _):
        # Implementation of add task dialog (simplified)
        task = Task(title="New Requirement", description="Details here...")
        self.db.add_task(task)
        self.refresh_task_list()

    def do_shutdown(self):
        self.db.close()
        super().do_shutdown()

if __name__ == "__main__":
    app = SmartTodoApp()
    app.run(sys.argv)
