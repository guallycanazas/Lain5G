const serviceLabels: Record<string, string> = {
  'enb-x310': 'LTE eNB',
  'gnb-x310': '5G SA gNB',
  'enb-nsa-x310': '5G NSA eNB',
};

export function serviceLabel(service: string) {
  return serviceLabels[service] || service.replace(/x(?:300|310)/gi, 'usrp');
}

export function runtimeIdentifier(name: string) {
  return name.replace(/x(?:300|310)/gi, 'usrp');
}
