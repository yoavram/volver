# -*- coding: utf-8 -*-
from flask import Flask, request, render_template, redirect, Response
import os
from flask.ext.pymongo import PyMongo, ASCENDING 
from datetime import datetime
from bson import ObjectId
import simplejson
from atlas import atlas

DATE_FORMAT = "%d/%m/%Y"

class MongoDocumentEncoder(simplejson.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        elif isinstance(o, ObjectId):
            return str(o)
        return simplejson.JSONEncoder(self, o)


def jsonify(*args, **kwargs):
    return Response(simplejson.dumps(dict(*args, **kwargs), cls=MongoDocumentEncoder), mimetype='application/json')


def db_name_from_uri(full_uri):
	ind = full_uri[::-1].find('/')
	return full_uri[-ind:]


def datetime_from_string(string):
	return datetime.strptime(string, DATE_FORMAT)


def string_from_datetime(datetime_obj):
	return datetime_obj.strftime(DATE_FORMAT)


def sort_atlas_by_field(atlas, field='lat', reverse=False):
	return sorted(atlas.items(), key=lambda x: x[1][field], reverse=reverse)

def process_form(form):
	form['leaving'] = datetime_from_string(form['leaving'])
	form['arriving'] = datetime_from_string(form['arriving'])
	if form['source'].endswith('...'):
		form['source'] = form['custom_source']
	if form['destination'].endswith('...'):
		form['destination'] = form['custom_destination']		
	return form


# add environment variables using 'heroku config:add VARIABLE_NAME=variable_name'
DEBUG = os.environ.get('DEBUG', 'True') == 'True'
#GOOGLE_ANALYTICS = os.environ.get('GOOGLE_ANALYTICS', '')
MONGO_URI = os.environ.get('MONGOLAB_URI')
EMAIL = 'volver.info.il@gmail.com'
WEBSITE_URL = 'http://www.volver.com/'

# configure app
app = Flask(__name__)
app.config.from_object(__name__)  
app.config.from_pyfile('config.py', True)

if app.debug:
	print " * Running in debug mode"
	import mockdb
	def get_collection():
		return mockdb.MockDb()
else:
	app.config['MONGO_DBNAME'] = db_name_from_uri(app.config['MONGO_URI'])
	mongo = PyMongo(app)
	if mongo:
		print " * Connection to database established"
		def get_collection():
			return  mongo.db.CarreteraAustralDev

app.jinja_env.filters['format_date'] = string_from_datetime
app.jinja_env.globals['atlas'] = atlas
app.jinja_env.globals['sort_atlas_by_field'] = sort_atlas_by_field


def get_posts():
	cursor = get_collection().find(sort=[('leaving', ASCENDING)])
	return cursor, cursor.count()
	

def add_post(post):
	return get_collection().insert(post)
	

@app.route("/",  methods=['GET', 'POST'])
def index():
	if request.method == 'GET':
		posts, num = get_posts()
		print "# Posts:", num
		return render_template("index.html", posts=posts)
	else:
		oid = add_post(process_form(request.form.to_dict()))
		print "Added object to database:", oid
		return redirect('/')


@app.route('/matches')
def make_matches():
	arriving = datetime_from_string(request.args.get('arriving', type=str))
	destination = request.args.get('destination', type=unicode)
	matches = get_collection().find({'leaving':arriving, 'source':destination})
	oid = [str(p['_id']) for p in matches]
	return jsonify(result=oid)


if __name__ == '__main__':
	# Bind to PORT if defined, otherwise default to 5000.
	port = int(os.environ.get('PORT', 5001))
	app.run(host='0.0.0.0', port=port, debug=app.debug)
	print "Finished"