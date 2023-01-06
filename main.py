from flask import Flask, make_response, request
from flask.json import jsonify
from flask_restful import Resource, Api
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from sqlalchemy.sql import func
from werkzeug.security import generate_password_hash, check_password_hash
import jwt

import uuid
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///events.sqlite3'
app.config['SECRET_KEY'] = 'd42340e0-7846-40cd-8f66-6f9d2d3ddfbb'
api = Api(app)
ma = Marshmallow(app)
db=SQLAlchemy(app)
HOST = "0.0.0.0"

REQUIRED_ERROR_TEXT = 'this field is required'


def init_db(db):
    """
    this is the function responsible to initiate the db tables which are not there
    """
    db.drop_all()
    db.create_all()

def tokin_required(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        token = None
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        if not token:
            return {"message":"Token is missing..."} 
        data = jwt.decode(token,app.config['SECRET_KEY'],algorithms='HS256')
        current_user = UserModel.query.filter_by(public_id=data.get('public_id')).first()
        if not current_user:
            return {"message":"Token is invalid..."}
        request.user = current_user
        return func(*args, **kwargs)
    return decorated

class UserModel(db.Model):
    """
    User model which stores the user information like username, password
    """
    id = db.Column('id',db.Integer, primary_key=True)
    public_id = db.Column(db.String(50), unique=True, nullable=False)
    username = db.Column(db.String(250), nullable=False, unique=True) # will store the email in here
    password = db.Column(db.String(2000), nullable=False)

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

class UserResource(Resource):
    """
    this is the user related views like registration, login
    """
    def post(self):
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        public_id = str(uuid.uuid4())
        REQUIRED_ERROR_TEXT = 'this field is required'
        errors = {}
        if not username:
            errors['username']=REQUIRED_ERROR_TEXT
        elif db.session.query(UserModel).filter_by(username=username).first():
            errors['username']='User already exist with the provided username...'
        if not password:
            errors['password']=REQUIRED_ERROR_TEXT
        if errors:
            return make_response({"message":"Registration Unsuccessful...","errors":errors},400)
        password = generate_password_hash(password)
        user = UserModel(username=username, password=password, public_id=public_id)
        db.session.add(user)
        db.session.commit()
        return {"message":"Registration Successful"},201 # this is automatically covert to json and return as response by Flask-Restful
        
class LoginResource(Resource):
    """
    Resource for API login
    """
    def post(self):
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        errors={}
        if not username:
            errors['username']= REQUIRED_ERROR_TEXT
        if not password:
            errors['password']= REQUIRED_ERROR_TEXT
        if errors:
            return {'message':'unable to login','errors':errors}, 400
        user = UserModel.query.filter_by(username=username).first()
        if not user:
            return {'message':'Email and password combination is wrong...'}, 401
        if check_password_hash(user.password,password):
            token = jwt.encode({
                'public_id':user.public_id,
                'exp': datetime.utcnow()+timedelta(minutes=30),
            }, app.config['SECRET_KEY'],algorithm='HS256')
            return {"message":"Login Succesful...","token":token}, 201
        else:
            return {'message':'Email and password combination is wrong...'}, 401
    
class AllEventResource(Resource):
    @tokin_required
    def get(self):
        """
        An api to return the list of all events
        """
        events = db.session.query(EventModel).all()
        result = events_resource_schema.dump(events)
        return make_response(result, 200)

    @tokin_required
    def post(self):
        """
        An api to post the event
        """
        data=request.get_json()
        title = data.get('title')
        meeting_link = data.get('meeting_link')
        errors = {}
        if not title:
            errors['title']='title is required'
        if not meeting_link:
            errors['meeting_link']='meeting_link is required'
        if errors:
            return make_response({'message':'unable to create event','errors':errors},400)
        event = EventModel(title=title,meeting_link=meeting_link)
        db.session.add(event)
        db.session.commit()
        result = event_resource_schema.dump(event)
        return make_response({'message':'event created','data':result},201)

class EventResource(Resource):
    @tokin_required
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

    @tokin_required
    def put(self,id):
        """
        An api to update the specific event
        """
        event = db.session.query(EventModel).filter_by(id=id).first()
        if not event:
            return make_response({'message':'event id not exist...'}, 404)
        else:
            data = request.get_json()
            title = data.get('title')
            meeting_link = data.get('meeting_link')
            event.title=title
            event.meeting_link=meeting_link
            db.session.commit()
            result = event_resource_schema.dump(event)
            return make_response(result,200)

    @tokin_required
    def delete(self,id):
            """
            An api to delete the specific event
            """
            event = db.session.query(EventModel).filter_by(id=id).first()
            if not event:
                return make_response({'message':'event id not exist...'}, 404)
            else:
                db.session.delete(event)
                db.session.commit()
                return make_response({'message':'event deleted successfully'}, 201)

api.add_resource(Hello,'/')
api.add_resource(UserResource,'/user/register')
api.add_resource(LoginResource,'/user/login')
api.add_resource(AllEventResource, '/events')
api.add_resource(EventResource, '/event/<id>')

app.app_context().push() # this is necessary for pushing application contect, so as db.create_all to work
init_db(db)

if __name__=="__main__":
    app.run(host=HOST,port=8000, debug=True)
