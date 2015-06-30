from google.appengine.ext import ndb
from google.appengine.api import users

import os
import cgi
import urllib
import time

import jinja2
import webapp2


template_dir = os.path.join(os.path.dirname(__file__), 'templates')

jinja_environment = jinja2.Environment(
    loader = jinja2.FileSystemLoader(template_dir),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class Author(ndb.Model):
    identity = ndb.StringProperty(indexed=True)
    name = ndb.StringProperty(indexed=False)
    email = ndb.StringProperty(indexed=False)

class Comment(ndb.Model):
    author = ndb.StructuredProperty(Author)
    content = ndb.StringProperty(indexed=False)
    timestamp = ndb.DateTimeProperty(auto_now_add=True)

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

class MainPage(Handler):

    def get_template_values(self, blank_comment_error=''):
        comments_query = Comment.query().order(-Comment.timestamp)
        comments, cursor, more = comments_query.fetch_page(25)

        user = users.get_current_user()

        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            user = 'Anonymous Poster'
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'
            
        template_values = {
            'user': user,
            'comments': comments,
            'url': url,
            'url_linktext': url_linktext,
            'blank_comment_error': blank_comment_error,
        }
        return template_values

    def get(self):
        template = jinja_environment.get_template('page_body.html')
        self.write(template.render(self.get_template_values()))


    def post(self):
        comment = Comment()

        if users.get_current_user():
                comment.author = Author(
                    identity=users.get_current_user().user_id(),
                    name=users.get_current_user().nickname(),
                    email=users.get_current_user().email())

        comment.content = self.request.get('comment')

        if comment.content == '' or comment.content.isspace():
            self.redirect('/error#comments')            

        else:    
            comment.put()

            time.sleep(1) #TODO: get rid of this when I figure why new comments don't display on immediate redirect
            self.redirect('/#comments')


class ErrorHandler(MainPage):
    def get(self):
        template = jinja_environment.get_template('page_body.html')
        self.write(template.render(self.get_template_values('Please write a comment and resubmit')))


app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/sign', MainPage),
    ('/error', ErrorHandler),
], debug=True)