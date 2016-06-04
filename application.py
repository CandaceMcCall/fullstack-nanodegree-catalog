# Catalog Application
# Candy McCall
# Udacity Full Stack Developer NanoDegree
#
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy import create_engine, asc, desc
from sqlalchemy.orm import sessionmaker
from database_setup import Category, Base, Item, User

from flask import session as login_session
import random, string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
import datetime

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog Application"

#
# Connect to database and create database session
#
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()
#
# Show Login
#
# Create a state token to prevent request forgery
# Store it in the session for later validation.
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits) 
        for x in xrange(32))
    login_session['state'] = state
    # RENDER THE LOGIN TEMPLATE
    return render_template('login.html', STATE=state)
    #return "The current session is %s" %login_session['state']

#
# Google Connect
#
@app.route('/gconnect', methods=['POST'])
def gconnect():
  # Validate state token
  if request.args.get('state') != login_session['state']:
    response = make_response(json.dumps('Invalid state parameter'), 401)
    response.headers['Content-Type'] = 'application/json'
    return response
  # Obtain authorization code
  code = request.data
  try:
    # Upgrade the authorization code into a credentials object
    oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
    oauth_flow.redirect_uri = 'postmessage'
    credentials = oauth_flow.step2_exchange(code)
  except FlowExchangeError:
    response = make_response(
       json.dumps('Failed to upgrade the authorization code.'), 401)
    response.headers['Content-Type'] = 'application/json'
    return response

  # Check that the access token is valid.
  access_token = credentials.access_token
  url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)
  h = httplib2.Http()
  result = json.loads(h.request(url, 'GET')[1])
  # If there was an error in the access token info, abort.
  if result.get('error') is not None:
    response = make_response(json.dumps(result.get('error')), 500)
    response.headers['Content-Type'] = 'application/json'
 # Verify that the access token is used for the intended user.
  gplus_id = credentials.id_token['sub']
  if result['user_id'] != gplus_id:
    response = make_response(
       json.dumps("Token's user ID doesn't match given user ID."), 401)
    response.headers['Content-Type'] = 'application/json'
    return response

  # Verify that the access token is valid for this app.
  if result['issued_to'] != CLIENT_ID:
    response = make_response(
       json.dumps("Token's client ID does not match app's."), 401)
    print "Token's client ID does not match app's."
    response.headers['Content-Type'] = 'application/json'
    return response

  # Check to see if user is already logged in
  stored_credentials = login_session.get('credentials')
  stored_gplus_id = login_session.get('gplus_id')
  if stored_credentials is not None and gplus_id == stored_gplus_id:
    response = make_response(
       json.dumps('Current user is already connected.'), 200)
    response.headers['Content-Type'] = 'application/json'
    return response

  # Store the access token in the session for later use
  login_session['credentials'] = credentials
  #login_session['access_token'] = credentials.access_token
  login_session['gplus_id'] = gplus_id
  response = make_response(json.dumps('Successfully connected user.'), 200)

  # Get user info
  userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
  params = {'access_token': credentials.access_token, 'alt': 'json'}
  answer = requests.get(userinfo_url, params=params)

  data = answer.json()

  login_session['username'] = data['name']
  login_session['picture'] = data['picture']
  login_session['email'] = data['email']
  # ADD PROVIDER TO LOGIN SESSION
  login_session['provider'] = 'google'
 # see if user exists, if it doesn't make a new one
  user_id = getUserID(login_session['email'])
  if not user_id:
    user_id = createUser(login_session)
  login_session['user_id'] = user_id

  output = ''
  output += '<h1>Welcome, '
  output += login_session['username']

  output += '!</h1>'
  output += '<img src="'
  output += login_session['picture']
  output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
  flash("you are now logged in as %s" % login_session['username'])
  print "done!"
  return output

#
# Google Disconnect
# Revoke a current user's token and reset their login_session.
@app.route("/gdisconnect")
def gdisconnect():
   # Only disconnect a connected user.
   credentials = login_session.get('credentials')
   print 'User name is: ' 
   print login_session['username']
   
   if credentials is None:
     response = make_response(json.dumps('Current user not connected.'), 401)
     response.headers['Content-Type'] = 'application/json'
     return response
   # Execute HTTP GET request to revoke current token.
   access_token = credentials.access_token
   url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
   #url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
   h = httplib2.Http()
   result = h.request(url, 'GET')[0]
   #print 'result is'
   #print result

   if result['status'] != '200':
       response = make_response(json.dumps('Failed to revoke token for given user.', 400))
       response.headers['Content-Type'] = 'application/json'
       return response
   
#
# Facebook Connect
#
@app.route('/fbconnect', methods=['POST'])
def fbconnect():
  # Validate state token
  if request.args.get('state') != login_session['state']:
    response = make_response(json.dumps('Invalid state parameter'), 401)
    response.headers['Content-Type'] = 'application/json'
    return response
  access_token = request.data
  #print "access token received %s " % access_token

  #Exchange client token for long-lived server-side token with GET /oauth/
  # access_token?grant_type=fb_exchange_token&client_id={app-id}&client_secret=
  # {app-secret}&fb_exchange_token={short-lived-token}
  app_id = json.loads(open('fb_client_secrets.json','r').read())['web']['app_id']
  app_secret = json.loads(open(
	  'fb_client_secrets.json','r').read())['web']['app_secret']
  url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
        app_id, app_secret, access_token)
  #url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (app_id, app_secret,access_token)
  h = httplib2.Http()
  result = h.request(url, 'GET')[1]

  # Use token to get user info from API
  userinfo_url = "https://graph.facebook.com/v2.4/me"
  # Strip expire tag from access token
  token = result.split("&")[0]

  url = 'https://graph.facebook.com/v2.4/me?%s&fields=name,id,email' % token
  h = httplib2.Http()
  result = h.request(url, 'GET')[1]
  #print "url sent for API access:%s"% url
  #print "API JSON result:  %s" % result
  data = json.loads(result)
  login_session['provider'] = 'facebook'
  login_session['username'] = data["name"]
  login_session['email'] = data["email"]
  login_session['facebook_id'] = data["id"]

  # The token must be stored in the login_session in order to properly logout, let's strip out the information before the equals sign in our token
  stored_token = token.split("=")[1]
  login_session['access_token'] = stored_token
  
  # Get user picture
  url = 'https://graph.facebook.com/v2.4/me/picture?%s&redirect=0&height=200&width=200' % token
  h = httplib2.Http()
  result = h.request(url, 'GET')[1]
  data = json.loads(result)

  login_session['picture'] = data["data"]["url"]
  # see if user exists, if it doesn't make a new one
  user_id = getUserID(login_session['email'])
  if not user_id:
    user_id = createUser(login_session)
  login_session['user_id'] = user_id

  output = ''
  output += '<h1>Welcome, '
  output += login_session['username']

  output += '!</h1>'
  output += '<img src="'
  output += login_session['picture']
  output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
  flash("Now logged in as %s" % login_session['username'])
  print "done!"
  return output

#
# Facebook Disconnect
#
@app.route("/fdisconnect")
def fbdisconnect():
   facebook_id = login_session['facebook_id']
   # The access token must be included to successfully logout
   access_token = login_session['access_token']
   url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id,access_token)
   h = httplib2.Http()
   result = h.request(url, 'DELETE')[1]
   return "you have been logged out"

#
# Disconnect (General)
#
@app.route('/disconnect')
def disconnect():
   if 'provider' in login_session:
     if login_session['provider'] == 'google':
       gdisconnect()
       del login_session['gplus_id']
       del login_session['credentials']
     if login_session['provider'] == 'facebook':
       fbdisconnect()
       del login_session['facebook_id']

     del login_session['username']
     del login_session['email']
     del login_session['picture']
     del login_session['user_id']
     del login_session['provider']
     flash( "You have successfully been logged out.")
     return redirect(url_for('showCategories'))
   else:
     flash( "You were not logged in to begin with!")
     return redirect(url_for('showCategories'))


#
# Making an API Endpoint (GET Request)
# All Items
#
@app.route('/items/JSON')
def allItemsJSON():
    items = session.query(Item).order_by(desc(Item.created)).all()
    return jsonify(Items=[i.serialize for i in items])

#
# Show all categories
# 
@app.route('/')
@app.route('/catalog/')
def showCategories():
    categories = session.query(Category).all()
    items = session.query(Item).order_by(desc(Item.created)).all()
    if 'username' not in login_session:
   	print 'public_categories' 
        return render_template('public_categories.html', categories = categories,items=items)
    else:
        return render_template('categories.html', categories = categories,items=items)

#
# Show all items for a particular category
#
@app.route('/catalog/<category_name>/')
@app.route('/catalog/<category_name>/items')
def showItems(category_name):
    categories = session.query(Category).all()
    category = session.query(Category).filter_by(name = category_name).one()
    numitems = session.query(Item).filter_by(category_id = category.id).count()
    char_numitems = str(numitems)
    items = session.query(Item).filter_by(category_id = category.id)
    return render_template('items_per_category.html', categories = categories, itemcategory = category,items=items,numitems = char_numitems)

#
# Show particular item for a given category
#
@app.route('/catalog/<category_name>/<item_title>')
def showItem(category_name,item_title):
    item = session.query(Item).filter_by(title = item_title).one()
    creator = getUserInfo(item.user_id)
    if 'username' not in login_session:
       return render_template('public_show_item.html', item=item,category_name=category_name,creator=creator)
    else:
       return render_template('show_item.html', item=item,category_name=category_name,creator=creator)

#
# New Item (Add item)
#
@app.route('/catalog/new', methods=['GET', 'POST'])
def newItem():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        chosenCategory = session.query(Category).filter_by(name = request.form['category_name']).one()
	newItem = Item(
	    user_id=login_session['user_id'],
	    title = request.form['title'], 
	    description = request.form['description'], 
	    category = chosenCategory,
	    created=datetime.datetime.now())
	session.add(newItem)
	session.commit()
	flash('New item %s successfully created.' % newItem.title)
	return redirect(url_for('showCategories'))
    else:
        categories = session.query(Category).all()
	return render_template('newitem.html', categories=categories)

# Edit item in catalog

@app.route('/catalog/<item_title>/edit', methods=['GET', 'POST'])
def editItem(item_title):
    editedItem = session.query(Item).filter_by(title = item_title).one()
    if 'username' not in login_session:
        return redirect('/login')
    if editedItem.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to edit this item. Please create your own item in order to edit.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
	if request.form['title']:
	    editedItem.title = request.form['title']
	if request.form['description']:
	    editedItem.description = request.form['description']
	if request.form['category_name']:
	    editedItem.category.name = request.form['category_name']
	session.add(editedItem)
	session.commit()
	flash('Item %s updated.' % editedItem.title)
	return redirect(url_for('showCategories'))
    else:
        categories = session.query(Category).all()
    	itemsCategory = session.query(Category).filter_by(id=editedItem.category_id).one()
	return render_template('edititem.html', item = editedItem, categories=categories,category=itemsCategory)
#
# Delete item from catalog
#	
@app.route('/catalog/<item_title>/delete', methods=['GET', 'POST'])
def deleteItem(item_title):
    if 'username' not in login_session:
        return redirect('/login')
    itemToDelete = session.query(Item).filter_by(title=item_title).one()
    print getUserInfo(itemToDelete.user_id).email
    print getUserInfo(itemToDelete.user_id).name
    print login_session['user_id']
    print getUserInfo(login_session['user_id']).email
    print getUserInfo(login_session['user_id']).name
    if itemToDelete.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to delete this item. Please create your own item in order to delete items.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
	flash('Item %s deleted.' % itemToDelete.title)
        return redirect(url_for('showCategories'))
    else:
    	itemsCategory = session.query(Category).filter_by(id=itemToDelete.category_id).one()
        return render_template('deleteitem.html', item=itemToDelete,category=itemsCategory)

def createUser(login_session):
    newUser = User(name = login_session['username'], email =
		login_session['email'], picture = login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email = login_session['email']).one()
    return user.id

def getUserInfo(user_id):
    user = session.query(User).filter_by(id = user_id).one()
    return user

def getUserID(email):
    try:
	user = session.query(User).filter_by(email = email).one()
	return user.id
    except:
	return None



if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host = '0.0.0.0', port = 8000)
