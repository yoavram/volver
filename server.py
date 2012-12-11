# -*- coding: utf-8 -*-
from flask import Flask, request, render_template, redirect, Response
import os
from flask.ext.pymongo import PyMongo, ASCENDING 
from flask.ext.mail import Mail, Message
from datetime import datetime
from bson import ObjectId
import simplejson
from atlas import atlas
from apscheduler.scheduler import Scheduler

DATE_FORMAT = "%d/%m/%Y"
DAYS_TO_EXPIRE = 7


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
EMAIL = 'volver.info.il@gmail.com'
WEBSITE_URL = 'http://www.volver.co.il/'
WEBSITE_NAME = u'לחזור - Volver'

# Services
MONGO_URI = os.environ.get('MONGOLAB_URI')
#GOOGLE_ANALYTICS = os.environ.get('GOOGLE_ANALYTICS', '')

# SendGrid
MAIL_SERVER = 'smtp.sendgrid.net'
MAIL_PORT = 587  
MAIL_USE_SSL = False
MAIL_USE_SSL = True
MAIL_USERNAME = os.environ.get("SENDGRID_USERNAME")
MAIL_PASSWORD = os.environ.get("SENDGRID_PASSWORD")


# init & configure app
app = Flask(__name__)
app.config.from_object(__name__)  
app.config.from_pyfile('config.py', True)

# init mail
mail = Mail(app)

# init database
if app.debug:
	print " * Running in debug mode"
	import mockdb
	col = mockdb.MockDb()
	def get_collection():
		return col
else:
	app.config['MONGO_DBNAME'] = db_name_from_uri(app.config['MONGO_URI'])
	mongo = PyMongo(app)
	if mongo:
		print " * Connection to database established"
		def get_collection():
			return mongo.db.CarreteraAustralDev

app.jinja_env.filters['format_date'] = string_from_datetime
app.jinja_env.globals['atlas'] = atlas
app.jinja_env.globals['sort_atlas_by_field'] = sort_atlas_by_field


def send_welcome_mail(recipient_name, recipient_email):
	msg = Message("ברוך הבא ללחזור!", sender=(WEBSITE_NAME, EMAIL))
	msg.add_recipient(recipient_email)
	msg.html = render_template("welcome_mail.html", name=recipient_name, delete_link=WEBSITE_URL)
	print "Sending mail to", recipient_email
	mail.send(msg)
	if app.debug:
		print msg.html

def get_posts():
	cursor = get_collection().find(sort=[('leaving', ASCENDING)])
	return cursor, cursor.count()
	

def add_post(post):
	return get_collection().insert(post)


def remove_old_posts():
	now = datetime.now()
	cursor = get_collection().find()
	for p in cursor:
		delta = now - p['arriving']
		if delta.days > DAYS_TO_EXPIRE:
			print "Removing old post: "
			print p
			get_collection().remove(p['_id'])
	

@app.route("/",  methods=['GET', 'POST'])
def index():
	if request.method == 'GET':
		posts, num = get_posts()
		print "# Posts:", num
		return render_template("index.html", posts=posts)
	else:
		oid = add_post(process_form(request.form.to_dict()))
		print "Added object to database:", oid
		send_welcome_mail(request.form['name'], request.form['email'])
		return redirect('/')


@app.route('/matches')
def make_matches():
	arriving = datetime_from_string(request.args.get('arriving', type=str))
	destination = request.args.get('destination', type=unicode)
	matches = get_collection().find({'leaving':arriving, 'source':destination})
	oid = [str(p['_id']) for p in matches]
	return jsonify(result=oid)


if __name__ == '__main__':
	sched = Scheduler()
	### used to test the scheduler
	#from datetime import timedelta
	#sched.add_date_job(remove_old_posts, datetime.now() + timedelta(0.0001)) 
	sched.add_cron_job(remove_old_posts, day_of_week='*', hour=12)
	sched.start()
	print " * Started scheduler"

	port = int(os.environ.get('PORT', 5001))
	app.run(host='0.0.0.0', port=port, debug=app.debug)
	sched.shutdown()
	print "Finished"