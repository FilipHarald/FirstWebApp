#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import webapp2
import jinja2
import os
import cgi
import encrypter
import authenticator
import hasher
from google.appengine.ext import db


#defines the entities (blog posts) stored in the database
class BlogPost(db.Model):
    subject = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)


#defines the entities (blog users) stored in the database
class BlogUser(db.Model):
    username = db.StringProperty(required=True)
    pw_hash = db.StringProperty(required=True)
    email = db.StringProperty(required=False)
    created = db.DateTimeProperty(auto_now_add=True)


#initializes templates (jinja)
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir), autoescape=True)


class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))


def escape_html(s):
    return cgi.escape(s, quote=True)

#anvandes innan jag larde mig templates
with open('./templates/rot13.html') as f:
    Rot13Html = f.read()


class MainPage(Handler):
    def get(self):
        #self.response.headers['Content-Type'] = 'text/html'
        visits = self.request.cookies.get('visits', '0')
        if visits.isdigit():
            visits = int(visits) + 1
        else:
            visits = 0
        self.response.headers.add_header('Set-Cookie', 'visits=%s' % visits)
        self.render("main.html", visits=visits)


class Rot13Page(Handler):
    def write_form(self, written_text="Jevgr lbhe grkg urer."): #"Wtrite your text here"
        self.response.out.write(Rot13Html % escape_html(encrypter.encrypt_text(written_text)))

    def get(self):
        self.write_form()

    def post(self):
        self.write_form(self.request.get("text"))


class FizzBuzzPage(Handler):
    def get(self):
        n = self.request.get('n', 0)
        n = n and int(n)
        self.render("fizzbuzz.html", n=n)


class SignUpPage(Handler):
    def get(self):
        self.render('blog_sign_up.html')

    def post(self):
        error_user_exists = "A user with that name does already exist."
        error_username = "That's not a valid username."
        error_password = "That's not a valid password."
        error_verify = "The passwords does not match."
        error_email = "That's not a valid email"
        username = self.request.get("username")
        password = self.request.get("password")
        verify = self.request.get("verify")
        email = self.request.get("email")
        if username:
            q = db.GqlQuery("SELECT * FROM BlogUser WHERE username = '%s'" % username)
            user = q.get()
            if not user:
                error_user_exists = ""
            if authenticator.valid_username(username):
                error_username = ""
        if password:
            if authenticator.valid_password(password):
                error_password = ""
        if verify:
            if verify == password:
                error_verify = ""
        if not email or authenticator.valid_email(email):
            error_email = ""
        if error_user_exists or error_username or error_password or error_verify or error_email:
            self.render('blog_sign_up.html',
                        username=username,
                        email=email,
                        error_user_exists=error_user_exists,
                        error_username=error_username,
                        error_password=error_password,
                        error_verify=error_verify,
                        error_email=error_email)
        else:
            blog_user = BlogUser(username=username, pw_hash=(hasher.make_pw_hash(username, password)), email=email)
            blog_user.put()
            user_id = str(blog_user.key().id())
            cookie_text = hasher.make_secure_val(user_id)
            self.response.headers.add_header('Set-Cookie', 'user_id=%s; Path=/' % cookie_text)
            self.redirect('/blog/welcome')


class LoginPage(Handler):
    def get(self):
        self.render('blog_login.html')

    def post(self):
        error_invalid_login = "Invalid login"
        username = self.request.get("username")
        password = self.request.get("password")
        if username:
            q = db.GqlQuery("SELECT * FROM BlogUser WHERE username = '%s'" % username)
            blog_user = q.get()
            if blog_user:
                if hasher.valid_pw(username, password, blog_user.pw_hash):
                    user_id = str(blog_user.key().id())
                    cookie_text = hasher.make_secure_val(user_id)
                    self.response.headers.add_header('Set-Cookie', 'user_id=%s; Path=/' % cookie_text)
                    self.redirect('/blog/welcome')
                else:
                    self.render('blog_login.html', username=username, error_invalid_login=error_invalid_login)
            else:
                self.render('blog_login.html', username=username, error_invalid_login=error_invalid_login)


class LogoutPage(Handler):
    def get(self):
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')
        self.redirect('/blog/signup')


class WelcomePage(Handler):
    def get(self):
        user_cookie = self.request.cookies.get('user_id')
        user_id = hasher.check_secure_val(user_cookie)
        if user_id:
            key = db.Key.from_path('BlogUser', int(user_id))
            username = (db.get(key)).username
            self.render('blog_welcome.html', username=username)
        else:
            self.redirect('/blog/signup')


class BlogFrontPage(Handler):
    def get(self):
        posts = db.GqlQuery('select * from BlogPost order by created desc')
        self.render("blog_front.html", posts=posts)


class BlogNewPostPage(Handler):
    def get(self):
        self.render("blog_new_post.html")

    def post(self):
        subject = self.request.get("subject")
        content = self.request.get("content")
        if subject and content:
            #db.delete(db.Query(keys_only=True))
            #skapar en BlogPost "entity"
            blog_post = BlogPost(subject=subject, content=content)
            #och lagger in den i databasen
            blog_post.put()
            self.redirect('/blog/%s' % str(blog_post.key().id()))


class BlogPermalinkPage(Handler):
    def get(self, post_id):
        key = db.Key.from_path('BlogPost', int(post_id))
        post = db.get(key)
        self.render("blog_permalink.html", post=post)


app = webapp2.WSGIApplication([('/', MainPage),
                               ('/Rot13', Rot13Page),
                               ('/blog/signup', SignUpPage),
                               ('/blog/login', LoginPage),
                               ('/blog/logout', LogoutPage),
                               ('/blog/welcome', WelcomePage),
                               ('/FizzBuzz', FizzBuzzPage),
                               ('/blog', BlogFrontPage),
                               ('/blog/newpost', BlogNewPostPage),
                               ('/blog/([0-9]+)', BlogPermalinkPage)],
                              debug=True)
