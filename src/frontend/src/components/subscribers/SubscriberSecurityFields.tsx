interface SubscriberSecurityFieldsProps {
  showSecrets: boolean;
  editing: boolean;
  values: Record<string, string>;
  errors: Record<string, string>;
  onChange: (name: string, value: string) => void;
  onToggle: () => void;
}

export function SubscriberSecurityFields({ showSecrets, editing, values, errors, onChange, onToggle }: SubscriberSecurityFieldsProps) {
  const type = showSecrets ? 'text' : 'password';
  return (
    <fieldset className="form-section">
      <legend>Authentication</legend>
      <p className="muted-text">Existing secrets are never prefilled. While editing, leave K/OP/OPc empty to preserve the current value.</p>
      <button type="button" className="secondary" onClick={onToggle}>{showSecrets ? 'Hide secrets' : 'Show secrets while typing'}</button>
      <label>K {editing ? '' : '*'}<input type={type} value={values.k} onChange={(event) => onChange('k', event.target.value)} autoComplete="off" /></label>
      {errors.k ? <p className="field-error">{errors.k}</p> : null}
      <label>OP<input type={type} value={values.op} onChange={(event) => onChange('op', event.target.value)} autoComplete="off" /></label>
      {errors.op ? <p className="field-error">{errors.op}</p> : null}
      <label>OPc<input type={type} value={values.opc} onChange={(event) => onChange('opc', event.target.value)} autoComplete="off" /></label>
      {errors.opc ? <p className="field-error">{errors.opc}</p> : null}
      <label>AMF<input value={values.amf} onChange={(event) => onChange('amf', event.target.value)} /></label>
      {errors.amf ? <p className="field-error">{errors.amf}</p> : null}
      <label>SQN<input value={values.sqn} onChange={(event) => onChange('sqn', event.target.value)} /></label>
      {errors.sqn ? <p className="field-error">{errors.sqn}</p> : null}
    </fieldset>
  );
}
