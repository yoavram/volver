from flask import Flask, request, render_template
import os
from flask.ext.pymongo import PyMongo


def db_name_from_uri(full_uri):
	ind = full_uri[::-1].find('/')
	return full_uri[-ind:]


# add environment variables using 'heroku config:add VARIABLE_NAME=variable_name'
DEBUG = os.environ.get('DEBUG', 'True') == 'True'
GOOGLE_ANALYTICS = os.environ.get('GOOGLE_ANALYTICS', '')
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


@app.route("/",  methods=['GET', 'POST'])
def index():
	if request.method == 'GET':
		return render_template("index.html")
	else:
		oid = mongo.insert(request.form.to_dict())
		print "Added object to database:", oid
		return render_template("index.html")
	

if __name__ == '__main__':
	# Bind to PORT if defined, otherwise default to 5000.
	port = int(os.environ.get('PORT', 5000))
	app.run(host='0.0.0.0', port=port, debug=app.debug)
