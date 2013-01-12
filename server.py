# -*- coding: utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

from flask import Flask, request, render_template, redirect, Response, url_for
import os
from flask.ext.pymongo import PyMongo, ObjectId, ASCENDING
from flaskext.markdown import Markdown
from flask.ext.assets import Environment, Bundle
from datetime import datetime
import simplejson
from atlas import atlas
from apscheduler.scheduler import Scheduler
import uuid
from sendgrid import Sendgrid, Message

DATE_FORMAT = "%d/%m/%Y"
SHORT_DATE_FORMAT = "%d/%m/%y"
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


def short_string_from_datetime(datetime_obj):
	return datetime_obj.strftime(SHORT_DATE_FORMAT)

def sort_atlas_by_field(atlas, field='lat', reverse=False):
	return sorted(atlas.items(), key=lambda x: x[1][field], reverse=reverse)


def process_form(form):
	form['leaving'] = datetime_from_string(form['leaving'])
	form['arriving'] = datetime_from_string(form['arriving'])
	if form['source'].endswith('...'):
		form['source'] = form['custom_source']
	if form['destination'].endswith('...'):
		form['destination'] = form['custom_destination']
	form['secret'] = str(uuid.uuid1())
	return form


# add environment variables using 'heroku config:add VARIABLE_NAME=variable_name'
DEBUG = os.environ.get('DEBUG', 'True') == 'True'
EMAIL = 'volver.info.il@gmail.com'
WEBSITE_URL = 'http://www.volver.co.il/'
WEBSITE_NAME = u'לחזור - Volver'

# Services
MONGO_URI = os.environ.get('MONGOLAB_URI')
GOOGLE_ANALYTICS = os.environ.get('GOOGLE_ANALYTICS', '')

# SendGrid
MAIL_USERNAME = os.environ.get("SENDGRID_USERNAME")
MAIL_PASSWORD = os.environ.get("SENDGRID_PASSWORD")

# init & configure app
app = Flask(__name__)
app.config.from_object(__name__)  
app.config.from_pyfile('config.py', True)
Markdown(app)

# init Assets
assets = Environment(app)
js_base = Bundle('jquery-1.8.3.js', 'bootstrap.rtl.js',
            filters=('yui_js'), output='base.js')
assets.register('js_base', js_base)

css_base = Bundle('style.css', 'bootstrap.rtl.css', 'bootstrap-responsive.rtl.css', 'bootstrap-override.css', 'font-awesome.css',
	filters="yui_css", output='base.css')
assets.register('css_base', css_base)

js_index = Bundle("jquery-ui.custom.min.js", "jquery.validate.js", "jquery.validate.messages_he.js", "mailcheck.js",
	filters='yui_js', output='index.js')
assets.register('js_index', js_index)

css_index = Bundle('jquery-ui.custom.css',
	filters="yui_css", output='index.css')
assets.register('css_index', css_index)

# init mail http://sendgrid.com/docs/Code_Examples/python.html
mail = Sendgrid(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'], secure=True)


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
			return mongo.db.CarreteraAustral

app.jinja_env.filters['format_date'] = string_from_datetime
app.jinja_env.filters['format_date_short'] = short_string_from_datetime
app.jinja_env.globals['atlas'] = atlas
app.jinja_env.globals['sort_atlas_by_field'] = sort_atlas_by_field
app.jinja_env.globals['howto'] = open("templates/howto.md").read()  

def send_welcome_mail(post):
	delete_link = request.url_root[:-1] + url_for('delete', secret=post['secret'])
	html = render_template("welcome_mail.html", post=post, delete_link=delete_link)
	msg = Message((app.config['EMAIL'], app.config['WEBSITE_NAME']), u"ברוך הבא ללחזור!", html=html)
	msg.add_to(post['email'], post['name'])	
	if not app.debug:
		print "Sent mail to", post['email'], mail.smtp.send(msg)


def send_contact_mail(subject, text, name, email):
	msg = Message((email, name), subject, html="<div dir='rtl'>" + text + "</div>")
	msg.add_to((app.config['EMAIL'], app.config['WEBSITE_NAME']))
	if app.debug:
		success = True
	else: 
		success = mail.smtp.send(msg)
		print "Sent contact mail", success
	html = render_template("contact_confirmation.html", success=success, name=name, subject=subject, to=app.config['WEBSITE_NAME'])
	msg = Message((app.config['EMAIL'], app.config['WEBSITE_NAME']), u'הודעתך נשלחה', html=html)
	msg.add_to((email, name))
	if app.debug:
		return True
	else:
		print "Sent confirmation mail", mail.smtp.send(msg)
		return success
		

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
		post = process_form(request.form.to_dict())
		oid = add_post(post)
		print "Added post to database:", oid
		send_welcome_mail(post)
		return redirect('/')


@app.route('/matches')
def make_matches():
	arriving = datetime_from_string(request.args.get('arriving', type=str))
	destination = request.args.get('destination', type=unicode)
	matches = get_collection().find({'leaving':arriving, 'source':destination})
	oid = [str(p['_id']) for p in matches]
	return jsonify(result=oid)


@app.route('/spaghetti')
def spaghetti():
	_id = request.args.get('id', type=unicode)
	oid = ObjectId(_id)
	item = get_collection().find_one({'_id':oid})
	if item:
		return jsonify(result=item['email'])
	else:
		return jsonify(result=None)


@app.route('/delete/<string:secret>')
def delete(secret):
	post = get_collection().find_one({'secret':secret})
	if post:
		get_collection().remove(post['_id'])
	return render_template("delete.html", post=post)


@app.route('/contact', methods=['POST'])
def contact():
	name = request.form.get('name', type=unicode)
	email = request.form.get('email', type=unicode)
	subject = request.form.get('subject', type=unicode)
	message = request.form.get('message', type=unicode)
	success = send_contact_mail(subject, message, name, email)
	return jsonify(result=success)


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
