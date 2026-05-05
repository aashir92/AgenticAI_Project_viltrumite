export type ProgressEvent = {
  phase: string;
  status: string;
  percent: number;
  meta?: Record<string, unknown>;
};

type Props = { events: ProgressEvent[] };

export default function PhaseProgress({ events }: Props) {
  return (
    <div className="card">
      <h3>Pipeline Progress</h3>
      {events.map((e, idx) => (
        <div key={`${e.phase}-${idx}`} className="phase-row">
          <div className="phase-head">
            <span>{e.phase}</span>
            <span>{e.percent}%</span>
          </div>
          <div className="bar">
            <div className="bar-fill" style={{ width: `${e.percent}%` }} />
          </div>
          <small>{e.status}</small>
        </div>
      ))}
    </div>
  );
}
