import requests
import json
from django.conf import settings
from accounts.models import Employees


def login() -> dict:
    """
    Zoho people Login API
    """
    login_url = f"{settings.ZOHO.get('login_host')}?refresh_token={settings.ZOHO.get('refresh_token')}&client_id={settings.ZOHO.get('client_id')}&client_secret={settings.ZOHO.get('client_secret')}&grant_type={settings.ZOHO.get('grant_type')}"
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", login_url, headers=headers, verify=False)
    login_response = response.json()
    if login_response.get('access_token'):
        return {'token': login_response.get('access_token')}
    else:
        return {'error': login_response.get('error')}


def get_employees(login: dict, index: int, limit: int) -> dict:
    """
    Zoho people Get employees API
    """
    get_employees_url = f"{settings.ZOHO.get('get_employees_url')}?sIndex={index}&limit={limit}"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f"Zoho-oauthtoken {login.get('token')}"
    }
    response = requests.request("GET", get_employees_url, headers=headers)
    login_response = response.json()

    if login_response.get('response').get('result'):
        return {'result': login_response.get('response').get('result')}
    else:
        return {'error': login_response.get('response').get('errors').get('message')}


def list_employees() -> list:
    """
    Get list of employees from Zoho people
    """
    finished: bool = False
    index: int = 1
    limit: int = 200
    result: list = []
    while not finished:
        response = get_employees(login(), index, limit)
        if response.get('error'):
            finished = True
            print(f'ZOHO Error: {response.get("error")}')
        else:
            index += 200
            result.extend(response.get('result'))
    return result


def save_employees_data_admin() -> dict:
    """
    Save the list of employees that come from Zoho people to local database
    """
    print('Getting Employees data from Zoho...')
    employees_list = list_employees()
    total = len(employees_list)
    updated: int = 0
    created: int = 0
    for employee in employees_list:
        employee_data = list(employee.values())[0][0]
        full_name = f"{employee_data.get('First_Name_Arabic', None)} {employee_data.get('Second_Arabic_Name', None)}"
        email = employee_data.get('EmailID', None)
        if Employees.objects.filter(email=email).exists():
            emp = Employees.objects.get(email=email)
            if emp.full_name != full_name:
                emp.full_name = full_name
                emp.full_info = employee_data
                emp.save()
                updated += 1
            elif emp.full_info is None:
                emp.full_info = employee_data
                emp.save()
                updated += 1
        else:

            Employees.objects.create(full_name=full_name, email=email, full_info=employee_data)
            created += 1
    return {'created': created, 'updated': updated, 'total': total}


def save_employees_data():
    """
    Save the list of employees that come from Zoho people to local database
    """
    employees_list = list_employees()
    updated: int = 0
    created: int = 0
    for employee in employees_list:
        employee_data = list(employee.values())[0][0]
        full_name = f"{employee_data.get('First_Name_Arabic', None)} {employee_data.get('Second_Arabic_Name', None)}"
        email = employee_data.get('EmailID', None)
        if Employees.objects.filter(email=email).exists():
            emp = Employees.objects.get(email=email)
            emp.full_name = full_name
            emp.full_info = employee_data
            emp.save()
            updated += 1
        else:
            Employees.objects.create(full_name=full_name, email=email, full_info=employee_data)
            created += 1
    return {'created': created, 'updated': updated}

def save_employees_data_new():
    """
    Save or update the list of employees from Zoho People in the local database.
    """
    employees_list = list_employees()
    created_count = 0
    updated_count = 0
    employees_to_create = []
    employees_to_update = []

    # Prepare a set of emails for fast lookup in the database
    emails = [f"{emp.get('EmailID', None)}" for emp in employees_list]
    existing_employees = Employees.objects.filter(email__in=emails)
    existing_employees_dict = {emp.email: emp for emp in existing_employees}
    print(f'{existing_employees_dict=}')
    for employee_data in employees_list:
        employee_details = list(employee_data.values())[0][0]
        full_name = f"{employee_details.get('First_Name_Arabic', '')} {employee_details.get('Second_Arabic_Name', '')}"
        email = employee_details.get('EmailID', None)

        # Check if the employee already exists
        if email in existing_employees_dict:
            # Update existing employee
            emp = existing_employees_dict[email]
            emp.full_name = full_name
            emp.full_info = employee_details
            employees_to_update.append(emp)
            print(f'exist email {email=}')
            updated_count += 1
        else:
            # Prepare a new employee record for creation
            print(f'exist email {email=}')
            new_employee = Employees(
                full_name=full_name,
                email=email,
                full_info=employee_details
            )
            employees_to_create.append(new_employee)
            created_count += 1

    # Bulk create new employees
    if employees_to_create:
        Employees.objects.bulk_create(employees_to_create)

    # Bulk update existing employees
    if employees_to_update:
        Employees.objects.bulk_update(employees_to_update, ['full_name', 'full_info'])

    return {'created': created_count, 'updated': updated_count}

from django.core.mail import EmailMessage
from queue import Queue
import threading

class EmployeesDataThread(threading.Thread):
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue

    def run(self):
        data = save_employees_data()
        self.queue.put(data)


def sync_employees_data():
    q = Queue()
    EmployeesDataThread(q).start()
    result = q.get()
    EmailMessage(subject='import result', body=f'result: {result}', to=['saif.ibrahim@qi.iq'])