-- Create Client table
CREATE TABLE Client (
  client_id SERIAL PRIMARY KEY,
  client_name VARCHAR(255),
  client_contact VARCHAR(255),
  client_address VARCHAR(255)
);

-- Create Project table
CREATE TABLE Project (
  project_id SERIAL PRIMARY KEY,
  project_name VARCHAR(255),
  client_id INT,
  start_date DATE,
  end_date DATE,
  FOREIGN KEY (client_id) REFERENCES Client(client_id)
);

-- Create Employee table
CREATE TABLE Employee (
  employee_id SERIAL PRIMARY KEY,
  employee_name VARCHAR(255),
  employee_contact VARCHAR(255),
  employee_address VARCHAR(255)
);

-- Create Timesheet table
CREATE TABLE Timesheet (
  timesheet_id SERIAL PRIMARY KEY,
  employee_id INT,
  project_id INT,
  date DATE,
  hours_worked DECIMAL(5,2),
  description TEXT,
  FOREIGN KEY (employee_id) REFERENCES Employee(employee_id),
  FOREIGN KEY (project_id) REFERENCES Project(project_id)
);