from __future__ import annotations

from typing import Callable, Dict

from langgraph.graph import END, StateGraph

from .state import OrchestratorState
from .workflow import PipelineWorkflow


def build_pipeline_graph(progress_cb: Callable[[str, str, int, Dict], None]):
    workflow = PipelineWorkflow(progress_cb=progress_cb)
    graph = StateGraph(OrchestratorState)

    def story_node(state: OrchestratorState):
        res = workflow.run_story(state["job_id"], state["user_prompt"])
        return {**state, "story_spec_path": res["story_spec_path"]}

    def audio_node(state: OrchestratorState):
        res = workflow.run_audio(state["job_id"], state["story_spec_path"])
        return {
            **state,
            "timing_manifest_path": res["timing_manifest_path"],
            "master_audio_path": res["master_audio_path"],
        }

    def video_node(state: OrchestratorState):
        res = workflow.run_video(
            state["job_id"], state["story_spec_path"], state["timing_manifest_path"], state["master_audio_path"]
        )
        return {**state, "final_video_path": res["final_video_path"]}

    graph.add_node("story", story_node)
    graph.add_node("audio", audio_node)
    graph.add_node("video", video_node)
    graph.set_entry_point("story")
    graph.add_edge("story", "audio")
    graph.add_edge("audio", "video")
    graph.add_edge("video", END)
    return graph.compile()
