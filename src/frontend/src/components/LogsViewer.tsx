import { useEffect, useRef, useState } from 'react';
import type { LogsResponse } from '../types/deployment';

export function LogsViewer({ response, text, title = 'Log output', isLoading = false }: { response?: LogsResponse; text?: string; title?: string; isLoading?: boolean }) {
  const [wrap, setWrap] = useState(true);
  const [autoScroll, setAutoScroll] = useState(true);
  const viewport = useRef<HTMLPreElement>(null);
  const output = text ?? response?.command.stdout ?? 'No logs available.';
  const isEmpty = !text && !response?.command.stdout?.trim();
  const lines = output.split('\n');
  const levelOf = (line: string) => /\b(fatal|critical|error|err)\b/i.test(line) ? 'error' : /\b(warn|warning)\b/i.test(line) ? 'warning' : /\b(debug|trace)\b/i.test(line) ? 'debug' : /\b(info|notice)\b/i.test(line) ? 'info' : 'other';
  useEffect(() => { if (autoScroll && viewport.current) viewport.current.scrollTop = viewport.current.scrollHeight; }, [autoScroll, output]);
  const [copied, setCopied] = useState(false);
  const copy = async () => {
    if (!navigator.clipboard?.writeText) return;
    try {
      await navigator.clipboard.writeText(output);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1600);
    } catch { setCopied(false); }
  };
  const download = () => {
    const url = URL.createObjectURL(new Blob([output], { type: 'text/plain' }));
    const link = document.createElement('a');
    link.href = url; link.download = 'lain5g-lab-logs.txt'; link.click(); URL.revokeObjectURL(url);
  };
  return <section className="panel logs-panel"><div className="panel-heading"><div><span className="eyebrow">Log stream</span><h3>{title}</h3></div><div className="inline-actions"><button className="secondary" onClick={() => setWrap((value) => !value)}>{wrap ? 'No wrap' : 'Wrap lines'}</button><button className="secondary" onClick={() => setAutoScroll((value) => !value)}>{autoScroll ? 'Pause scroll' : 'Resume scroll'}</button><button className="secondary" onClick={copy}>{copied ? 'Copied' : 'Copy visible'}</button><button className="secondary" onClick={download}>Download</button></div></div>{isEmpty ? <div className="logs-empty-state"><strong>{isLoading ? 'Loading service output…' : 'No service output in this fetch'}</strong><p>{isLoading ? 'Waiting for the selected service logs.' : 'The selected services have not emitted container messages in this capture. Check the deployment state, select another service, or refresh after starting the profile.'}</p></div> : <pre ref={viewport} className={`logs-viewer ${wrap ? 'wrap' : 'no-wrap'}`} aria-label="Filtered service log output">{lines.map((line, index) => <span className={`log-line log-${levelOf(line)}`} key={`${index}-${line}`}><span className="log-line-number">{index + 1}</span><span className="log-line-content">{line || ' '}</span></span>)}</pre>}{response?.command.stderr ? <details className="technical-output"><summary>Command diagnostics</summary><pre>{response.command.stderr}</pre></details> : null}</section>;
}
