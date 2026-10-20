import { useEffect, useRef, useState } from 'react';
import type { LogsResponse } from '../types/deployment';

const diagnosticRules = [
  { category: 'USRP / UHD / FPGA', title: 'Radio initialization problem detected', pattern: /no uhd devices|no devices found|failed to (?:open|claim|make|create).*?(?:device|usrp)|uhd.*(?:error|fail|timeout|exception)|(?:fpga|image).*(?:incompat|mismatch|fail|not found|error)|firmware.*(?:incompat|mismatch|fail|error)|usrp.*(?:not found|busy|fail|error|timeout)|(?:clock|time|lo|gpsdo).*(?:not locked|unlock|fail|error)|rx streamer.*(?:error|fail)|tx streamer.*(?:error|fail)/i },
  { category: 'Locks / contention', title: 'Resource lock or service contention detected', pattern: /resource temporarily unavailable|device or resource busy|another rf start is in progress|another rf session is active|flock.*(?:fail|lock)|failed to acquire.*(?:lock|device|resource)|lock.*(?:timeout|failed|busy)|address already in use|port .* already allocated|bind\(\).*failed/i },
  { category: 'Host networking / preflight', title: 'Network or hardware preflight problem detected', pattern: /ethernet[_ -]?link.*(?:fail|warning|error)|ethernet.*(?:link down|no carrier|unavailable)|no host ipv4 route|no route to host|network is unreachable|destination host unreachable|usrp.*(?:did not respond|not found)|uhd.*(?:not available|not found)|fpga.*(?:unknown|incompatible|not found)/i },
  { category: 'UE / attach / radio connection', title: 'UE connection or attach problem detected', pattern: /attach.*(?:fail|reject|timeout|repeated)|(?:reject|rejected).*(?:ue|attach|registration)|(?:ue|subscriber).*(?:disconnect|detached|lost|timeout|fail)|(?:rrc|nas).*(?:reject|release|fail|timeout)|(?:registration|authentication).*(?:reject|fail|timeout)|(?:radio link failure|rlf|random access.*(?:fail|problem)|erab.*(?:fail|reject)|failed to establish.*(?:connection|session|bearer))|(?:no|zero) (?:active )?ue|ue.*(?:not connected|connection lost)/i },
  { category: 'Service / preflight result', title: 'Service or preflight failure detected', pattern: /\b(?:fatal|critical|error|failed|failure|FAIL)\b|\[E\]|segmentation fault|core dumped|process exited with code [1-9]/i },
];

function diagnose(output: string) {
  const lines = output.split(/\r?\n/);
  return diagnosticRules.flatMap((rule) => {
    const matches = lines.filter((line) => rule.pattern.test(line)).slice(-5);
    return matches.length ? [{ ...rule, matches }] : [];
  });
}

export function LogsViewer({ response, text, title = 'Log output' }: { response?: LogsResponse; text?: string; title?: string }) {
  const [wrap, setWrap] = useState(true);
  const [autoScroll, setAutoScroll] = useState(true);
  const viewport = useRef<HTMLPreElement>(null);
  const output = text ?? response?.command.stdout ?? 'No logs available.';
  const diagnostics = diagnose(output);
  useEffect(() => { if (autoScroll && viewport.current) viewport.current.scrollTop = viewport.current.scrollHeight; }, [autoScroll, output]);
  const copy = async () => navigator.clipboard?.writeText(output);
  const download = () => {
    const url = URL.createObjectURL(new Blob([output], { type: 'text/plain' }));
    const link = document.createElement('a');
    link.href = url; link.download = 'lain5g-lab-logs.txt'; link.click(); URL.revokeObjectURL(url);
  };
  return <section className="panel logs-panel"><div className="panel-heading"><div><span className="eyebrow">Service output</span><h3>{title}</h3></div><div className="inline-actions"><button className="secondary" onClick={() => setWrap((value) => !value)}>{wrap ? 'No wrap' : 'Wrap'}</button><button className="secondary" onClick={() => setAutoScroll((value) => !value)}>{autoScroll ? 'Pause scroll' : 'Resume scroll'}</button><button className="secondary" onClick={copy}>Copy</button><button className="secondary" onClick={download}>Download</button></div></div>{diagnostics.length ? <div className="log-diagnostics" role="alert"><strong>{diagnostics.length} possible issue{diagnostics.length === 1 ? '' : 's'} found in the current log window</strong>{diagnostics.map((item) => <details key={item.category} open><summary>{item.title} <span>{item.category}</span></summary><ul>{item.matches.map((line, index) => <li key={`${item.category}-${index}`}><code>{line}</code></li>)}</ul></details>)}</div> : response ? <p className="log-clear-state">No known hardware, service, lock, or UE error patterns found in the current log window.</p> : null}<pre ref={viewport} className="logs-viewer" style={{ whiteSpace: wrap ? 'pre-wrap' : 'pre' }}>{output}</pre>{response?.command.stderr ? <details className="technical-output"><summary>stderr</summary><pre>{response.command.stderr}</pre></details> : null}</section>;
}
