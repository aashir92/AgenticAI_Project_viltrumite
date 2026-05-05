from __future__ import annotations

from typing import Callable, Dict

from agents.audio_agent.agent import AudioAgent
from agents.story_agent.agent import StoryAgent
from agents.video_agent.agent import VideoAgent
from shared.utils import read_json


class PipelineWorkflow:
    def __init__(self, progress_cb: Callable[[str, str, int, Dict], None]) -> None:
        self.progress_cb = progress_cb
        self.story_agent = StoryAgent()
        self.audio_agent = AudioAgent()
        self.video_agent = VideoAgent()

    def run_story(self, job_id: str, user_prompt: str) -> Dict:
        self.progress_cb("story", "running", 15, {"msg": "Generating story"})
        res = self.story_agent.run(job_id, user_prompt)
        self.progress_cb("story", "completed", 30, {"story_spec_path": res["story_spec_path"]})
        return res

    def run_audio(self, job_id: str, story_spec_path: str) -> Dict:
        self.progress_cb("audio", "running", 45, {"msg": "Generating voice lines"})
        story = read_json(story_spec_path)
        res = self.audio_agent.run(job_id=job_id, story_spec_data=story)
        self.progress_cb("audio", "completed", 65, {"timing_manifest_path": res["timing_manifest_path"]})
        return res

    def run_video(self, job_id: str, story_spec_path: str, timing_manifest_path: str, master_audio_path: str) -> Dict:
        self.progress_cb("video", "running", 80, {"msg": "Rendering final video"})
        story = read_json(story_spec_path)
        timing = read_json(timing_manifest_path)
        res = self.video_agent.run(job_id, story, timing, master_audio_path=master_audio_path)
        self.progress_cb("video", "completed", 100, {"final_video_path": res["final_video_path"]})
        return res
