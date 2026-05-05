import { useMemo, useState } from "react";
import EditPanel from "./components/EditPanel";
import PhaseProgress, { type ProgressEvent } from "./components/PhaseProgress";
import PromptForm from "./components/PromptForm";
import VideoPlayer from "./components/VideoPlayer";

const API_BASE = "http://localhost:8001";

export default function App() {
  const [jobId, setJobId] = useState<string>();
  const [events, setEvents] = useState<ProgressEvent[]>([]);
  const [videoPath, setVideoPath] = useState<string>();
  const [loading, setLoading] = useState(false);

  const socketUrl = useMemo(() => (jobId ? `ws://localhost:8001/ws/progress/${jobId}` : undefined), [jobId]);

  const start = async (prompt: string) => {
    setLoading(true);
    setEvents([]);
    const res = await fetch(`${API_BASE}/api/pipeline/start`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt })
    });
    const data = await res.json();
    setJobId(data.job_id);
    setLoading(false);

    const ws = new WebSocket(`ws://localhost:8001/ws/progress/${data.job_id}`);
    ws.onopen = () => ws.send("subscribe");
    ws.onmessage = (ev) => {
      const payload = JSON.parse(ev.data) as ProgressEvent;
      setEvents((prev) => [...prev, payload]);
      if (payload.phase === "done") {
        const path = String((payload.meta?.final_video_path as string) || "");
        if (path) setVideoPath(`${API_BASE}/api/assets/${data.job_id}/final_output.mp4`);
      }
    };
  };

  const applyEdit = async (query: string) => {
    if (!jobId) return;
    await fetch(`${API_BASE}/api/edit/${jobId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query })
    });
  };

  const undo = async () => {
    if (!jobId) return;
    await fetch(`${API_BASE}/api/edit/${jobId}/undo`, { method: "POST" });
  };

  return (
    <main className="layout">
      <h1>AI-Powered Animated Video Generation</h1>
      <p className="sub">Dark-mode orchestration dashboard with real-time multi-agent progress.</p>
      <PromptForm onSubmit={start} loading={loading} />
      <PhaseProgress events={events} />
      <VideoPlayer src={videoPath} />
      <EditPanel jobId={jobId} onApply={applyEdit} onUndo={undo} />
      {socketUrl && <small className="muted">WebSocket: {socketUrl}</small>}
    </main>
  );
}
