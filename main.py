from flask import Flask, make_response
from flask.json import jsonify
from flask_restful import Resource, Api
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from sqlalchemy.sql import func

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///events.sqlite3'
api = Api(app)
ma = Marshmallow(app)
db=SQLAlchemy(app)
HOST = "0.0.0.0"

class EventModel(db.Model):
    id = db.Column('id',db.Integer, primary_key=True)
    meeting_link=db.Column(db.Text,nullable=False,unique=True)
    title=db.Column(db.String(500),nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

class EventResourceSchema(ma.Schema):
    class Meta:
        fields=(
                'id',
                'title',
                'meeting_link',
                'created_at',
                )
events_resource_schema = EventResourceSchema(many=True)
event_resource_schema = EventResourceSchema()
class Hello(Resource):
    def get(self):
        return make_response({"message":"Hello World"},200)

class AllEventResource(Resource):
    def get(self):
        """
        An api to return the list of all events
        """
        events = db.session.query(EventModel).all()
        result = events_resource_schema.dump(events)
        return make_response(result, 200)

class EventResource(Resource):
    def get(self,id):
        """
        An api to return the specific event
        """
        event = db.session.query(EventModel).filter_by(id=id).first()
        if not event:
            return make_response({'message':'event id not exist...'}, 404)
        else:
            result = event_resource_schema.dump(event)
            return make_response(result,200)

api.add_resource(Hello,'/')
api.add_resource(AllEventResource, '/events')
api.add_resource(EventResource, '/event/<id>')

if __name__=="__main__":
    app.run(host=HOST,port=8000, debug=True)
