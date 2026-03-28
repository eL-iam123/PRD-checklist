#!/usr/bin/env python3
"""
Custom widgets for Smart To-Do List
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib, Adw, Pango
from datetime import datetime
import uuid
from models import Task, Status, Priority, SubTask

def markdown_to_pango(text):
    """Simple markdown to Pango markup converter"""
    import re
    # Bold
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    # Italic
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
    # Code
    text = re.sub(r'`(.*?)`', r'<span font_family="monospace" background="#f0f0f0">\1</span>', text)
    # Lists
    text = re.sub(r'^\s*-\s*(.*)', r' • \1', text, flags=re.MULTILINE)
    return text

class ChecklistWidget(Gtk.Box):
    """Widget for managing sub-tasks"""
    def __init__(self, task, on_change):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.task = task
        self.on_change = on_change
        self.refresh()

    def refresh(self):
        while child := self.get_first_child():
            self.remove(child)
        
        for item in self.task.checklist:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            check = Gtk.CheckButton()
            check.set_active(item.completed)
            check.connect("toggled", self.on_item_toggled, item)
            
            label = Gtk.Label(label=item.text)
            label.set_hexpand(True)
            label.set_halign(Gtk.Align.START)
            
            remove_btn = Gtk.Button.new_from_icon_name("list-remove-symbolic")
            remove_btn.get_style_context().add_class("flat")
            remove_btn.connect("clicked", self.on_remove_item, item)
            
            row.append(check)
            row.append(label)
            row.append(remove_btn)
            self.append(row)
        
        # Add new item entry
        add_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.new_item_entry = Gtk.Entry(placeholder_text="Add sub-task...")
        self.new_item_entry.set_hexpand(True)
        self.new_item_entry.connect("activate", self.on_add_item)
        
        add_btn = Gtk.Button.new_from_icon_name("list-add-symbolic")
        add_btn.connect("clicked", self.on_add_item)
        
        add_box.append(self.new_item_entry)
        add_box.append(add_btn)
        self.append(add_box)

    def on_item_toggled(self, btn, item):
        item.completed = btn.get_active()
        self.on_change()

    def on_add_item(self, widget):
        text = self.new_item_entry.get_text().strip()
        if text:
            self.task.checklist.append(SubTask(id=str(uuid.uuid4()), text=text))
            self.new_item_entry.set_text("")
            self.refresh()
            self.on_change()

    def on_remove_item(self, btn, item):
        self.task.checklist.remove(item)
        self.refresh()
        self.on_change()

class HistoryWidget(Gtk.Box):
    """Widget for displaying task history/audit log"""
    def __init__(self, history):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        for entry in history:
            row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            row.get_style_context().add_class("card")
            
            header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            type_label = Gtk.Label()
            type_label.set_markup(f"<b>{entry.change_type.upper()}</b>")
            date_label = Gtk.Label(label=entry.changed_at.strftime("%Y-%m-%d %H:%M"))
            date_label.set_hexpand(True)
            date_label.set_halign(Gtk.Align.END)
            header.append(type_label)
            header.append(date_label)
            
            detail = Gtk.Label(label=f"{entry.old_value} → {entry.new_value}" if entry.old_value else entry.new_value)
            detail.set_halign(Gtk.Align.START)
            detail.set_wrap(True)
            
            row.append(header)
            row.append(detail)
            self.append(row)

class TaskRowWidget(Gtk.ListBoxRow):
    def __init__(self, task: Task, on_toggle=None):
        super().__init__()
        self.task = task
        self.on_toggle = on_toggle
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.main_box.set_margin_top(8)
        self.main_box.set_margin_bottom(8)
        self.main_box.set_margin_start(8)
        self.main_box.set_margin_end(8)
        self.set_child(self.main_box)
        self.create_widgets()

    def create_widgets(self):
        check = Gtk.CheckButton(active=(self.task.status == Status.COMPLETED))
        check.connect("toggled", lambda b: self.on_toggle(self.task.id, b.get_active()))
        
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        content.set_hexpand(True)
        
        title = Gtk.Label(xalign=0)
        title_text = f"{self.task.priority.get_emoji()} {self.task.title}"
        if self.task.status == Status.COMPLETED:
            title.set_markup(f"<s>{GLib.markup_escape_text(title_text)}</s>")
        else:
            title.set_text(title_text)
        
        details = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        if self.task.category:
            cat = Gtk.Label(label=self.task.category)
            cat.get_style_context().add_class("tag")
            details.append(cat)
            
        if self.task.checklist:
            done = sum(1 for s in self.task.checklist if s.completed)
            progress = Gtk.Label(label=f"📋 {done}/{len(self.task.checklist)}")
            details.append(progress)

        content.append(title)
        content.append(details)
        
        self.main_box.append(check)
        self.main_box.append(content)

class TaskDetailWidget(Gtk.ScrolledWindow):
    def __init__(self, task: Task, db, on_update=None):
        super().__init__()
        self.task = task
        self.db = db
        self.on_update = on_update
        
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        self.content.set_margin_top(20)
        self.content.set_margin_bottom(20)
        self.content.set_margin_start(20)
        self.content.set_margin_end(20)
        self.set_child(self.content)
        self.create_widgets()

    def create_widgets(self):
        # Header: Title and Status
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        title_entry = Adw.EntryRow(title="Title", text=self.task.title)
        title_entry.connect("changed", self.on_field_changed, "title")
        header.append(title_entry)
        self.content.append(header)

        # Description with Markdown Toggle
        desc_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        desc_label_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        desc_label_box.append(Gtk.Label(label="Description (Markdown supported):", xalign=0))
        
        self.preview_btn = Gtk.ToggleButton(label="Preview")
        self.preview_btn.connect("toggled", self.on_preview_toggled)
        desc_label_box.append(self.preview_btn)
        
        self.desc_stack = Gtk.Stack()
        self.desc_buffer = Gtk.TextBuffer(text=self.task.description)
        self.desc_view = Gtk.TextView(buffer=self.desc_buffer, wrap_mode=Gtk.WrapMode.WORD)
        self.desc_view.set_size_request(-1, 150)
        
        self.desc_preview = Gtk.Label(xalign=0, yalign=0, wrap=True)
        self.desc_preview.set_use_markup(True)
        
        self.desc_stack.add_named(self.desc_view, "edit")
        self.desc_stack.add_named(self.desc_preview, "preview")
        
        desc_box.append(desc_label_box)
        desc_box.append(self.desc_stack)
        self.content.append(desc_box)
        
        # Checklist
        self.content.append(Gtk.Label(label="Sub-tasks Checklist:", xalign=0))
        self.content.append(ChecklistWidget(self.task, self.save_task))
        
        # History
        history_expander = Gtk.Expander(label="Audit Log / History")
        history_list = HistoryWidget(self.db.get_task_history(self.task.id))
        history_expander.set_child(history_list)
        self.content.append(history_expander)

    def on_preview_toggled(self, btn):
        if btn.get_active():
            text = self.desc_buffer.get_text(self.desc_buffer.get_start_iter(), self.desc_buffer.get_end_iter(), False)
            self.desc_preview.set_markup(markdown_to_pango(GLib.markup_escape_text(text)))
            self.desc_stack.set_visible_child_name("preview")
        else:
            self.desc_stack.set_visible_child_name("edit")

    def on_field_changed(self, entry, field_name):
        setattr(self.task, field_name, entry.get_text())
        self.save_task()

    def save_task(self):
        # Update description from buffer before saving
        if self.desc_stack.get_visible_child_name() == "edit":
            self.task.description = self.desc_buffer.get_text(self.desc_buffer.get_start_iter(), self.desc_buffer.get_end_iter(), False)
        
        self.db.update_task(self.task)
        if self.on_update: self.on_update()

class StatsWidget(Gtk.Box):
    def __init__(self, db):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        self.db = db
        self.set_margin_top(20)
        self.set_margin_bottom(20)
        self.set_margin_start(20)
        self.set_margin_end(20)
        self.refresh()

    def refresh(self):
        while child := self.get_first_child(): self.remove(child)
        stats = self.db.get_statistics()
        self.append(Gtk.Label(label=f"Completion Rate: {stats['completion_rate']:.1f}%"))
