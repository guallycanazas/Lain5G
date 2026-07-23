ALTER TABLE subscribers ADD COLUMN IF NOT EXISTS auth_ha1 VARCHAR(32);
INSERT INTO subscribers (imsi, msisdn, impi, impu, domain_name, auth_ha1)
VALUES (
  '__SUBSCRIBER_IMSI__',
  '__SUBSCRIBER_MSISDN__',
  '__SUBSCRIBER_IMSI__@__IMS_DOMAIN__',
  'sip:__SUBSCRIBER_MSISDN__@__IMS_DOMAIN__',
  '__IMS_DOMAIN__',
  MD5(CONCAT('__SUBSCRIBER_IMSI__', '@', '__IMS_DOMAIN__', ':', '__IMS_DOMAIN__', ':', '__IMS_AUTH_PASSWORD__'))
)
ON DUPLICATE KEY UPDATE
  msisdn = VALUES(msisdn),
  impi = VALUES(impi),
  impu = VALUES(impu),
  domain_name = VALUES(domain_name),
  auth_ha1 = VALUES(auth_ha1);
