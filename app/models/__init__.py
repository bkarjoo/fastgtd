from app.db.session import Base

# Import models to register them with SQLAlchemy metadata
from .user import User  # noqa: F401
from .tag import Tag  # noqa: F401

# New unified models
from .node import Node, Task, Note  # noqa: F401
from .node_associations import node_tags  # noqa: F401
from .default_node import DefaultNode  # noqa: F401

# Legacy models - disabled to avoid naming conflicts during migration
# from .task_list import TaskList  # noqa: F401
# from .task import Task as LegacyTask  # noqa: F401
# from .tag_list import TagList  # noqa: F401
# from .note_list import NoteList  # noqa: F401
# from .associations import task_tags  # noqa: F401
# from .note import Note as LegacyNote  # noqa: F401
# from .artifact import Artifact  # noqa: F401
# from .default_task_list import DefaultTaskList  # noqa: F401
# from .default_note_list import DefaultNoteList  # noqa: F401
# from .default_tag_list import DefaultTagList  # noqa: F401

__all__ = [
    "Base",
    "User",
    "Tag",
    # New unified models
    "Node",
    "Task", 
    "Note",
    "DefaultNode",
    "node_tags",
]
