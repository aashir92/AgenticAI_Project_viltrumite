type Props = { onSubmit: (prompt: string) => void; loading: boolean };

export default function PromptForm({ onSubmit, loading }: Props) {
  return (
    <form
      className="card"
      onSubmit={(e) => {
        e.preventDefault();
        const data = new FormData(e.currentTarget);
        const prompt = String(data.get("prompt") || "");
        onSubmit(prompt);
      }}
    >
      <label className="label">Film Prompt</label>
      <textarea name="prompt" className="input" rows={4} placeholder="A rainy rooftop argument between two old friends..." />
      <button className="btn" disabled={loading}>
        {loading ? "Generating..." : "Generate Video"}
      </button>
    </form>
  );
}
