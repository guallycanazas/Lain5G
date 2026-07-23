const env = process.env;

function required(name) {
  const value = env[name];
  if (!value || value.trim() === '') throw new Error(`${name} is required`);
  return value.trim();
}

function hex(name, length) {
  const value = required(name);
  if (!new RegExp(`^[0-9a-fA-F]{${length}}$`).test(value)) throw new Error(`${name} must be ${length} hexadecimal characters`);
  return value.toUpperCase();
}

const imsi = required('SUBSCRIBER_IMSI');
if (!/^\d{5,15}$/.test(imsi)) throw new Error('SUBSCRIBER_IMSI must contain 5 to 15 digits');
const internet = env.APN_INTERNET || 'internet';

db.subscribers.updateOne(
  { imsi },
  {
    $set: {
      imsi,
      msisdn: env.SUBSCRIBER_MSISDN ? [env.SUBSCRIBER_MSISDN] : [],
      schema_version: 1,
      subscribed_rau_tau_timer: 12,
      network_access_mode: 0,
      subscriber_status: 0,
      access_restriction_data: 32,
      security: {
        k: hex('SUBSCRIBER_KEY', 32),
        amf: hex('SUBSCRIBER_AMF', 4),
        op: null,
        opc: hex('SUBSCRIBER_OPC', 32),
        sqn: hex('SUBSCRIBER_SQN', 12),
      },
      ambr: { uplink: { value: 1, unit: 3 }, downlink: { value: 1, unit: 3 } },
      slice: [{
        sst: 1,
        default_indicator: true,
        session: [{ name: internet, type: 3, qos: { index: 9, arp: { priority_level: 8, pre_emption_capability: 1, pre_emption_vulnerability: 1 } }, ambr: { uplink: { value: 1, unit: 3 }, downlink: { value: 1, unit: 3 } }, pcc_rule: [] }],
      }],
    },
    $setOnInsert: { createdAt: new Date() },
    $currentDate: { updatedAt: true },
  },
  { upsert: true },
);

printjson({ status: 'ok', imsi, apn: [internet], secrets: 'hidden' });
