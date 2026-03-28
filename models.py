#!/usr/bin/env python3
"""
Data models for Smart To-Do List application
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict
import json

class Priority(Enum):
    """Task priority levels"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    
    @classmethod
    def from_string(cls, value: str):
        mapping = {'low': cls.LOW, 'medium': cls.MEDIUM, 'high': cls.HIGH, 'critical': cls.CRITICAL}
        return mapping.get(value.lower(), cls.MEDIUM)
    
    def to_string(self) -> str:
        return self.name.capitalize()
    
    def get_emoji(self) -> str:
        return {Priority.LOW: '🟢', Priority.MEDIUM: '🟡', Priority.HIGH: '🟠', Priority.CRITICAL: '🔴'}.get(self, '⚪')

class Status(Enum):
    """Task status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    
    @classmethod
    def from_string(cls, value: str):
        mapping = {'pending': cls.PENDING, 'in_progress': cls.IN_PROGRESS, 'completed': cls.COMPLETED, 'blocked': cls.BLOCKED}
        return mapping.get(value.lower(), cls.PENDING)
    
    def to_string(self) -> str:
        return self.name.replace('_', ' ').capitalize()

@dataclass
class SubTask:
    """Sub-task checklist item"""
    id: str
    text: str
    completed: bool = False

    def to_dict(self):
        return {"id": self.id, "text": self.text, "completed": self.completed}

@dataclass
class HistoryEntry:
    """Audit log entry for task changes"""
    id: Optional[int] = None
    task_id: int = 0
    change_type: str = "" # 'status', 'priority', 'description', etc.
    old_value: str = ""
    new_value: str = ""
    changed_at: datetime = field(default_factory=datetime.now)

@dataclass
class Task:
    """Task data model"""
    id: Optional[int] = None
    title: str = ""
    description: str = ""
    priority: Priority = Priority.MEDIUM
    status: Status = Status.PENDING
    category: str = ""
    due_date: Optional[datetime] = None
    created_at: Optional[datetime] = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    prd_section: str = ""
    estimated_hours: float = 0.0
    actual_hours: float = 0.0
    checklist: List[SubTask] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'priority': self.priority.value,
            'status': self.status.value,
            'category': self.category,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'tags': json.dumps(self.tags),
            'prd_section': self.prd_section,
            'estimated_hours': self.estimated_hours,
            'actual_hours': self.actual_hours,
            'checklist': json.dumps([s.to_dict() for s in self.checklist])
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        checklist_data = json.loads(data.get('checklist', '[]'))
        return cls(
            id=data.get('id'),
            title=data.get('title', ''),
            description=data.get('description', ''),
            priority=Priority(data.get('priority', 2)),
            status=Status.from_string(data.get('status', 'pending')),
            category=data.get('category', ''),
            due_date=datetime.fromisoformat(data['due_date']) if data.get('due_date') else None,
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None,
            tags=json.loads(data.get('tags', '[]')),
            prd_section=data.get('prd_section', ''),
            estimated_hours=data.get('estimated_hours', 0.0),
            actual_hours=data.get('actual_hours', 0.0),
            checklist=[SubTask(**s) for s in checklist_data]
        )

@dataclass
class Comment:
    id: Optional[int] = None
    task_id: int = 0
    comment: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    user: str = ""

class TaskFilter:
    def __init__(self):
        self.search_text = ""
        self.priority: Optional[Priority] = None
        self.status: Optional[Status] = None
        self.category: Optional[str] = None
        self.show_completed = True

    def is_empty(self) -> bool:
        return not any([self.search_text, self.priority, self.status, self.category, not self.show_completed])

    def to_sql_query(self) -> tuple:
        conditions, params = [], []
        if self.search_text:
            conditions.append("(title LIKE ? OR description LIKE ?)")
            params.extend([f"%{self.search_text}%", f"%{self.search_text}%"])
        if self.priority:
            conditions.append("priority = ?")
            params.append(self.priority.value)
        if self.status:
            conditions.append("status = ?")
            params.append(self.status.value)
        if self.category:
            conditions.append("category = ?")
            params.append(self.category)
        if not self.show_completed:
            conditions.append("status != 'completed'")
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        return where_clause, params
