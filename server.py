from flask import Flask, request, render_template, redirect
import os
from flask.ext.pymongo import PyMongo, ASCENDING 
from datetime import datetime

DATE_FORMAT = "%d/%m/%Y"

def db_name_from_uri(full_uri):
	ind = full_uri[::-1].find('/')
	return full_uri[-ind:]


def datetime_from_string(string):
	return datetime.strptime(string, DATE_FORMAT)


def string_from_datetime(datetime_obj):
	return datetime_obj.strftime(DATE_FORMAT)


def process_form(form):
	form['leaving'] = datetime_from_string(form['leaving'])
	form['arriving'] = datetime_from_string(form['arriving'])
	return form


# add environment variables using 'heroku config:add VARIABLE_NAME=variable_name'
DEBUG = os.environ.get('DEBUG', 'True') == 'True'
#GOOGLE_ANALYTICS = os.environ.get('GOOGLE_ANALYTICS', '')
MONGO_URI = os.environ.get('MONGOLAB_URI')

# configure app
app = Flask(__name__)
app.config.from_object(__name__)  
app.config.from_pyfile('config.py', True)
if app.debug:
	print " * Running in debug mode"

app.config['MONGO_DBNAME'] = db_name_from_uri(app.config['MONGO_URI'])
mongo = PyMongo(app)
if mongo:
	print " * Connection to database established"

app.jinja_env.filters['format_date'] = string_from_datetime

@app.route("/",  methods=['GET', 'POST'])
def index():
	if request.method == 'GET':
		posts = mongo.db.tlv_hai.find(sort=[('leaving', ASCENDING)])
		print "# Posts:", posts.count()
		return render_template("index.html", posts=posts)
	else:
		oid = mongo.db.tlv_hai.insert(process_form(request.form.to_dict()))
		print "Added object to database:", oid
		return redirect('/')
	

if __name__ == '__main__':
	# Bind to PORT if defined, otherwise default to 5000.
	port = int(os.environ.get('PORT', 5001))
	app.run(host='0.0.0.0', port=port, debug=app.debug)
