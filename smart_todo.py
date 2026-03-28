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
    RoadmapView, PlanningView, AddTaskWindow,
    OnboardingWidget, EmptySelectionWidget
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
        self.window.set_title("PRD Manager & Engineering Suite")
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
        
        # Add Requirement Button
        add_btn = Gtk.Button.new_from_icon_name("list-add-symbolic")
        add_btn.set_tooltip_text("Draft a new functional requirement")
        add_btn.connect("clicked", self.show_add_task_dialog)
        self.header.pack_start(add_btn)
        
        # Focus Mode Toggle
        self.focus_btn = Gtk.ToggleButton(label="Focus")
        self.focus_btn.set_tooltip_text("Deep work mode: hides distractions and starts a timer")
        self.focus_btn.connect("toggled", self.on_focus_toggled)
        self.header.pack_start(self.focus_btn)
        
        # Timer Label
        self.timer_label = Gtk.Label(label="25:00")
        self.timer_label.set_margin_start(10)
        self.header.pack_start(self.timer_label)

        # Export Button
        export_btn = Gtk.Button.new_from_icon_name("document-save-symbolic")
        export_btn.set_tooltip_text("Export entire project as a professional PRD (.md or .txt)")
        export_btn.connect("clicked", self.on_export_clicked)
        self.header.pack_end(export_btn)

        # View Switcher (Middle)
        self.view_switcher = Adw.ViewSwitcher()
        self.header.set_title_widget(self.view_switcher)

    def create_main_content(self):
        self.main_stack = Gtk.Stack()
        self.main_box.append(self.main_stack)

        # 1. Onboarding (Welcome)
        self.onboarding = OnboardingWidget(self.show_add_task_dialog)
        self.main_stack.add_named(self.onboarding, "welcome")

        # 2. Main App View Stack
        self.app_stack = Adw.ViewStack()
        self.view_switcher.set_stack(self.app_stack)
        self.main_stack.add_named(self.app_stack, "app")
        
        # --- REQUIREMENTS PAGE ---
        self.paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        self.paned.set_position(350)
        
        # Sidebar
        self.sidebar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sidebar_label = Gtk.Label(label="Requirements Index")
        sidebar_label.set_margin_top(10)
        sidebar_label.set_margin_bottom(10)
        sidebar_label.get_style_context().add_class("dim-label")
        self.sidebar_box.append(sidebar_label)

        self.list_scroll = Gtk.ScrolledWindow()
        self.task_list = Gtk.ListBox()
        self.task_list.connect("row-activated", self.on_task_selected)
        self.list_scroll.set_child(self.task_list)
        self.sidebar_box.append(self.list_scroll)
        self.paned.set_start_child(self.sidebar_box)
        
        # Details Pane
        self.detail_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.empty_selection = EmptySelectionWidget()
        self.detail_container.append(self.empty_selection)
        self.paned.set_end_child(self.detail_container)
        
        req_page = self.app_stack.add_titled(self.paned, "requirements", "Requirements")
        req_page.set_icon_name("format-list-bulleted-symbolic")
        
        # --- SECTIONS PAGE ---
        self.planning_view = PlanningView(self.db)
        plan_page = self.app_stack.add_titled(self.planning_view, "sections", "Sections")
        plan_page.set_icon_name("view-grid-symbolic")

        # --- TIMELINE PAGE ---
        self.roadmap_view = RoadmapView(self.db)
        time_page = self.app_stack.add_titled(self.roadmap_view, "timeline", "Timeline")
        time_page.set_icon_name("appointment-soon-symbolic")
        
        # --- ANALYTICS PAGE ---
        self.stats_view = StatsWidget(self.db)
        dash_page = self.app_stack.add_titled(self.stats_view, "analytics", "Analytics")
        dash_page.set_icon_name("org.gnome.Usage-symbolic")

    def refresh_all_views(self):
        tasks = self.db.get_all_tasks()
        
        # Handle Welcome vs App view
        if not tasks:
            self.main_stack.set_visible_child_name("welcome")
        else:
            self.main_stack.set_visible_child_name("app")
            self.refresh_task_list(tasks)
            self.roadmap_view.refresh()
            self.planning_view.refresh()
            self.stats_view.refresh()

    def refresh_task_list(self, tasks):
        while row := self.task_list.get_first_child():
            self.task_list.remove(row)
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

    def on_export_clicked(self, _):
        dialog = Gtk.FileChooserNative(
            title="Export PRD Document",
            transient_for=self.window,
            action=Gtk.FileChooserAction.SAVE,
            accept_label="_Save",
            cancel_label="_Cancel"
        )
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
            if not file: return
            file_path = file.get_path()
            tasks = self.db.get_all_tasks()
            content = PRDExporter.generate_markdown(tasks) if file_path.endswith(".md") else PRDExporter.generate_text(tasks)
            try:
                with open(file_path, "w", encoding="utf-8") as f: f.write(content)
                self.window.add_toast(Adw.Toast.new(f"Exported to {os.path.basename(file_path)}"))
            except Exception as e:
                self.window.add_toast(Adw.Toast.new(f"Export failed: {str(e)}"))

    def on_focus_toggled(self, btn):
        active = btn.get_active()
        self.sidebar_box.set_visible(not active)
        if active: self.start_pomodoro()
        else: self.stop_pomodoro()

    def start_pomodoro(self):
        self.pomodoro_seconds = 25 * 60
        self.timer_id = GLib.timeout_add_seconds(1, self.update_timer)

    def stop_pomodoro(self):
        if self.timer_id: GLib.source_remove(self.timer_id); self.timer_id = None
        self.timer_label.set_text("25:00")

    def update_timer(self):
        if self.pomodoro_seconds <= 0: self.timer_label.set_text("Break!"); return False
        self.pomodoro_seconds -= 1
        mins, secs = divmod(self.pomodoro_seconds, 60)
        self.timer_label.set_text(f"{mins:02d}:{secs:02d}")
        return True

    def show_add_task_dialog(self, _):
        dialog = AddTaskWindow(self.window, self.db, on_save=self.refresh_all_views)
        dialog.present()

    def do_shutdown(self):
        self.db.close()
        super().do_shutdown()

if __name__ == "__main__":
    app = SmartTodoApp()
    app.run(sys.argv)
