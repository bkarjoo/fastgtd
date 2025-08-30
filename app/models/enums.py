from enum import Enum


class TaskStatus(str, Enum):
    todo = "todo"
    in_progress = "in_progress"
    done = "done"
    dropped = "dropped"


class TaskPriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"


class ArtifactKind(str, Enum):
    file = "file"
    link = "link"

