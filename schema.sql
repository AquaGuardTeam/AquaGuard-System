CREATE DATABASE IF NOT EXISTS aquaguard CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE aquaguard;

CREATE TABLE IF NOT EXISTS devices (
  id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(80) NOT NULL, location VARCHAR(120) NOT NULL,
  api_token_hash VARCHAR(255) NOT NULL, status VARCHAR(20) NOT NULL DEFAULT 'online',
  created_at DATETIME NOT NULL
);
CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY, username VARCHAR(80) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL, role VARCHAR(30) NOT NULL DEFAULT 'viewer',
  created_at DATETIME NOT NULL
);
CREATE TABLE IF NOT EXISTS sensor_readings (
  id INT AUTO_INCREMENT PRIMARY KEY, device_id INT NOT NULL, timestamp DATETIME NOT NULL,
  ph FLOAT NULL, tds_ppm FLOAT NULL, turbidity_ntu FLOAT NULL,
  validity_status VARCHAR(20) NOT NULL DEFAULT 'valid',
  FOREIGN KEY (device_id) REFERENCES devices(id)
);
CREATE TABLE IF NOT EXISTS filters (
  id INT AUTO_INCREMENT PRIMARY KEY, device_id INT NOT NULL, filter_type VARCHAR(120) NOT NULL,
  installed_at DATETIME NOT NULL, replaced_at DATETIME NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'active', FOREIGN KEY (device_id) REFERENCES devices(id)
);
CREATE TABLE IF NOT EXISTS maintenance_records (
  id INT AUTO_INCREMENT PRIMARY KEY, filter_id INT NOT NULL, event_date DATETIME NOT NULL,
  action VARCHAR(80) NOT NULL, notes TEXT NULL, recorded_by INT NULL,
  FOREIGN KEY (filter_id) REFERENCES filters(id), FOREIGN KEY (recorded_by) REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS filter_assessments (
  id INT AUTO_INCREMENT PRIMARY KEY, filter_id INT NOT NULL, timestamp DATETIME NOT NULL,
  `condition` VARCHAR(20) NOT NULL, trend_summary VARCHAR(255) NOT NULL, rule_version VARCHAR(30) NOT NULL,
  FOREIGN KEY (filter_id) REFERENCES filters(id)
);
CREATE TABLE IF NOT EXISTS alerts (
  id INT AUTO_INCREMENT PRIMARY KEY, device_id INT NOT NULL, reading_id INT NULL,
  alert_type VARCHAR(60) NOT NULL, severity VARCHAR(20) NOT NULL, message VARCHAR(255) NOT NULL,
  created_at DATETIME NOT NULL, status VARCHAR(20) NOT NULL DEFAULT 'open',
  FOREIGN KEY (device_id) REFERENCES devices(id), FOREIGN KEY (reading_id) REFERENCES sensor_readings(id)
);
CREATE TABLE IF NOT EXISTS dispensing_events (
  id INT AUTO_INCREMENT PRIMARY KEY, device_id INT NOT NULL, mode VARCHAR(20) NOT NULL,
  requested_at DATETIME NOT NULL, reported_state VARCHAR(40) NOT NULL,
  feedback_available BOOLEAN NOT NULL DEFAULT FALSE,
  FOREIGN KEY (device_id) REFERENCES devices(id)
);

CREATE TABLE IF NOT EXISTS valve_events (
  id INT AUTO_INCREMENT PRIMARY KEY, device_id INT NOT NULL, user_id INT NULL,
  command VARCHAR(40) NOT NULL, requested_at DATETIME NOT NULL,
  reported_state VARCHAR(40) NOT NULL, feedback_available BOOLEAN NOT NULL DEFAULT FALSE,
  FOREIGN KEY (device_id) REFERENCES devices(id), FOREIGN KEY (user_id) REFERENCES users(id)
);
