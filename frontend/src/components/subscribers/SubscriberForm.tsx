import { FormEvent, useState } from 'react';
import type { SubscriberDetail, SubscriberFormPayload } from '../../types/subscriber';
import { ActionButton } from '../ActionButton';
import { SubscriberSecurityFields } from './SubscriberSecurityFields';

const hex32 = /^[0-9a-fA-F]{32}$/;
const imsiRe = /^\d{5,15}$/;
const msisdnRe = /^\d{5,20}$/;
const amfRe = /^[0-9a-fA-F]{4}$/;
const sqnRe = /^[0-9a-fA-F]{12}$/;
const sdRe = /^[0-9a-fA-F]{6}$/;
const dnnRe = /^[A-Za-z0-9][A-Za-z0-9.-]{0,62}$/;

interface SubscriberFormProps {
  mode: 'create' | 'edit';
  initial?: SubscriberDetail;
  loading?: boolean;
  onSubmit: (payload: SubscriberFormPayload) => void;
}

export function SubscriberForm({ mode, initial, loading, onSubmit }: SubscriberFormProps) {
  const editing = mode === 'edit';
  const [showSecrets, setShowSecrets] = useState(false);
  const [values, setValues] = useState({
    imsi: initial?.imsi || '',
    msisdn: initial?.msisdn || '',
    k: '',
    op: '',
    opc: '',
    amf: initial?.security.amf || '8000',
    sqn: editing ? '' : '000000000001',
    sst: String(initial?.sst ?? 1),
    sd: initial?.sd || '000001',
    dnn: initial?.dnn || 'internet',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  const setField = (name: string, value: string) => setValues((current) => ({ ...current, [name]: value }));

  const submit = (event: FormEvent) => {
    event.preventDefault();
    const nextErrors = validate(values, editing);
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) return;
    onSubmit(toPayload(values, editing));
  };

  return (
    <form className="subscriber-form" onSubmit={submit}>
      <fieldset className="form-section">
        <legend>Identity</legend>
        <label>IMSI *<input value={values.imsi} disabled={editing} onChange={(event) => setField('imsi', event.target.value)} /></label>
        {errors.imsi ? <p className="field-error">{errors.imsi}</p> : null}
        <label>MSISDN<input value={values.msisdn} onChange={(event) => setField('msisdn', event.target.value)} /></label>
        {errors.msisdn ? <p className="field-error">{errors.msisdn}</p> : null}
      </fieldset>
      <SubscriberSecurityFields showSecrets={showSecrets} editing={editing} values={values} errors={errors} onChange={setField} onToggle={() => setShowSecrets((value) => !value)} />
      <fieldset className="form-section">
        <legend>Slice and DNN</legend>
        <label>SST *<input type="number" value={values.sst} onChange={(event) => setField('sst', event.target.value)} /></label>
        {errors.sst ? <p className="field-error">{errors.sst}</p> : null}
        <label>SD<input value={values.sd} onChange={(event) => setField('sd', event.target.value)} /></label>
        {errors.sd ? <p className="field-error">{errors.sd}</p> : null}
        <label>DNN *<input value={values.dnn} onChange={(event) => setField('dnn', event.target.value)} /></label>
        {errors.dnn ? <p className="field-error">{errors.dnn}</p> : null}
      </fieldset>
      <p className="muted-text">Changing authentication may require restarting the UE or forcing a new registration.</p>
      <ActionButton loading={loading}>{editing ? 'Save changes' : 'Create subscriber'}</ActionButton>
    </form>
  );
}

function validate(values: Record<string, string>, editing: boolean) {
  const errors: Record<string, string> = {};
  if (!editing && !imsiRe.test(values.imsi)) errors.imsi = 'IMSI must contain 5 to 15 digits.';
  if (values.msisdn && !msisdnRe.test(values.msisdn)) errors.msisdn = 'MSISDN must contain 5 to 20 digits.';
  if (!editing && !hex32.test(values.k)) errors.k = 'K must contain 32 hexadecimal characters.';
  if (values.k && !hex32.test(values.k)) errors.k = 'K must contain 32 hexadecimal characters.';
  if (values.op && !hex32.test(values.op)) errors.op = 'OP must contain 32 hexadecimal characters.';
  if (values.opc && !hex32.test(values.opc)) errors.opc = 'OPc must contain 32 hexadecimal characters.';
  if (values.op && values.opc) errors.opc = 'Use either OP or OPc, not both.';
  if (!editing && !values.op && !values.opc) errors.opc = 'OP or OPc is required.';
  if (values.amf && !amfRe.test(values.amf)) errors.amf = 'AMF must contain 4 hexadecimal characters.';
  if (values.sqn && !sqnRe.test(values.sqn)) errors.sqn = 'SQN must contain 12 hexadecimal characters.';
  const sst = Number(values.sst);
  if (!Number.isInteger(sst) || sst < 1 || sst > 255) errors.sst = 'SST must be between 1 and 255.';
  if (values.sd && !sdRe.test(values.sd)) errors.sd = 'SD must contain 6 hexadecimal characters.';
  if (!values.dnn || values.dnn.includes(' ') || !dnnRe.test(values.dnn)) errors.dnn = 'DNN must be a safe name without spaces.';
  return errors;
}

function toPayload(values: Record<string, string>, editing: boolean): SubscriberFormPayload {
  const security: NonNullable<SubscriberFormPayload['security']> = {};
  for (const key of ['k', 'op', 'opc', 'amf', 'sqn'] as const) {
    const value = values[key].trim();
    if (value || !editing && ['amf', 'sqn'].includes(key)) security[key] = value || null;
  }
  return {
    ...(!editing ? { imsi: values.imsi.trim() } : {}),
    msisdn: values.msisdn.trim() || null,
    security,
    slice: { sst: Number(values.sst), sd: values.sd.trim() || null },
    dnn: values.dnn.trim(),
  };
}
