from enum import Enum


class PhaseName(str, Enum):
    STORY = "story"
    AUDIO = "audio"
    VIDEO = "video"
    EDIT = "edit"
    DONE = "done"
    ERROR = "error"


class EditTarget(str, Enum):
    AUDIO = "audio"
    VIDEO_FRAME = "video_frame"
    VIDEO = "video"
    SCRIPT = "script"


DEFAULT_VIDEO_FPS = 24
DEFAULT_VIDEO_RESOLUTION = (1280, 720)
DEFAULT_TARGET_DURATION_SECONDS = 60
MAX_STORY_REPAIR_ATTEMPTS = 3
