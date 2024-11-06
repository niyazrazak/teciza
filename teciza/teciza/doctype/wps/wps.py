# Copyright (c) 2024, Niyaz and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.desk.query_report import build_xlsx_data
from frappe.utils.csvutils import to_csv
from frappe import _
from datetime import datetime


class WPS(Document):
	def validate(self):
		self.get_data_from_slip()

	def on_submit(self):
		if not self.employees:
			frappe.throw(_("No employees remaining for WPS"))

	def get_data_from_slip(self):

		filters = self.get_filters()
		employees = self.get_employees()

		if employees:
			filters['employee'] = ["not in", employees]

		data = frappe.db.get_all("Salary Slip", filters=filters, fields=[
			"name as salary_slip", "employee", "net_pay as amount"
		])

		self.set("employees", [])
		for row in data:
			self.append("employees", row)

	def get_filters(self):
		filters = {
			"docstatus": 1
		}

		if self.from_date:
			filters['start_date'] = [">=", self.from_date]

		if self.to_date:
			filters['end_date'] = ["<=", self.to_date]

		if self.department:
			filters['department'] = self.department

		if self.from_range:
			filters['net_pay'] = [">=", self.from_range]

		if self.to_range:
			filters['net_pay'] = ["<=", self.to_range]

		return filters
	
	def get_employees(self):
		wps = frappe.qb.DocType("WPS")
		wps_emp = frappe.qb.DocType("WPS Employee")

		query = (
			frappe.qb.from_(wps)
			.inner_join(wps_emp)
			.on(wps_emp.parent == wps.name)
			.select(
				wps_emp.employee.as_('employee'),
			)
			.where(wps.docstatus == 1)
			.where(wps.name != self.name)
		)

		return query.run(pluck=True)


	def get_report_content(self):
		filters = self.get_report_filters()
		employees = [d.employee for d in self.employees]
		filters['employees'] = employees
		report = frappe.get_doc("Report", "WPS")
		filters = frappe.parse_json(filters) if filters else {}

		columns, data = report.get_data(
			user=frappe.session.user,
			filters=filters,
			as_dict=True,
			ignore_prepared_report=True,
		)
		employer_id = frappe.db.get_single_value('WPS Settings', 'employer_eid')
		bank = frappe.db.get_single_value('WPS Settings', 'payer_bank_short_name')
		today = datetime.today()
		now = datetime.now()
		creation_date = today.strftime("%Y%m%d")
		creation_time = now.strftime("%H%M")
		filename = f"SIF_{employer_id}_{bank}_{creation_date}_{creation_time}"
		report_data = frappe._dict()
		report_data["columns"] = columns
		report_data["result"] = data

		xlsx_data, column_widths = build_xlsx_data(report_data, [], 1, ignore_visible_idx=True)
		return to_csv(xlsx_data), filename
	
	def get_report_filters(self):
		filters = {
			"docstatus": 1
		}

		if self.from_date:
			filters['from_date'] = self.from_date

		if self.to_date:
			filters['to_date'] = self.to_date

		if self.department:
			filters['department'] = self.department

		if self.from_range:
			filters['from_range'] = self.from_range

		if self.to_range:
			filters['to_range'] = self.to_range

		return filters

@frappe.whitelist()
def get_wps_csv(docname):
	doc = frappe.get_doc("WPS", docname)
	data, filename = doc.get_report_content()
	if not data:
		frappe.msgprint(_("No Data"))
		return

	frappe.response["filecontent"] = data
	frappe.response["type"] = "download" 
	frappe.response["doctype"] = "WPS"
	frappe.response["filename"] = f"{filename}.csv"