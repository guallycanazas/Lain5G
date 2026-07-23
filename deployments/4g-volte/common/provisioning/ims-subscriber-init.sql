CREATE DATABASE IF NOT EXISTS ims;
USE ims;

CREATE TABLE IF NOT EXISTS subscribers (
  id INT AUTO_INCREMENT PRIMARY KEY,
  imsi VARCHAR(15) NOT NULL UNIQUE,
  msisdn VARCHAR(32),
  impi VARCHAR(128) NOT NULL,
  impu VARCHAR(128) NOT NULL,
  domain_name VARCHAR(128) NOT NULL,
  auth_ha1 VARCHAR(32),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO subscribers (imsi, msisdn, impi, impu, domain_name, auth_ha1)
VALUES (
  '${SUBSCRIBER_IMSI}',
  '${SUBSCRIBER_MSISDN}',
  '${SUBSCRIBER_IMSI}@${IMS_DOMAIN}',
  'sip:${SUBSCRIBER_MSISDN}@${IMS_DOMAIN}',
  '${IMS_DOMAIN}',
  MD5('${SUBSCRIBER_IMSI}@${IMS_DOMAIN}:${IMS_DOMAIN}:${IMS_AUTH_PASSWORD}')
)
ON DUPLICATE KEY UPDATE msisdn = VALUES(msisdn), impi = VALUES(impi), impu = VALUES(impu), domain_name = VALUES(domain_name), auth_ha1 = VALUES(auth_ha1);
