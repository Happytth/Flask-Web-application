from flask import Flask,render_template,flash,url_for,redirect
from flask_sqlalchemy import SQLAlchemy

app=Flask(__name__)

import config

import model

import routes
   
if __name__=='__main__':
    app.run(debug=True)