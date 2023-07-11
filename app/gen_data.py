from faker import Faker
import psycopg2
import random
from uuid import uuid4
from datetime import datetime, timedelta
import os
# Connect to the database
db = psycopg2.connect(
    user=os.environ['POSTGRES_USER'],
    password=os.environ['POSTGRES_PASSWORD'],
    host=os.environ['POSTGRES_HOST'],
    database=os.environ['POSTGRES_DB']
    )
cursor = db.cursor()

# Create Faker instance
fake = Faker()


# Generate and insert fake data into Client table
def gen_clients():
    clients_data = []
    for _ in range(200):
        client_name = fake.company()
        client_contact = fake.name()
        client_address = fake.address().replace("\n", ", ")

        # Insert data into Client table
        sql = "INSERT INTO Client (client_name, client_contact, client_address) VALUES (%s, %s, %s) RETURNING client_id;"
        values = (client_name, client_contact, client_address)
        cursor.execute(sql, values)
        client_id = cursor.fetchone()[0]
        clients_data.append((client_name, client_contact, client_address, client_id))

    # Commit the changes and close the database connection
    db.commit()
    return clients_data


def gen_projects(clients_data):
    # Generate and insert fake data into Project table
    for _ in range(300):
        _, _, _, client_id = random.choice(clients_data)
        project_name = str(uuid4())
        start_date = fake.date_between(start_date="-1y", end_date="+1y")
        end_date = fake.date_between(start_date=start_date, end_date="+1y")

        # Insert data into Project table
        sql = "INSERT INTO Project (project_name, start_date, end_date, client_id) VALUES (%s, %s, %s, %s)"
        values = (
            project_name,
            start_date,
            end_date,
            client_id
        )
        cursor.execute(sql, values)
    db.commit()

def gen_employee():
    for _ in range(100):
        employee_name = fake.name()
        employee_contact = fake.phone_number()
        employee_address = fake.address().replace("\n", ", ")
        sql = "INSERT INTO Employee (employee_name, employee_contact, employee_address) VALUES (%s, %s, %s)"
        values = (
            employee_name,
            employee_contact,
            employee_address,
        )
        cursor.execute(sql, values)
    db.commit()

def gen_timesheet():
    now = datetime.now()
    for _ in range(1000):
        employee_id = random.randint(1, 100)
        project_id = random.randint(1, 300)
        date = now + timedelta(days = random.randint(-100,100))
        hours_worked = round(random.uniform(1, 8), 2)
        description = fake.text()
        sql = "INSERT INTO Timesheet (employee_id, project_id, date, hours_worked, description) VALUES (%s, %s, %s, %s, %s)"
        values = (
            employee_id,
            project_id,
            date,
            hours_worked,
            description
        )
        cursor.execute(sql, values)
    db.commit()

if __name__ == "__main__":
    client_data = gen_clients()
    gen_projects(client_data)
    gen_employee()
    gen_timesheet()

    cursor.close()
    db.close()
