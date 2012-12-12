# -*- coding: utf-8 -*-
from datetime import datetime
DATE_FORMAT = "%d/%m/%Y"

def datetime_from_string(string):
	return datetime.strptime(string, DATE_FORMAT)

class MockDb:
	def __init__(self):
		self.data = [
			{'_id':1,'name':u'uri', 'direction':'north', 'leaving':datetime_from_string('2/12/2012'), 'arriving':datetime_from_string('3/12/2012'), 'email':'uri@gmail.com', 'source':'bariloche', 'destination':'al poson', 'secret':'secret1'},
			{'_id':2,'name':u'מיכל', 'direction':'south', 'leaving':datetime_from_string('12/12/2012'), 'arriving':datetime_from_string('17/12/2012'), 'email':'uri@gmail.com', 'source':'al poson', 'destination':'bariloche', 'secret':'secret2'}
		]


	def insert(self, post):
		_id = max([ x['_id'] for x in self.data ]) + 1
		post['_id'] = _id
		self.data.append(post)
		return _id


	def find(self, spec=None, sort=None):
		if spec:
			data = []
			for d in self.data:
				match = True
				for k,v in spec.items():
					if d[k] != v:
						match = False
						break
				if match:
					data.append(d)
			return data
		else:
			return self


	def find_one(self, spec=None, sort=None):
		data = self.find(spec, sort)
		if len(data)>0:
			return data[0]
		else:
			return None


	def rewind(self):
		return self


	def __iter__(self):
		return self.data.__iter__()


	def count(self):
		return len(self.data)


	def remove(self, _id):
		for x in self.data:
			if x['_id'] == _id:
				return self.data.remove(x)
