#!/usr/bin/env python3
"""
Database management for Smart To-Do List
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Optional, Tuple
from models import Task, Comment, TaskFilter, Status, Priority, HistoryEntry

class Database:
    """Database manager for the application"""
    
    def __init__(self, db_path: str = "smart_todo.db"):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.init_database()
    
    def init_database(self):
        """Initialize database connection and create tables"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.create_tables()
        self.migrate_database()
    
    def create_tables(self):
        """Create all necessary tables"""
        # Tasks table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                priority INTEGER DEFAULT 2,
                status TEXT DEFAULT 'pending',
                category TEXT,
                due_date TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tags TEXT,
                prd_section TEXT,
                estimated_hours REAL DEFAULT 0,
                actual_hours REAL DEFAULT 0,
                checklist TEXT DEFAULT '[]'
            )
        ''')
        
        # Comments table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                comment TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user TEXT DEFAULT '',
                FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE CASCADE
            )
        ''')

        # History table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                change_type TEXT NOT NULL,
                old_value TEXT,
                new_value TEXT,
                changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE CASCADE
            )
        ''')
        
        # Categories table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                name TEXT PRIMARY KEY,
                color TEXT DEFAULT '#6c5ce7',
                icon TEXT DEFAULT 'folder-symbolic',
                description TEXT
            )
        ''')
        
        # Tags table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS tags (
                name TEXT PRIMARY KEY,
                usage_count INTEGER DEFAULT 0
            )
        ''')
        
        self.conn.commit()

    def migrate_database(self):
        """Handle schema migrations"""
        # Check for checklist column
        self.cursor.execute("PRAGMA table_info(tasks)")
        columns = [column[1] for column in self.cursor.fetchall()]
        if 'checklist' not in columns:
            self.cursor.execute("ALTER TABLE tasks ADD COLUMN checklist TEXT DEFAULT '[]'")
            self.conn.commit()

    # Task operations
    def add_task(self, task: Task) -> int:
        """Add a new task"""
        task.updated_at = datetime.now()
        data = task.to_dict()
        
        self.cursor.execute('''
            INSERT INTO tasks (title, description, priority, status, category, 
                             due_date, tags, prd_section, estimated_hours, 
                             actual_hours, checklist, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['title'], data['description'], data['priority'],
            data['status'], data['category'], data['due_date'],
            data['tags'], data['prd_section'], data['estimated_hours'],
            data['actual_hours'], data['checklist'], data['created_at'], data['updated_at']
        ))
        
        task.id = self.cursor.lastrowid
        self.conn.commit()
        self.log_history(task.id, 'creation', None, 'Task created')
        return task.id
    
    def get_task(self, task_id: int) -> Optional[Task]:
        """Get task by ID"""
        self.cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = self.cursor.fetchone()
        if row:
            return Task.from_dict(dict(row))
        return None
    
    def get_all_tasks(self, filter_obj: Optional[TaskFilter] = None) -> List[Task]:
        """Get all tasks with optional filtering"""
        if filter_obj and not filter_obj.is_empty():
            where_clause, params = filter_obj.to_sql_query()
            query = f"SELECT * FROM tasks WHERE {where_clause} ORDER BY priority DESC, due_date ASC"
            self.cursor.execute(query, params)
        else:
            self.cursor.execute("SELECT * FROM tasks ORDER BY priority DESC, due_date ASC")
        
        return [Task.from_dict(dict(row)) for row in self.cursor.fetchall()]
    
    def update_task(self, task: Task) -> bool:
        """Update existing task and log changes"""
        old_task = self.get_task(task.id)
        if not old_task: return False

        # Detect changes for history
        changes = []
        if old_task.status != task.status:
            changes.append(('status', old_task.status.value, task.status.value))
        if old_task.priority != task.priority:
            changes.append(('priority', old_task.priority.name, task.priority.name))
        if old_task.description != task.description:
            changes.append(('description', 'Previous description', 'Updated description'))

        task.updated_at = datetime.now()
        data = task.to_dict()
        
        self.cursor.execute('''
            UPDATE tasks 
            SET title=?, description=?, priority=?, status=?, category=?,
                due_date=?, tags=?, prd_section=?, estimated_hours=?,
                actual_hours=?, checklist=?, updated_at=?
            WHERE id=?
        ''', (
            data['title'], data['description'], data['priority'],
            data['status'], data['category'], data['due_date'],
            data['tags'], data['prd_section'], data['estimated_hours'],
            data['actual_hours'], data['checklist'], data['updated_at'], task.id
        ))
        
        self.conn.commit()
        
        for change_type, old_val, new_val in changes:
            self.log_history(task.id, change_type, old_val, new_val)
            
        return self.cursor.rowcount > 0
    
    def log_history(self, task_id, change_type, old_val, new_val):
        """Log a change to task history"""
        self.cursor.execute('''
            INSERT INTO task_history (task_id, change_type, old_value, new_value)
            VALUES (?, ?, ?, ?)
        ''', (task_id, change_type, str(old_val) if old_val else None, str(new_val)))
        self.conn.commit()

    def get_task_history(self, task_id: int) -> List[HistoryEntry]:
        """Get audit log for a task"""
        self.cursor.execute("SELECT * FROM task_history WHERE task_id = ? ORDER BY changed_at DESC", (task_id,))
        return [HistoryEntry(
            id=row['id'],
            task_id=row['task_id'],
            change_type=row['change_type'],
            old_value=row['old_value'],
            new_value=row['new_value'],
            changed_at=datetime.fromisoformat(row['changed_at']) if isinstance(row['changed_at'], str) else row['changed_at']
        ) for row in self.cursor.fetchall()]

    # Comment operations
    def add_comment(self, comment: Comment) -> int:
        data = comment.to_dict()
        self.cursor.execute('''
            INSERT INTO comments (task_id, comment, user, created_at)
            VALUES (?, ?, ?, ?)
        ''', (data['task_id'], data['comment'], data['user'], data['created_at']))
        self.conn.commit()
        return self.cursor.lastrowid
    
    def get_task_comments(self, task_id: int) -> List[Comment]:
        self.cursor.execute("SELECT * FROM comments WHERE task_id = ? ORDER BY created_at DESC", (task_id,))
        return [Comment.from_dict(dict(row)) for row in self.cursor.fetchall()]
    
    # Statistics
    def get_statistics(self) -> dict:
        stats = {}
        self.cursor.execute("SELECT COUNT(*) FROM tasks")
        stats['total'] = self.cursor.fetchone()[0]
        
        for status in Status:
            self.cursor.execute("SELECT COUNT(*) FROM tasks WHERE status = ?", (status.value,))
            stats[f'status_{status.value}'] = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM tasks WHERE due_date < datetime('now') AND status != 'completed'")
        stats['overdue'] = self.cursor.fetchone()[0]
        
        stats['completion_rate'] = (stats['status_completed'] / stats['total'] * 100) if stats['total'] > 0 else 0
        return stats

    def get_category_stats(self) -> List[dict]:
        self.cursor.execute('''
            SELECT category, COUNT(*) as count, 
                   SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed
            FROM tasks GROUP BY category ORDER BY count DESC
        ''')
        return [dict(row) for row in self.cursor.fetchall()]

    def get_categories(self) -> List[dict]:
        self.cursor.execute("SELECT * FROM categories ORDER BY name")
        return [dict(row) for row in self.cursor.fetchall()]
    
    def delete_task(self, task_id: int) -> bool:
        """Delete a task"""
        self.cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        self.conn.commit()
        return self.cursor.rowcount > 0

    def close(self):
        if self.conn: self.conn.close()
