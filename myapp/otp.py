#!/usr/bin/env python
# -*- coding: utf-8 -

import uuid
import onetimepass as otp

from peewee import *
from flask import request, redirect, render_template,  make_response, flash

from myapp import app

db = SqliteDatabase('db.sqlite3', check_same_thread=False)


class BaseModel(Model):
    class Meta:
        database = db


class User(BaseModel):
    login = CharField(unique=True)
    secret = CharField(null=False)
    emergency = CharField(null=True)
    sid = CharField(null=True)


def valid_emergency(user, code):
    is_valid = False
    emergency = (user.emergency).split(',')
    code = str(code)

    if code in emergency:
        is_valid = True
        emergency.remove(code)

        try:
            user.emergency = ','.join(emergency)
            user.save()
        except Exception, e:
            print "Unexpected error: %s" % e

    return is_valid


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "GET":
        return render_template('login.html')

    if request.method == "POST":

        if 'login' in request.form and 'code' in request.form:
            login = request.form["login"]

            try:
                code = int(request.form["code"])
            except:
                flash("Forbidden.", "danger")
                return redirect(request.referrer, code=302)

            try:
                user = User.get(User.login == login)
            except User.DoesNotExist:
                flash("Forbidden.", "danger")
                return redirect(request.referrer, code=302)

            if otp.valid_totp(token=code, secret=user.secret, window=0) or valid_emergency(user, code):
                sid = str(uuid.uuid4())
                resp = make_response(redirect(request.referrer, code=302))

                try:
                    user.sid = sid
                    user.save()
                    resp.set_cookie('x-factor-sid', sid, httponly=True)
                except Exception, e:
                    print "Unexpected error: %s" % e

                return resp
            else:
                flash("Forbidden.", "danger")
                return redirect(request.referrer, code=302)
        else:
            flash("Forbidden.", "danger")
            return redirect(request.referrer, code=302)


@app.route("/auth", methods=["GET"])
def auth():

    sid = request.cookies.get('x-factor-sid')

    if sid is None:
        return "Unauthorized", 401

    try:
        User.get(User.sid == sid)
    except User.DoesNotExist:
        return "Unauthorized", 401
    else:
        return "Success", 200
