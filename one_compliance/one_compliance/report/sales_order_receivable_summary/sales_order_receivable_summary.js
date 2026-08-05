// Copyright (c) 2026, Zoul Technologies Private Limited and contributors
// For license information, please see license.txt

frappe.query_reports["Sales Order Receivable Summary"] = {
	onload: function (report) {
		if (!report.get_filter_value('report_date')) {
			report.set_filter_value('report_date', frappe.datetime.get_today());
		}
	},

	filters: [
		{
			fieldname: "company",
			label: "Company",
			fieldtype: "Link",
			options: "Company"
		},
		{
			fieldname: "customer",
			label: "Customer",
			fieldtype: "Link",
			options: "Customer"
		},
		{
			fieldname: "report_date",
			label: "Report Date",
			fieldtype: "Date",
			default: frappe.datetime.get_today()
		},
		{
			fieldname: "from_date",
			label: "From Date",
			fieldtype: "Date"
		},
		{
			fieldname: "to_date",
			label: "To Date",
			fieldtype: "Date"
		},
		{
			fieldname: "territory",
			label: "Territory",
			fieldtype: "Link",
			options: "Territory"
		},
		{
			fieldname: "customer_group",
			label: "Customer Group",
			fieldtype: "Link",
			options: "Customer Group"
		},
		{
			fieldname: "include_invoiced",
			label: "Include Invoiced",
			fieldtype: "Check",
			default: 0
		},
		{
			fieldname: "include_paid",
			label: "Include Paid",
			fieldtype: "Check",
			default: 0
		}
	]
};
