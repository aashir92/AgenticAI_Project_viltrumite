type Props = { src?: string };

export default function VideoPlayer({ src }: Props) {
  return (
    <div className="card">
      <h3>Final Output</h3>
      {src ? <video src={src} controls className="video" /> : <p>No video yet.</p>}
    </div>
  );
}
