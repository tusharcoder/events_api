from flask import Flask, make_response
from flask_restful import Resource, Api
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///events.sqllite3'
api = Api(app)
db=SQLAlchemy(app)
HOST = "0.0.0.0"

class EventModel(db.Model):
    id = db.Column('id',db.Integer, primary_key=True)
    meeting_link=db.Column(db.Text,nullable=False,unique=True)
    title=db.Column(db.String(500),nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

class Hello(Resource):
    def get(self):
        return make_response({"message":"Hello World"},200)

api.add_resource(Hello,'/')

if __name__=="__main__":
    app.run(host=HOST,port=8000)
