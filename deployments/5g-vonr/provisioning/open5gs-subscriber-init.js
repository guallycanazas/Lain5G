const env = process.env;

function required(name) {
  const value = env[name];
  if (!value || value.trim() === '') {
    throw new Error(`${name} is required`);
  }
  return value.trim();
}

function requireHex(name, length) {
  const value = required(name);
  const re = new RegExp(`^[0-9a-fA-F]{${length}}$`);
  if (!re.test(value)) {
    throw new Error(`${name} must be ${length} hexadecimal characters`);
  }
  return value.toUpperCase();
}

function session(name, qci) {
  return {
    name,
    type: 3,
    ambr: {
      uplink: { value: 1, unit: 3 },
      downlink: { value: 1, unit: 3 },
    },
    qos: {
      index: qci,
      arp: {
        priority_level: 8,
        pre_emption_capability: 1,
        pre_emption_vulnerability: 1,
      },
    },
    pcc_rule: [],
  };
}

const imsi = required('SUBSCRIBER_IMSI');
const key = requireHex('SUBSCRIBER_KEY', 32);
const opc = requireHex('SUBSCRIBER_OPC', 32);
const amf = requireHex('SUBSCRIBER_AMF', 4);
const sqn = requireHex('SUBSCRIBER_SQN', 12);
const sst = Number(env.SST || '1');
const sd = env.SD || '000001';
const dnnInternet = env.DNN_INTERNET || 'internet';
const dnnIms = env.DNN_IMS || 'ims';

if (!/^\d{5,15}$/.test(imsi)) {
  throw new Error('SUBSCRIBER_IMSI must contain 5 to 15 digits');
}

const subscriber = {
  imsi,
  schema_version: 1,
  subscribed_rau_tau_timer: 12,
  network_access_mode: 0,
  subscriber_status: 0,
  access_restriction_data: 32,
  security: {
    k: key,
    amf,
    op: null,
    opc,
    sqn,
  },
  ambr: {
    uplink: { value: 1, unit: 3 },
    downlink: { value: 1, unit: 3 },
  },
  slice: [
    {
      sst,
      sd,
      default_indicator: true,
      session: [session(dnnInternet, 9), session(dnnIms, 5)],
    },
  ],
};

const result = db.subscribers.updateOne(
  { imsi },
  { $set: subscriber, $setOnInsert: { createdAt: new Date() }, $currentDate: { updatedAt: true } },
  { upsert: true },
);

const action = result.upsertedCount === 1 ? 'inserted' : 'updated';
printjson({
  status: 'ok',
  action,
  imsi,
  dnn: [dnnInternet, dnnIms],
  sst,
  sd,
  secrets: 'hidden',
});
