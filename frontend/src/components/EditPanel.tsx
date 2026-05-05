type Props = {
  jobId?: string;
  onApply: (query: string) => Promise<void>;
  onUndo: () => Promise<void>;
};

export default function EditPanel({ jobId, onApply, onUndo }: Props) {
  return (
    <form
      className="card"
      onSubmit={async (e) => {
        e.preventDefault();
        const data = new FormData(e.currentTarget);
        await onApply(String(data.get("query") || ""));
      }}
    >
      <h3>Edit & Undo Agent</h3>
      <input name="query" className="input" placeholder="Make the background darker and moodier." />
      <div className="row">
        <button className="btn" disabled={!jobId}>
          Apply Edit
        </button>
        <button className="btn secondary" type="button" onClick={onUndo} disabled={!jobId}>
          Undo Last
        </button>
      </div>
    </form>
  );
}
