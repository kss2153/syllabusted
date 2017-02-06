from flask import Flask, jsonify, render_template, request, redirect, url_for
import requests
from flask.ext.mongoengine import MongoEngine
from flask.ext.login import LoginManager, login_required, login_user, logout_user, current_user
from flask.ext.mongoengine.wtf import model_form
from wtforms import PasswordField
from werkzeug import secure_filename
from flask_restful import Resource, Api

from cStringIO import StringIO
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage

import json
import date_parser
import os
from urlparse import urlsplit
from pymongo import Connection



app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'this_should_be_configured')
api = Api(app)
app.config['MONGODB_SETTINGS'] = { 'db': 'calendarevents' }
app.config['SECRET_KEY'] = 'aal193192112lfqams'
app.config['WTF_CSRF_ENABLED'] = True

url = os.getenv('MONGOLAB_URI', 'mongodb://localhost:27017')
parsed = urlsplit(url)
db_name = parsed.path[1:]

# Get your DB
db = Connection(url)[db_name]

# Authenticate
if '@' in url:
    user, password = parsed.netloc.split('@')[0].split(':')
    db.authenticate(user, password)

login_manager = LoginManager()
login_manager.init_app(app)

###
# Routing for your application.
###

class User(db.Document):
  name = db.StringField(required=True,unique=True)
  password = db.StringField(required=True)
  def is_authenticated(self):
    users = User.objects(name=self.name, password=self.password)
    return len(users) != 0
  def is_active(self):
    return True
  def is_anonymous(self):
    return False
  def get_id(self):
    return self.name
UserForm = model_form(User)
UserForm.password = PasswordField('password')

@login_manager.user_loader
def load_user(name):
  users = User.objects(name=name)
  if len(users) != 0:
    return users[0]
  else:
    return None

class CalendarEvent(db.Document):
  startDate = db.StringField(required=True)
  endDate = db.StringField(required=True)
  readDate = db.StringField(required=True)
  description = db.StringField(required=True)
  summary = db.StringField(required=True)
  className = db.StringField(required=True)
  userName = db.ReferenceField(User)

def convert(fname, pages=None):
    if not pages:
        pagenums = set()
    else:
        pagenums = set(pages)

    output = StringIO()
    manager = PDFResourceManager()
    converter = TextConverter(manager, output, laparams=LAParams())
    interpreter = PDFPageInterpreter(manager, converter)

    infile = file(fname, 'rb')
    for page in PDFPage.get_pages(infile, pagenums):
        interpreter.process_page(page)
    infile.close()
    converter.close()
    text = output.getvalue()
    output.close
    return text

@app.route("/")
def hello():
  return render_template("hello1.html")

@app.route("/home")
def startHome():
  return render_template("syllabus.html")

@app.route('/uploader', methods = ['GET', 'POST'])
def upload_file():
   if request.method == 'POST':
      f = request.files['file']
      f.save(secure_filename(f.filename))
      result = convert(f.filename)
      os.remove(f.filename)
      dates, events = date_parser.stringToEvents(result)
      saveEvents(dates, events)
      return redirect("/list")

def saveEvents(dates, events) :
  i = 0
  while i < len(dates) :
    cur_startDate, cur_endDate = date_parser.formatDate(dates[i])
    cur_readDate = dates[i]
    cur_description = events[i]
    cur_summary = 'HW EVENT'
    cur_className = 'CLASS'
    cur_userName = User.objects(name=current_user.name).first()
    new_event = CalendarEvent(readDate=cur_readDate, startDate=cur_startDate, endDate=cur_endDate, description=cur_description, summary=cur_summary, className=cur_className, userName=cur_userName)
    possibleDups = CalendarEvent.objects(readDate=new_event.readDate, description=new_event.description, summary=new_event.summary, userName=new_event.userName)
    if len(possibleDups) == 0 :
      new_event.save()
    i += 1

@app.route("/calendar")
def cal():
  current_poster = User.objects(name=current_user.name).first()
  favorites = CalendarEvent.objects(userName=current_poster)
  return render_template("calendar.html", current_user=current_user, favorites=favorites)

@app.route("/upload")
def upload():
	return render_template("hello.html")

@app.route("/register", methods=["POST", "GET"])
def register():
  form = UserForm(request.form)
  if request.method == 'POST' and form.validate():
    form.save()
    return redirect("/login")

  return render_template("register.html", form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
  form = UserForm(request.form)
  if request.method == 'POST' and form.validate():
    user = User(name=form.name.data,password=form.password.data)
    login_user(user)
    return redirect('/upload')

  return render_template('login.html', form=form)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")

@app.route("/search", methods=["POST", "GET"])
@login_required
def search():
	if request.method == "POST":
		url = "https://www.googleapis.com/books/v1/volumes?q=" + request.form["user_search"]
		response_dict = requests.get(url).json()
		return render_template("results.html", api_data=response_dict)
	else: # request.method == "GET"
		return render_template("search.html")

@app.route("/favorite/<id>")
@login_required
def favorite(id):
  book_url = "https://www.googleapis.com/books/v1/volumes/" + id
  book_dict = requests.get(book_url).json()
  poster = User.objects(name=current_user.name).first()
  new_fav = FavoriteBook(author=book_dict["volumeInfo"]["authors"][0], title=book_dict["volumeInfo"]["title"], link=book_url, poster=poster)
  new_fav.save()
  return render_template("confirm.html", api_data=book_dict)

@app.route("/list")
@login_required
def favorites():
  current_poster = User.objects(name=current_user.name).first()
  favorites = CalendarEvent.objects(userName=current_poster)
  return render_template("favorites.html", current_user=current_user, favorites=favorites)

class SychSchedule(Resource):
    def get(self):

      return "hello"

api.add_resource(SychSchedule, '/syncUserSchedule')


@app.route('/about/')
def about():
    """Render the website's about page."""
    return render_template('about.html')


###
# The functions below should be applicable to all Flask apps.
###

@app.route('/<file_name>.txt')
def send_text_file(file_name):
    """Send your static text file."""
    file_dot_text = file_name + '.txt'
    return app.send_static_file(file_dot_text)


@app.after_request
def add_header(response):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
    response.headers['Cache-Control'] = 'public, max-age=600'
    return response


@app.errorhandler(404)
def page_not_found(error):
    """Custom 404 page."""
    return render_template('404.html'), 404


if __name__ == '__main__':
    app.run(debug=True)
