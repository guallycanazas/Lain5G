import { useCallback, useEffect, useState } from 'react';
import { Check, CircleAlert, Cpu, Download, KeyRound, RefreshCw, ShieldAlert, Usb } from 'lucide-react';
import { ActionButton } from '../components/ActionButton';
import { ConfirmDialog } from '../components/ConfirmDialog';
import { apiRequest } from '../services/apiClient';

interface ReaderStatus {
  available: boolean;
  programming_enabled: boolean;
  readers: string[];
  message: string;
}

interface CardStatus {
  reader: string;
  detected: boolean;
  recognized: boolean;
  supported: boolean;
  card?: string | null;
  message: string;
}

interface ProgramResult {
  success: boolean;
  reader: string;
  card: string;
  imsi: string;
  iccid: string;
  verified_fields: string[];
  message: string;
}

interface SimFields {
  mcc: string;
  mnc: string;
  imsi: string;
  iccid: string;
  ki: string;
  opc: string;
}

const EMPTY_FIELDS: SimFields = { mcc: '', mnc: '', imsi: '', iccid: '', ki: '', opc: '' };
const PBKDF2_ITERATIONS = 250_000;

function randomHex(bytes: number): string {
  const data = crypto.getRandomValues(new Uint8Array(bytes));
  return Array.from(data, (value) => value.toString(16).padStart(2, '0')).join('');
}

function randomDigits(count: number): string {
  const values = crypto.getRandomValues(new Uint8Array(count));
  return Array.from(values, (value) => String(value % 10)).join('');
}

function makeIccid(): string {
  const body = `89${randomDigits(16)}`;
  const sum = [...body].reverse().reduce((total, char, index) => {
    let digit = Number(char) * (index % 2 === 0 ? 2 : 1);
    if (digit > 9) digit -= 9;
    return total + digit;
  }, 0);
  return `${body}${(10 - (sum % 10)) % 10}`;
}

function hasValidIccidCheckDigit(iccid: string): boolean {
  if (!/^\d{19}$/.test(iccid)) return false;
  const sum = [...iccid].reverse().reduce((total, char, index) => {
    let digit = Number(char) * (index % 2 === 1 ? 2 : 1);
    if (digit > 9) digit -= 9;
    return total + digit;
  }, 0);
  return sum % 10 === 0;
}

function toBase64(data: Uint8Array): string {
  return btoa(String.fromCharCode(...data));
}

function fromBase64(value: string): Uint8Array<ArrayBuffer> {
  const binary = atob(value);
  const bytes = new Uint8Array(new ArrayBuffer(binary.length));
  for (let index = 0; index < binary.length; index += 1) bytes[index] = binary.charCodeAt(index);
  return bytes;
}

async function downloadEncryptedCredentials(fields: SimFields, passphrase: string): Promise<void> {
  if (!crypto.subtle) throw new Error('Secure browser encryption is unavailable. Open the console on localhost or HTTPS.');
  const salt = crypto.getRandomValues(new Uint8Array(16));
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const material = await crypto.subtle.importKey('raw', new TextEncoder().encode(passphrase), 'PBKDF2', false, ['deriveKey']);
  const key = await crypto.subtle.deriveKey(
    { name: 'PBKDF2', salt, iterations: PBKDF2_ITERATIONS, hash: 'SHA-256' },
    material,
    { name: 'AES-GCM', length: 256 },
    false,
    ['encrypt'],
  );
  const plaintext = new TextEncoder().encode(JSON.stringify({ format: 'openlain5g-sim-credentials', version: 1, ...fields }));
  const ciphertext = await crypto.subtle.encrypt({ name: 'AES-GCM', iv }, key, plaintext);
  const envelope = {
    format: 'openlain5g-encrypted-sim-credentials',
    version: 1,
    kdf: { name: 'PBKDF2', hash: 'SHA-256', iterations: PBKDF2_ITERATIONS, salt: toBase64(salt) },
    encryption: { name: 'AES-GCM', iv: toBase64(iv) },
    ciphertext: toBase64(new Uint8Array(ciphertext)),
  };
  const file = new Blob([JSON.stringify(envelope, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(file);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = 'openlain5g-sim-credentials.encrypted.json';
  anchor.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

async function decryptCredentials(file: File, passphrase: string): Promise<SimFields> {
  if (!crypto.subtle) throw new Error('Secure browser encryption is unavailable. Open the console on localhost or HTTPS.');
  if (file.size > 65_536) throw new Error('That credential backup is not a valid OpenLain5G file.');
  const envelope = JSON.parse(await file.text()) as {
    format?: string;
    version?: number;
    kdf?: { name?: string; hash?: string; iterations?: number; salt?: string };
    encryption?: { name?: string; iv?: string };
    ciphertext?: string;
  };
  if (envelope.format !== 'openlain5g-encrypted-sim-credentials' || envelope.version !== 1
    || envelope.kdf?.name !== 'PBKDF2' || envelope.kdf.hash !== 'SHA-256'
    || envelope.kdf.iterations !== PBKDF2_ITERATIONS || envelope.encryption?.name !== 'AES-GCM'
    || !envelope.kdf.salt || !envelope.encryption.iv || !envelope.ciphertext) {
    throw new Error('That credential backup is not a valid OpenLain5G file.');
  }
  const material = await crypto.subtle.importKey('raw', new TextEncoder().encode(passphrase), 'PBKDF2', false, ['deriveKey']);
  const key = await crypto.subtle.deriveKey(
    { name: 'PBKDF2', salt: fromBase64(envelope.kdf.salt), iterations: PBKDF2_ITERATIONS, hash: 'SHA-256' },
    material,
    { name: 'AES-GCM', length: 256 },
    false,
    ['decrypt'],
  );
  const plaintext = await crypto.subtle.decrypt(
    { name: 'AES-GCM', iv: fromBase64(envelope.encryption.iv) },
    key,
    fromBase64(envelope.ciphertext),
  );
  const saved = JSON.parse(new TextDecoder().decode(plaintext)) as SimFields & { format?: string; version?: number };
  if (saved.format !== 'openlain5g-sim-credentials' || saved.version !== 1
    || !/^\d{3}$/.test(saved.mcc) || !/^\d{2,3}$/.test(saved.mnc)
    || !/^\d{15}$/.test(saved.imsi) || !saved.imsi.startsWith(saved.mcc + saved.mnc)
    || !hasValidIccidCheckDigit(saved.iccid) || !/^[0-9a-fA-F]{32}$/.test(saved.ki)
    || !/^[0-9a-fA-F]{32}$/.test(saved.opc)) {
    throw new Error('The backup could not be decrypted. Check the passphrase and file.');
  }
  return { mcc: saved.mcc, mnc: saved.mnc, imsi: saved.imsi, iccid: saved.iccid, ki: saved.ki, opc: saved.opc };
}

export function SimProgrammerPage() {
  const [status, setStatus] = useState<ReaderStatus | null>(null);
  const [selectedReader, setSelectedReader] = useState<number | null>(null);
  const [card, setCard] = useState<CardStatus | null>(null);
  const [fields, setFields] = useState(EMPTY_FIELDS);
  const [adm, setAdm] = useState('');
  const [confirmed, setConfirmed] = useState(false);
  const [result, setResult] = useState<ProgramResult | null>(null);
  const [busy, setBusy] = useState<'refresh' | 'inspect' | 'program' | null>(null);
  const [error, setError] = useState('');
  const [backupPassphrase, setBackupPassphrase] = useState('');
  const [backupSaved, setBackupSaved] = useState(false);
  const [backupFile, setBackupFile] = useState<File | null>(null);
  const [restorePassphrase, setRestorePassphrase] = useState('');
  const [restoreMessage, setRestoreMessage] = useState('');
  const [revealingKeys, setRevealingKeys] = useState(false);
  const [showWriteConfirm, setShowWriteConfirm] = useState(false);

  const refreshReaders = useCallback(async () => {
    setBusy('refresh');
    setError('');
    try {
      const response = await apiRequest<ReaderStatus>('/api/sim-programmer/status');
      setStatus(response);
      setSelectedReader((current) => current !== null && current < response.readers.length ? current : (response.readers.length ? 0 : null));
      setCard(null);
    } catch {
      setStatus(null);
      setError('Could not read SIM programmer status from the backend.');
    } finally {
      setBusy(null);
    }
  }, []);

  useEffect(() => { void refreshReaders(); }, [refreshReaders]);

  async function inspectCard() {
    if (selectedReader === null) return;
    setBusy('inspect');
    setError('');
    setCard(null);
    try {
      const response = await apiRequest<CardStatus>('/api/sim-programmer/inspect', {
        method: 'POST',
        body: JSON.stringify({ reader_index: selectedReader }),
      });
      setCard(response);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Could not inspect the selected reader.');
    } finally {
      setBusy(null);
    }
  }

  function updateField(field: keyof SimFields, value: string) {
    setFields((current) => ({ ...current, [field]: value }));
    setResult(null);
    setBackupSaved(false);
  }

  const credentialsValid = Boolean(
    fields.mcc.match(/^\d{3}$/)
      && fields.mnc.match(/^\d{2,3}$/)
      && fields.imsi.match(/^\d{15}$/)
      && fields.imsi.startsWith(fields.mcc + fields.mnc)
      && hasValidIccidCheckDigit(fields.iccid)
      && fields.ki.match(/^[0-9a-fA-F]{32}$/)
      && fields.opc.match(/^[0-9a-fA-F]{32}$/)
      && adm.match(/^\d{1,8}$/),
  );
  const credentialIssues = [
    fields.mcc && !/^\d{3}$/.test(fields.mcc) ? 'MCC must contain 3 digits.' : '',
    fields.mnc && !/^\d{2,3}$/.test(fields.mnc) ? 'MNC must contain 2 or 3 digits.' : '',
    fields.imsi && (!/^\d{15}$/.test(fields.imsi) || !fields.imsi.startsWith(fields.mcc + fields.mnc)) ? 'IMSI must contain 15 digits and start with MCC + MNC.' : '',
    fields.iccid && !hasValidIccidCheckDigit(fields.iccid) ? 'ICCID must contain 19 digits with a valid check digit.' : '',
    fields.ki && !/^[0-9a-fA-F]{32}$/.test(fields.ki) ? 'Ki must be a 128-bit hexadecimal key.' : '',
    fields.opc && !/^[0-9a-fA-F]{32}$/.test(fields.opc) ? 'OPc must be a 128-bit hexadecimal value.' : '',
    adm && !/^\d{1,8}$/.test(adm) ? 'ADM1 must contain 1 to 8 digits.' : '',
  ].filter(Boolean);
  const canProgram = Boolean(status?.available && status.programming_enabled && card?.supported && credentialsValid && confirmed && busy === null);

  async function programCard() {
    if (selectedReader === null || !canProgram) return;
    setBusy('program');
    setError('');
    setResult(null);
    setConfirmed(false);
    const submittedAdm = adm;
    setAdm('');
    try {
      const response = await apiRequest<ProgramResult>('/api/sim-programmer/program', {
        method: 'POST',
        body: JSON.stringify({ ...fields, adm: submittedAdm, reader_index: selectedReader, confirm: true }),
      });
      setResult(response);
      setBackupPassphrase('');
      setBackupSaved(false);
      setCard(null);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'SIM programming did not complete.');
    } finally {
      setBusy(null);
    }
  }

  async function saveEncryptedBackup() {
    try {
      await downloadEncryptedCredentials(fields, backupPassphrase);
      setBackupSaved(true);
      setBackupPassphrase('');
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Could not encrypt the credential backup.');
    }
  }

  async function restoreEncryptedBackup() {
    if (!backupFile || restorePassphrase.length < 12) return;
    setError('');
    setRestoreMessage('');
    try {
      const restored = await decryptCredentials(backupFile, restorePassphrase);
      setFields(restored);
      setCard(null);
      setResult(null);
      setAdm('');
      setConfirmed(false);
      setRevealingKeys(false);
      setRestoreMessage('Credentials decrypted in this browser and loaded into the form. They were not sent to the backend.');
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Could not decrypt the credential backup.');
    } finally {
      setRestorePassphrase('');
    }
  }

  const setReady = status?.available && status.readers.length > 0;
  return <section className="page-panel sim-programmer-page">
    <header className="page-heading">
      <div><span className="eyebrow">Subscriber tools</span><h1>SIM Programmer</h1><p className="page-subtitle">Write a supported physical test USIM and keep its network credentials available for later subscriber setup.</p></div>
      <ActionButton variant="secondary" onClick={() => void refreshReaders()} loading={busy === 'refresh'}><RefreshCw size={15} />Refresh reader</ActionButton>
    </header>

    <section className={`sim-bridge-status ${setReady ? 'ready' : ''}`} aria-live="polite">
      <span className="sim-bridge-icon"><Usb size={20} /></span>
      <div><strong>{busy === 'refresh' && !status ? 'Checking PC/SC bridge' : status?.available ? (setReady ? 'PC/SC reader available' : 'No reader detected') : 'PC/SC bridge offline'}</strong><p>{status?.message || 'Checking the local PC/SC bridge…'}</p></div>
      <span className={`status-badge ${setReady ? 'status-pass' : 'status-not-tested'}`}>{setReady ? `${status?.readers.length} reader${status?.readers.length === 1 ? '' : 's'}` : 'Unavailable'}</span>
    </section>

    {!status?.programming_enabled ? <div className="sim-inline-note"><CircleAlert size={17} /><p>SIM writes are disabled. Run <code>./lain5g app start --operations --open</code> once to start the application and its protected local SIM reader bridge.</p></div> : null}
    {status?.programming_enabled && !status.available ? <div className="sim-inline-note"><CircleAlert size={17} /><p>The local PC/SC bridge did not respond. Run <code>./install.sh</code> to prepare the host reader service, then restart OpenLain5G with <code>./lain5g app start --operations</code>. Check <code>./lain5g app logs</code> if it remains offline.</p></div> : null}
    {status?.available && !status.readers.length ? <div className="sim-inline-note"><CircleAlert size={17} /><p>No PC/SC reader is available. Connect a supported reader and refresh. If the reader stays unavailable, run <code>./install.sh</code> to prepare PC/SC, then restart the app.</p></div> : null}
    {error ? <div className="sim-error" role="alert"><CircleAlert size={17} /><span>{error}</span></div> : null}

    <div className="sim-programmer-grid">
      <section className="panel">
        <div className="panel-heading"><div><span className="eyebrow">1 · Hardware</span><h2>Select and inspect card</h2></div><Cpu size={21} /></div>
        <p className="muted-text">Detects sysmoUSIM-SJS1, sysmoISIM-SJA2, and sysmoISIM-SJA5 cards. This version writes only sysmoUSIM-SJS1; recognized newer models remain read-only here. Commercial SIMs and eSIM profiles are not written.</p>
        <label>PC/SC reader<select value={selectedReader ?? ''} disabled={!status?.readers.length || busy !== null} onChange={(event) => { setSelectedReader(event.target.value === '' ? null : Number(event.target.value)); setCard(null); setResult(null); }}><option value="">Select a reader</option>{status?.readers.map((reader, index) => <option value={index} key={`${index}-${reader}`}>{reader}</option>)}</select></label>
        <div className="actions-row"><ActionButton variant="secondary" disabled={selectedReader === null || busy !== null} loading={busy === 'inspect'} onClick={() => void inspectCard()}>Detect card</ActionButton></div>
        {card ? <div className={`sim-card-detection ${card.supported ? 'ready' : card.recognized ? 'recognized' : 'unsupported'}`}><strong>{card.card || (card.detected ? 'Unknown card detected' : 'No card detected')}</strong><span>{card.reader}</span><p>{card.message}</p></div> : null}
      </section>

      <section className="panel sim-program-fields">
        <div className="panel-heading"><div><span className="eyebrow">2 · Network identity</span><h2>SIM credentials</h2></div><KeyRound size={21} /></div>
        <p className="muted-text">Use values for your private network. IMSI must start with MCC + MNC and be unique in your core. Ki and OPc are generated only in this browser unless you enter your own.</p>
        <div className="sim-fields-grid">
          <label>MCC<input disabled={busy !== null} inputMode="numeric" autoComplete="off" maxLength={3} value={fields.mcc} onChange={(event) => updateField('mcc', event.target.value.replace(/\D/g, ''))} placeholder="3 digits" /></label>
          <label>MNC<input disabled={busy !== null} inputMode="numeric" autoComplete="off" maxLength={3} value={fields.mnc} onChange={(event) => updateField('mnc', event.target.value.replace(/\D/g, ''))} placeholder="2 or 3 digits" /></label>
          <label className="wide">IMSI<input disabled={busy !== null} inputMode="numeric" autoComplete="off" maxLength={15} value={fields.imsi} onChange={(event) => updateField('imsi', event.target.value.replace(/\D/g, ''))} placeholder="15 digits" /></label>
          <label className="wide">ICCID<input disabled={busy !== null} inputMode="numeric" autoComplete="off" maxLength={19} value={fields.iccid} onChange={(event) => updateField('iccid', event.target.value.replace(/\D/g, ''))} placeholder="19 digits" /></label>
          <label>Ki<input disabled={busy !== null} type={revealingKeys ? 'text' : 'password'} autoComplete="new-password" spellCheck={false} maxLength={32} value={fields.ki} onChange={(event) => updateField('ki', event.target.value.replace(/[^\da-f]/gi, ''))} placeholder="128-bit key · hex" /></label>
          <label>OPc<input disabled={busy !== null} type={revealingKeys ? 'text' : 'password'} autoComplete="new-password" spellCheck={false} maxLength={32} value={fields.opc} onChange={(event) => updateField('opc', event.target.value.replace(/[^\da-f]/gi, ''))} placeholder="128-bit OPc · hex" /></label>
        </div>
        <label className="sim-confirm-check sim-reveal-check"><input type="checkbox" checked={revealingKeys} onChange={(event) => setRevealingKeys(event.target.checked)} />Reveal Ki and OPc on this screen for manual subscriber setup.</label>
        <div className="actions-row sim-generate-actions"><ActionButton variant="secondary" disabled={busy !== null} onClick={() => { updateField('iccid', makeIccid()); }}><RefreshCw size={15} />Generate ICCID</ActionButton><ActionButton variant="secondary" disabled={busy !== null} onClick={() => { updateField('ki', randomHex(16)); updateField('opc', randomHex(16)); }}><KeyRound size={15} />Generate Ki + OPc</ActionButton></div>
        <label className="sim-adm-field">Card ADM1<input disabled={busy !== null} type="password" inputMode="numeric" autoComplete="off" maxLength={8} value={adm} onChange={(event) => setAdm(event.target.value.replace(/\D/g, ''))} placeholder="Provided with your programmable SIM" /><small>Do not guess the ADM code. Incorrect attempts can lock card administration.</small></label>
        {credentialIssues.length ? <ul className="sim-validation-list" aria-live="polite">{credentialIssues.map((issue) => <li key={issue}>{issue}</li>)}</ul> : null}
      </section>
    </div>

    <section className="panel sim-write-panel">
      <div className="panel-heading"><div><span className="eyebrow">3 · Program card</span><h2>Review before writing</h2></div><ShieldAlert size={22} /></div>
      <div className="sim-write-warning"><ShieldAlert size={18} /><p>Writing changes the inserted physical SIM. The operation requires its ADM1 code and may partially modify the card if communication is interrupted. Keep Ki and OPc matched to the subscriber record in your core.</p></div>
      <p className="sim-write-gate">{!status?.programming_enabled ? 'Enable local operations to allow physical SIM writes.' : !status.available ? 'The SIM bridge is offline. Prepare PC/SC with ./install.sh and restart the app in operations mode.' : selectedReader === null ? 'Select a connected PC/SC reader.' : !card ? 'Detect the inserted card before entering the ADM code.' : !card.supported ? card.recognized ? `${card.card} is recognized, but writing for this model is not enabled in this version.` : 'Insert a recognized and supported test USIM.' : !credentialsValid ? 'Complete all fields with valid values before writing.' : !confirmed ? 'Confirm that you inserted the intended card and reviewed the values.' : 'Card and subscriber credentials are ready for final confirmation.'}</p>
      <label className="sim-confirm-check"><input type="checkbox" disabled={busy !== null} checked={confirmed} onChange={(event) => setConfirmed(event.target.checked)} />I inserted the intended supported test USIM and reviewed the values above.</label>
      <div className="actions-row"><ActionButton disabled={!canProgram} loading={busy === 'program'} onClick={() => setShowWriteConfirm(true)}><Usb size={15} />Review and write</ActionButton><span className="muted-text">The ADM code is cleared from the form after submission.</span></div>
    </section>

    {result ? <section className="panel sim-success-panel"><div className="panel-heading"><div><span className="eyebrow">Write completed</span><h2>Card verified</h2></div><Check size={22} /></div><p>{result.message} Read-back matched {result.verified_fields.join(', ')}.</p><dl className="sim-result-identities"><div><dt>IMSI</dt><dd>{result.imsi}</dd></div><div><dt>ICCID</dt><dd>{result.iccid}</dd></div><div><dt>Card</dt><dd>{result.card}</dd></div></dl><p className="muted-text">Ki and OPc are not saved by OpenLain5G and are never returned by the backend. Download an encrypted local backup so you can provision the matching subscriber later.</p><div className="sim-backup-controls"><label>Backup passphrase<input type="password" autoComplete="new-password" minLength={12} value={backupPassphrase} onChange={(event) => setBackupPassphrase(event.target.value)} placeholder="At least 12 characters" /></label><ActionButton variant="secondary" disabled={backupPassphrase.length < 12 || backupSaved} onClick={() => void saveEncryptedBackup()}><Download size={15} />{backupSaved ? 'Encrypted backup saved' : 'Download encrypted backup'}</ActionButton></div></section> : null}

    <section className="panel sim-restore-panel"><div className="panel-heading"><div><span className="eyebrow">Local credential file</span><h2>Restore an encrypted backup</h2></div><KeyRound size={20} /></div><p className="muted-text">Choose an OpenLain5G encrypted file and enter its passphrase. Decryption stays in this browser; restored credentials are not sent until you explicitly program a card.</p><div className="sim-backup-controls"><label>Encrypted backup file<input type="file" accept="application/json,.json" onChange={(event) => { setBackupFile(event.target.files?.[0] || null); setRestoreMessage(''); }} /></label><label>Backup passphrase<input type="password" autoComplete="new-password" minLength={12} value={restorePassphrase} onChange={(event) => setRestorePassphrase(event.target.value)} placeholder="At least 12 characters" /></label><ActionButton variant="secondary" disabled={!backupFile || restorePassphrase.length < 12} onClick={() => void restoreEncryptedBackup()}>Decrypt in browser</ActionButton></div>{restoreMessage ? <p className="sim-restore-success" role="status">{restoreMessage}</p> : null}</section>

    <section className="sim-programmer-steps"><span className="eyebrow">Before you start</span><ol><li>Connect a compatible USB SIM reader to this Linux host.</li><li>Run <code>./install.sh</code> once to prepare the host reader service. Then <code>./lain5g app start --operations --open</code> starts the web app and protected SIM bridge together.</li><li>Use the same MCC, MNC, IMSI, Ki, and OPc when you add the subscriber to Open5GS.</li></ol></section>
    <ConfirmDialog open={showWriteConfirm} title="Write the physical SIM?" message="This updates the inserted sysmoUSIM-SJS1 card. Confirm the reader, values, and ADM1 before proceeding." confirmLabel="Write SIM" onConfirm={() => { setShowWriteConfirm(false); void programCard(); }} onCancel={() => setShowWriteConfirm(false)} />
  </section>;
}
