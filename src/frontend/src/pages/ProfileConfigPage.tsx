import { useEffect, useState } from 'react';
import { ConfirmDialog } from '../components/ConfirmDialog';
import { ErrorAlert } from '../components/ErrorAlert';
import { LoadingState } from '../components/LoadingState';
import { StatusBadge } from '../components/StatusBadge';
import { useProfile, useProfileActions, useProfileBackup, useProfiles } from '../hooks/useProfiles';
import { useSubscribers } from '../hooks/useSubscribers';
import type { ProfileConfig, ProfileSummary } from '../types/profile';
import type { SubscriberSummary } from '../types/subscriber';
import { getScenarioGuidance } from '../utils/scenarioGuidance';

const sections: Record<string, Array<[string, string, string]>> = {
  Network: [['network.mcc', 'MCC', 'text'], ['network.mnc', 'MNC', 'text'], ['network.tac', 'TAC', 'number'], ['network.dnn', 'DNN', 'text'], ['network.dnn_internet', 'Internet DNN', 'text'], ['network.dnn_ims', 'IMS DNN', 'text'], ['network.apn_internet', 'Internet APN', 'text'], ['network.apn_ims', 'IMS APN', 'text'], ['network.slice.sst', 'SST', 'number'], ['network.slice.sd', 'SD', 'text']],
  Core: [['core.amf_addr', 'AMF address', 'text'], ['core.gnb_addr', 'gNB address', 'text'], ['core.mme_addr', 'MME address', 'text'], ['core.gnb_bind_addr', 'gNB bind address', 'text'], ['core.n3_bind_addr', 'N3 bind address', 'text']],
  Subscriber: [['subscriber.imsi', 'IMSI', 'text'], ['subscriber.msisdn', 'MSISDN', 'text']],
  IMS: [['ims.domain', 'IMS domain', 'text']],
  Radio: [['ran.enb_bind_addr', 'eNB bind address', 'text'], ['ran.dl_earfcn', 'DL EARFCN', 'number'], ['ran.tx_gain', 'TX gain', 'number'], ['ran.rx_gain', 'RX gain', 'number'], ['radio.device', 'UHD device type', 'text'], ['radio.usrp_addr', 'USRP address', 'text'], ['radio.lte_band', 'LTE anchor band', 'number'], ['radio.earfcn', 'LTE anchor EARFCN', 'number'], ['radio.bandwidth_mhz', 'Bandwidth MHz', 'number'], ['radio.band', 'NR band', 'number'], ['radio.dl_arfcn', 'DL ARFCN', 'number'], ['radio.nr_band', 'NR secondary band', 'number'], ['radio.nr_dl_arfcn', 'NR DL ARFCN', 'number'], ['radio.subcarrier_spacing_khz', 'NR subcarrier spacing kHz', 'number'], ['radio.tx_gain', 'TX gain', 'number'], ['radio.rx_gain', 'RX gain', 'number'], ['radio.clock_source', 'Clock source', 'text'], ['radio.time_source', 'Time source', 'text']],
  'RF safety': [['safety.environment', 'Laboratory mode', 'environment'], ['safety.attenuation_db', 'Attenuation dB', 'number'], ['safety.antenna_connected', 'Antenna connected', 'boolean'], ['safety.nr_rf_path_connected', 'NR RF path connected', 'boolean'], ['safety.shielded_environment', 'Shielded environment', 'boolean'], ['safety.auto_stop', 'Auto-stop enabled', 'boolean'], ['safety.authorization_confirmed', 'RF authorization confirmed', 'boolean'], ['safety.authorized_lab_frequencies', 'All carrier frequencies authorized', 'boolean'], ['safety.operator_note', 'Authorization note', 'text'], ['safety.maximum_duration_seconds', 'Maximum duration', 'number']],
};
const fixedLteTopologyFields = new Set(['core.mme_addr', 'ran.enb_bind_addr']);

export function ProfileConfigPage() {
  const profiles = useProfiles();
  const [selected, setSelected] = useState<string | null>(null);
  const [draft, setDraft] = useState<ProfileConfig | null>(null);
  const [applyOpen, setApplyOpen] = useState(false);
  const [restoreOpen, setRestoreOpen] = useState(false);
  const profile = useProfile(selected);
  const actions = useProfileActions(selected);
  const backup = useProfileBackup(selected);
  const subscribers = useSubscribers({ limit: 100, offset: 0, profile: '4g-lte-x310' });
  useEffect(() => { if (!selected && profiles.data?.length) setSelected(profiles.data[0].profile); }, [profiles.data, selected]);
  useEffect(() => { if (profile.data) setDraft(structuredClone(profile.data)); }, [profile.data]);
  const dirty = Boolean(draft && profile.data && JSON.stringify(draft) !== JSON.stringify(profile.data));
  const sharesLteEnvironment = selected === '4g-lte-sim' || selected === '4g-lte-x310';
  const save = async () => { if (draft) { await actions.update.mutateAsync(draft); actions.validate.reset(); actions.diff.reset(); actions.apply.reset(); } };
  const validate = async () => actions.validate.mutateAsync();
  const compare = async () => actions.diff.mutateAsync();
  const requestApply = async () => { const result = await validate(); if (result.valid) setApplyOpen(true); };
  const errors = actions.update.error || actions.validate.error || actions.diff.error || actions.apply.error || actions.restore.error || backup.error;

  return <section className="page-panel"><div className="page-heading"><div><span className="eyebrow">LAB PROFILE WIZARD</span><h1>Choose and configure</h1><p className="page-subtitle">Start from a working simulation or guarded RF profile, then review network, TX/RX and safety values before applying.</p></div>{dirty ? <StatusBadge status="warning" /> : <span className="mode-indicator">No unsaved changes</span>}</div>
    {profiles.isLoading ? <LoadingState /> : null}{profiles.error ? <ErrorAlert error={profiles.error} /> : null}{profiles.data ? <div className="profile-groups"><ProfileGroup title="Simulated, no RF" description="Learn and validate the core over virtual radio. These profiles require no USRP and do not transmit over an antenna." kind="simulation" items={profiles.data.filter((item) => !item.rf_capable)} selected={selected} onSelect={setSelected} /><ProfileGroup title="Guarded real RF" description="X-Series profiles with TX/RX, channel plan, attenuation, authorization, and automatic stop." kind="rf" items={profiles.data.filter((item) => item.rf_capable)} selected={selected} onSelect={setSelected} /></div> : null}
    {profile.isLoading ? <LoadingState /> : null}{profile.error ? <ErrorAlert error={profile.error} /> : null}{errors ? <ErrorAlert error={errors} /> : null}
    {draft ? <div className="page-grid" style={{ marginTop: 18 }}><section className="panel wide"><div className="panel-heading"><div><h3>Configuration editor · {getScenarioGuidance(selected || '')?.profileTitle || selected}</h3><span className="muted-text">Edits stay in this form until you save. Save sends this profile to the backend. Compare, Validate and Apply use the saved profile; Apply writes only the files listed in the change review. This edits the selected profile, not the Active Scenario, and does not start or restart services.</span>{sharesLteEnvironment ? <span className="muted-text">This LTE profile shares deployments/4g-volte/common/.env with the other LTE profile; applying shared network or subscriber values can affect both.</span> : null}</div><div className="inline-actions"><button className="secondary" onClick={() => profile.data && setDraft(structuredClone(profile.data))}>Discard changes</button><button className="secondary" onClick={compare} disabled={dirty || actions.diff.isPending}>Compare changes</button><button className="secondary" onClick={validate} disabled={dirty || actions.validate.isPending}>Validate configuration</button><button onClick={save} disabled={!dirty || actions.update.isPending}>Save draft</button><button onClick={requestApply} disabled={dirty || actions.apply.isPending}>Apply to scenario</button><button className="secondary" onClick={() => setRestoreOpen(true)} disabled={dirty || actions.restore.isPending || !backup.data?.backup}>{backup.isLoading ? 'Checking backup…' : 'Restore latest backup'}</button></div></div>{dirty ? <p className="muted-text" role="status">Save or discard these edits before comparing, validating, applying or restoring.</p> : null}{backup.data?.backup ? <p className="muted-text">Latest backup: <code>{backup.data.backup}</code></p> : null}{actions.apply.data ? <div className="ims-result">Configuration applied. The effective scenario files now match this profile.</div> : null}{actions.restore.data ? <div className="ims-result">Deployed files restored from {actions.restore.data.backup}.</div> : null}<ProfileForm draft={draft} setDraft={setDraft} validationErrors={actions.validate.data?.errors || []} subscribers={subscribers.data?.items || []} subscribersUnavailable={Boolean(subscribers.error)} subscribersLoading={subscribers.isLoading} /></section>
      <section className="panel"><h3>Validation result</h3>{actions.validate.data ? <><StatusBadge status={actions.validate.data.valid ? 'PASS' : 'FAIL'} kind="validation" />{actions.validate.data.errors.length ? <><p>Fix the highlighted fields, then validate again.</p><ul>{actions.validate.data.errors.map((error) => <li key={error}>{error}</li>)}</ul></> : <p className="muted-text">Profile schema accepted by backend validation.</p>}</> : <div className="empty-state"><h3>Not validated</h3><p>Validate before applying deployment changes.</p></div>}</section>
      <section className="panel"><h3>Change review</h3>{actions.diff.data ? <>{actions.diff.data.files.filter((file) => file.changed).length ? <ul>{actions.diff.data.files.filter((file) => file.changed).map((file) => <li key={file.path}><code>{file.path}</code></li>)}</ul> : <p className="muted-text">No generated deployment file changes.</p>}<details className="technical-output"><summary>Unified diff</summary><pre>{actions.diff.data.files.map((file) => file.diff).join('\n')}</pre></details></> : <div className="empty-state"><h3>No diff loaded</h3><p>Compare changes to inspect generated deployment files.</p></div>}</section></div> : null}
    <ConfirmDialog open={applyOpen} title={`Apply configuration to ${selected || 'profile'}`} message={`Validated values for ${selected || 'this profile'} will be written only to its generated files listed in Change review. This does not change the Active Scenario, start or restart services, or transmit RF.`} confirmLabel="Apply configuration" onConfirm={async () => { await actions.apply.mutateAsync(); actions.diff.reset(); setApplyOpen(false); }} onCancel={() => setApplyOpen(false)} />
    <ConfirmDialog open={restoreOpen} title={`Restore ${selected || 'profile'} deployment files`} message={`Restore ${backup.data?.backup || 'the latest backup'} to this profile's generated files? The saved profile YAML stays unchanged, and services are not restarted.`} confirmLabel="Restore backup" onConfirm={async () => { await actions.restore.mutateAsync(); actions.diff.reset(); setRestoreOpen(false); }} onCancel={() => setRestoreOpen(false)} />
  </section>;
}

function ProfileGroup({ title, description, kind, items, selected, onSelect }: { title: string; description: string; kind: 'simulation' | 'rf'; items: ProfileSummary[]; selected: string | null; onSelect: (profile: string) => void }) {
  return <section className={`profile-group profile-group-${kind}`}><div className="profile-group-heading"><span className="profile-group-mark">{kind === 'simulation' ? 'SIM' : 'RF'}</span><div><h2>{title}</h2><p>{description}</p></div></div><div className="scenario-grid profile-catalog">{items.map((item) => { const guidance = getScenarioGuidance(item.profile); return <button key={item.profile} className={`panel scenario-card profile-choice ${selected === item.profile ? 'selected' : ''}`} onClick={() => onSelect(item.profile)}><div className="scenario-meta"><span className="eyebrow">{guidance ? `${guidance.generation} · ${guidance.variant}` : kind === 'rf' ? 'GUARDED RF PROFILE' : 'SIMULATED PROFILE'}</span><span className="profile-mode-dot">{kind === 'rf' ? 'RF' : 'SIM'}</span></div><strong>{guidance?.profileTitle || item.profile}</strong><code>{item.profile}</code><p>{guidance?.purpose}</p><span className="profile-card-footnote">{kind === 'rf' ? `RF transmission: ${item.rf_allowed ? 'enabled locally' : 'blocked by default'}` : 'Virtual radio: no SDR or RF transmission'}</span></button>; })}</div></section>;
}

function ProfileForm({ draft, setDraft, validationErrors, subscribers, subscribersUnavailable, subscribersLoading }: { draft: ProfileConfig; setDraft: (value: ProfileConfig) => void; validationErrors: string[]; subscribers: SubscriberSummary[]; subscribersUnavailable: boolean; subscribersLoading: boolean }) {
  const selectedSubscriber = subscribers.find((item) => item.imsi === draft.subscriber?.imsi);
  const requiredServices = [draft.network?.apn_internet, draft.network?.dnn_internet, draft.network?.dnn, draft.network?.apn_ims, draft.network?.dnn_ims].filter((value): value is string => typeof value === 'string' && value.length > 0);
  const missingServices = selectedSubscriber ? requiredServices.filter((service) => !(selectedSubscriber.apns || []).includes(service)) : [];
  return (
    <div className="profile-form">
      {Object.entries(sections).map(([section, fields]) => {
        const visible = fields.filter(([path]) => hasPath(draft, path) && !(draft.profile === '4g-lte-x310' && fixedLteTopologyFields.has(path)));
        if (!visible.length) return null;
        return (
          <fieldset key={section} className="form-section">
            <legend>{section}</legend>
            {section === 'Network' && hasPath(draft, 'network.mcc') && hasPath(draft, 'network.mnc') ? (
              <label>
                <span>Network identity preset</span>
                <select aria-label="Network identity preset" value={draft.network.mcc === '001' && draft.network.mnc === '01' ? 'lab' : 'custom'} onChange={(event) => { if (event.target.value === 'lab') setDraft(setPath(setPath(draft, 'network.mcc', '001'), 'network.mnc', '01')); }}>
                  <option value="lab">Private lab PLMN · 001 / 01</option>
                  <option value="custom">Custom MCC/MNC</option>
                </select>
                <small>Use 001/01 only for an isolated lab network.</small>
              </label>
            ) : null}
            {visible.map(([path, label, type]) => {
              const current = getPath(draft, path);
              const error = fieldError(path, validationErrors);
              const dnnField = ['network.apn_internet', 'network.apn_ims', 'network.dnn', 'network.dnn_internet', 'network.dnn_ims'].includes(path);
              const preset = path.endsWith('_ims') ? 'ims' : 'internet';
              const presetValue = current === preset ? preset : 'custom';
              const update = (value: unknown) => setDraft(setPath(draft, path, value));
              return (
                <div className="profile-editor-field" key={path}>
                  <label htmlFor={`${path}-value`}>{label}</label>
                  {path === 'subscriber.imsi' ? (
                    <>
                      <select aria-label="Select existing subscriber" value={current && subscribers.some((item) => item.imsi === current) ? current : ''} onChange={(event) => { if (event.target.value) update(event.target.value); }}>
                        <option value="">Choose from Subscribers…</option>
                        {current && !subscribers.some((item) => item.imsi === current) ? <option value={current}>Current profile IMSI · {current}</option> : null}
                        {subscribers.map((item) => <option key={item.imsi} value={item.imsi}>{item.imsi}{item.msisdn ? ` · ${item.msisdn}` : ''}</option>)}
                      </select>
                      <input id={`${path}-value`} type="text" value={valueToInput(current)} onChange={(event) => update(inputToValue(event.target.value, current))} aria-invalid={Boolean(error)} aria-describedby={error ? `${path}-error` : undefined} />
                      {subscribersLoading ? <small>Loading saved subscribers…</small> : subscribersUnavailable ? <small>Subscriber list is unavailable. You can still enter an IMSI manually.</small> : subscribers.length === 0 ? <small>No saved subscribers were found. You can still enter an IMSI manually.</small> : <small>Selection updates this profile’s IMSI only. It does not provision the target core or expose subscriber credentials.</small>}
                      {selectedSubscriber && missingServices.length ? <small role="status">This subscriber does not list {missingServices.join(', ')}. Confirm its subscribed services before applying.</small> : null}
                    </>
                  ) : type === 'boolean' ? (
                    <select id={`${path}-value`} value={String(current)} onChange={(event) => update(event.target.value === 'true')}><option value="true">Yes</option><option value="false">No</option></select>
                  ) : type === 'environment' ? (
                    <select id={`${path}-value`} value={valueToInput(current)} onChange={(event) => update(event.target.value)}><option value="cabled">Cabled</option><option value="shielded">Shielded</option><option value="authorized">Authorized environment</option></select>
                  ) : (
                    <>
                      {dnnField ? <select aria-label={`${label} preset`} value={presetValue} onChange={(event) => { if (event.target.value !== 'custom') update(event.target.value); }}><option value={preset}>{preset === 'ims' ? 'IMS voice · ims' : 'Internet data · internet'}</option><option value="custom">Custom value</option></select> : null}
                      <input id={`${path}-value`} type={type} value={valueToInput(current)} onChange={(event) => update(inputToValue(event.target.value, current))} aria-invalid={Boolean(error)} aria-describedby={error ? `${path}-error` : undefined} />
                      {dnnField ? <small>Use the same APN/DNN name provisioned for the selected subscriber and core.</small> : null}
                    </>
                  )}
                  {error ? <small className="field-error" id={`${path}-error`}>{error}</small> : null}
                </div>
              );
            })}
          </fieldset>
        );
      })}
    </div>
  );
}

function fieldError(path: string, errors: string[]) {
  const name = path.split('.').at(-1) || path;
  const words: Record<string, string[]> = { mcc: ['mcc'], mnc: ['mnc'], tac: ['tac'], dnn: ['dnn'], dnn_internet: ['dnn_internet'], dnn_ims: ['dnn_ims'], apn_internet: ['apn_internet'], apn_ims: ['apn_ims'], sst: ['sst'], sd: ['sd'], imsi: ['imsi'], msisdn: ['msisdn'], earfcn: ['earfcn'], nr_dl_arfcn: ['nr_dl_arfcn'], bandwidth_mhz: ['bandwidth'], tx_gain: ['tx gain', 'tx_gain'], rx_gain: ['rx gain', 'rx_gain'], attenuation_db: ['attenuation'], maximum_duration_seconds: ['maximum_duration', 'duration'], environment: ['environment', 'laboratory mode'], auto_stop: ['auto_stop'], authorization_confirmed: ['authorization'], authorized_lab_frequencies: ['authorized_lab_frequencies'], nr_rf_path_connected: ['nr_rf_path_connected'] };
  return errors.find((error) => (words[name] || [name]).some((word) => error.toLowerCase().includes(word.toLowerCase())));
}

function hasPath(data: any, path: string) { return path.split('.').every((part) => { if (!data || !(part in data)) return false; data = data[part]; return true; }); }
function getPath(data: any, path: string) { return path.split('.').reduce((value, part) => value?.[part], data); }
function setPath(data: any, path: string, value: any) { const copy = structuredClone(data); const parts = path.split('.'); let target = copy; for (const part of parts.slice(0, -1)) target = target[part]; target[parts.at(-1)!] = value; return copy; }
function valueToInput(value: any) { return value === null || value === undefined ? '' : String(value); }
function inputToValue(value: string, previous: any) { if (value === '') return null; if (typeof previous === 'boolean') return ['true', 'yes', '1'].includes(value.toLowerCase()); return typeof previous === 'number' ? Number(value) : value; }
