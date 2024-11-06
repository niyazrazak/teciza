# Copyright (c) 2024, Niyaz and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate
from datetime import datetime


def execute(filters=None):
	columns, data = [], []
	columns = get_columns()
	data = get_record(filters)
	return columns, data

def get_record(filters):
	data = []

	ss = frappe.qb.DocType("Salary Slip")
	emp = frappe.qb.DocType("Employee")

	query = (
		frappe.qb.from_(ss)
		.inner_join(emp)
		.on(emp.name == ss.employee)
		.select(
			emp.custom_qid.as_('qid_no'),
			emp.bank_ac_no.as_('bank_ac_no'),
			emp.iban.as_('iban'),
			emp.custom_employee_bank_short_name.as_('bank_short_name'),
			ss.name.as_('name'),
			ss.employee.as_('employee'),
			ss.employee_name.as_('employee_name'),
			ss.payroll_frequency.as_('payroll_frequency'),
			ss.total_working_days.as_('total_working_days'),
			ss.net_pay.as_('net_salary'),
			ss.total_deduction.as_('total_deduction')
		)
		.where(ss.docstatus == 1)
	)

	if filters.get('from_date'):
		query = query.where(ss.start_date >= filters.get('from_date'))

	if filters.get('to_date'):
		query = query.where(ss.end_date <= filters.get('to_date'))
	
	if filters.get('department'):
		query = query.where(ss.department == filters.get('department'))

	if filters.get('from_range'):
		query = query.where(ss.net_pay >= filters.get('from_range'))

	if filters.get('to_range'):
		query = query.where(ss.net_pay <= filters.get('to_range'))	
	
	if filters.get('employees'):
		query = query.where(ss.employee.isin(filters.get('employees')))

	data = query.run(as_dict=True)

	month_name = getdate(filters.from_date).strftime("%B")
	year = getdate(filters.from_date).strftime("%Y")

	total_records = len(data)
	total_salary = sum((row.get("net_salary", 0)) for row in data)
	idx = 0
	for row in data:
		idx += 1
		if row.get("payroll_frequency") == "Monthly":
			row['salary_frequency'] = "M"

		base = frappe.db.get_value("Salary Detail", {"parent": row.get("name"), "salary_component": ["like", "%Basic%"]}, "Sum(amount)") or 0
		housing_allowance = frappe.db.get_value("Salary Detail", {"parent": row.get("name"), "salary_component": ["like", "%Housing Allowance%"]}, "Sum(amount)") or 0
		food_allowance = frappe.db.get_value("Salary Detail", {"parent": row.get("name"), "salary_component":  ["like", f"%Food Allowance%"] }, "Sum(amount)") or 0
		transportation_allowance = frappe.db.get_value("Salary Detail", {"parent": row.get("name"), "salary_component":  ["like", "%Transportation Allowance%"]}, "Sum(amount)") or 0
		
		remaining_balance = row.net_salary - (base + housing_allowance + food_allowance + transportation_allowance)

		data_to_append = {
			"sno": idx,
			"base_salary": base or 0.0,
			"extra_hours": 0.0,
			"ot_allowance": 0.0,
			"extra_field_1": 0.0,
			"extra_field_2": 0.0,
			"payment_type": "Normal Payment",
			"comments": f"Salary For {month_name} {year}",
			"housing_allowance": housing_allowance or 0.0,
			"food_allowance":  food_allowance or 0.0,
			"transportation_allowance": transportation_allowance or 0.0,
			"extra_income": remaining_balance or 0.0
		}

		row.update(data_to_append)
		if row.get("total_deduction"):
			row["deduction_reason_code"] = 4
		else:
			row["deduction_reason_code"] = 0

	today = datetime.today()
	now = datetime.now()
	salary_month = getdate(filters.from_date).strftime("%Y%m")
	headers = {
		"sno": frappe.db.get_single_value('WPS Settings', 'employer_eid'),
		"qid_no": today.strftime("%Y%m%d"),
		"visa_id": now.strftime("%H%M"),
		"employee_name": frappe.db.get_single_value('WPS Settings', 'payer_eid'),
		"bank_short_name": frappe.db.get_single_value('WPS Settings', 'payer_qid'),
		"iban": frappe.db.get_single_value('WPS Settings', 'payer_bank_short_name'),
		"salary_frequency": frappe.db.get_single_value('WPS Settings', 'payer_iban'),
		"total_working_days": salary_month,
		"net_salary": total_salary,
		"base_salary": total_records,
		"extra_hours": frappe.db.get_single_value('WPS Settings', 'sif_version')
	}
	data.insert(0, headers)
	title_headers = {
		"sno": "Record Sequence",
		"qid_no": "Employee QID",
		"visa_id": "Employee Visa ID",
		"employee_name": "Employee Name",
		"bank_short_name": "Employee Bank Short Name",
		"iban": "Employee Account",
		"salary_frequency": "Salary Frequency",
		"total_working_days": "Number of Working days",
		"net_salary": "Net Salary",
		"base_salary": "Basic Salary",
		"extra_hours": "Extra hours",
		"extra_income": "Extra income",
		"total_deduction": "Deductions",
        "payment_type": "Payment Type",
		"comments": "Notes / Comments",
        "housing_allowance": "Housing Allowance",
        "food_allowance": "Food Allowance",
        "transportation_allowance": "Transportation Allowance",
		"ot_allowance": "Over Time Allowance",
		"deduction_reason_code": "Deduction Reason Code",
		"extra_field_1": "Extra Field 1",
		"extra_field_2": "Extra Field 2",
	}
	data.insert(1, title_headers)
	return data


def get_columns():
	columns = [
		{
			"label": _("Employer EID"),
			"fieldname": "sno",
			"fieldtype": "Data",
			"width": 150
		},
		{
			"label": _("File Creation Date"),
			"fieldname": "qid_no",
			"fieldtype": "Data",
			"width": 150
		},
		{
			"label": _("File Creation Time"),
			"fieldname": "visa_id",
			"fieldtype": "Data",
			"width": 180
		},
		{
			"label": _("Payer EID"),
			"fieldname": "employee_name",
			"fieldtype": "Data",
			"width": 180
		},
		{
			"label": _("Payer QID"),
			"fieldname": "bank_short_name",
			"fieldtype": "Data",
			"width": 150
		},
		{
			"label": _("Payer Bank Short Name"),
			"fieldname": "iban",
			"fieldtype": "Data",
			"width": 150
		},
		{
			"label": _("Payer IBAN"),
			"fieldname": "salary_frequency",
			"fieldtype": "Data",
			"width": 150
		},
		{
			"label": _("Salary Year and Month"),
			"fieldname": "total_working_days",
			"fieldtype": "Data",
			"width": 150
		},
		{
			"label": _("Total Salaries"),
			"fieldname": "net_salary",
			"fieldtype": "Data",
			"width": 150
		},
		{
			"label": _("Total Records"),
			"fieldname": "base_salary",
			"fieldtype": "Data",
			"width": 150
		},
		{
			"label": _("SIF Version"),
			"fieldname": "extra_hours",
			"fieldtype": "Data",
			"width": 150
		},
		{
			"label": _(""),
			"fieldname": "extra_income",
			"fieldtype": "Data",
			"width": 150
		},
		{
			"label": _(""),
			"fieldname": "total_deduction",
			"fieldtype": "Data",
			"width": 150
		},
		{
			"label": _(""),
			"fieldname": "payment_type",
			"fieldtype": "Data",
			"width": 150
		},
		{
			"label": _(""),
			"fieldname": "comments",
			"fieldtype": "Data",
			"width": 150
		},
		{
			"label": _(""),
			"fieldname": "housing_allowance",
			"fieldtype": "Data",
			"width": 150
		},
		{
			"label": _(""),
			"fieldname": "food_allowance",
			"fieldtype": "Data",
			"width": 150
		},
		{
			"label": _(""),
			"fieldname": "transportation_allowance",
			"fieldtype": "Data",
			"width": 150
		},
		{
			"label": _(""),
			"fieldname": "ot_allowance",
			"fieldtype": "Data",
			"width": 150
		},
		{
			"label": _(""),
			"fieldname": "deduction_reason_code",
			"fieldtype": "Data",
			"width": 150
		},
		{
			"label": _(""),
			"fieldname": "extra_field_1",
			"fieldtype": "Data",
			"width": 150
		},
		{
			"label": _(""),
			"fieldname": "extra_field_2",
			"fieldtype": "Data",
			"width": 150
		},
	]
	return columns