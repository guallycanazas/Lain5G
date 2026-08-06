import { useEffect, useRef, useState } from 'react';
import type { LogsResponse } from '../types/deployment';

export function LogsViewer({ response, text, title = 'Log output' }: { response?: LogsResponse; text?: string; title?: string }) {
  const [wrap, setWrap] = useState(true);
  const [autoScroll, setAutoScroll] = useState(true);
  const viewport = useRef<HTMLPreElement>(null);
  const output = text ?? response?.command.stdout ?? 'No logs available.';
  useEffect(() => { if (autoScroll && viewport.current) viewport.current.scrollTop = viewport.current.scrollHeight; }, [autoScroll, output]);
  const copy = async () => navigator.clipboard?.writeText(output);
  const download = () => {
    const url = URL.createObjectURL(new Blob([output], { type: 'text/plain' }));
    const link = document.createElement('a');
    link.href = url; link.download = 'lain5g-lab-logs.txt'; link.click(); URL.revokeObjectURL(url);
  };
  return <section className="panel logs-panel"><div className="panel-heading"><div><span className="eyebrow">Streaming view</span><h3>{title}</h3></div><div className="inline-actions"><button className="secondary" onClick={() => setWrap((value) => !value)}>{wrap ? 'No wrap' : 'Wrap'}</button><button className="secondary" onClick={() => setAutoScroll((value) => !value)}>{autoScroll ? 'Pause scroll' : 'Resume scroll'}</button><button className="secondary" onClick={copy}>Copy</button><button className="secondary" onClick={download}>Download</button></div></div><pre ref={viewport} className="logs-viewer" style={{ whiteSpace: wrap ? 'pre-wrap' : 'pre' }}>{output}</pre>{response?.command.stderr ? <details className="technical-output"><summary>stderr</summary><pre>{response.command.stderr}</pre></details> : null}</section>;
}
