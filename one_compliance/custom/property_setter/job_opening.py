def get_job_opening_property_setters():
	'''
		Get property setters for Job Opening doctype.
	'''
	return [
		{
			"doc_type": "Job Opening",
			"doctype_or_field": "DocType",
			"property": "image_field",
			"property_type": "Data",
			"value": "qr_scan_to_apply",
		},
	]
