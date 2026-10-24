-- Schema required by Kamailio's ims_icscf module.
-- Adapted from the Kamailio 6.0 IMS example schema (BSD-2-Clause).
CREATE TABLE IF NOT EXISTS nds_trusted_domains (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  trusted_domain VARCHAR(83) NOT NULL DEFAULT ''
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS s_cscf (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(83) NOT NULL DEFAULT '',
  s_cscf_uri VARCHAR(83) NOT NULL DEFAULT ''
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS s_cscf_capabilities (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  id_s_cscf INT NOT NULL DEFAULT 0,
  capability INT NOT NULL DEFAULT 0,
  KEY idx_capability (capability),
  KEY idx_id_s_cscf (id_s_cscf)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
