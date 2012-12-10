# -*- coding: utf-8 -*-
from datetime import datetime
DATE_FORMAT = "%d/%m/%Y"

def datetime_from_string(string):
	return datetime.strptime(string, DATE_FORMAT)

class MockDb:
	def __init__(self):
		self.data = [
			{'name':u'uri', 'direction':'north', 'leaving':datetime_from_string('22/12/2012'), 'arriving':datetime_from_string('23/12/2012'), 'email':'uri@gmail.com', 'source':'bariloche', 'destination':'al poson'},
			{'name':u'מיכל', 'direction':'south', 'leaving':datetime_from_string('24/12/2012'), 'arriving':datetime_from_string('26/12/2012'), 'email':'uri@gmail.com', 'source':'al poson', 'destination':'bariloche'}
		]


	def insert(self, post):
		self.data.append(post)
		return 1


	def find(self, spec=None, sort=None):
		return self


	def rewind(self):
		return self


	def __iter__(self):
		return self.data.__iter__()

	def count(self):
		return len(self.data)