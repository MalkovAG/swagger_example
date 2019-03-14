from flask import Flask, jsonify, make_response, render_template, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect
from marshmallow_sqlalchemy import ModelSchema
from safrs import SAFRSBase, SAFRSAPI
import json

app = Flask('asdfasdf')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
db = SQLAlchemy(app)

class People(SAFRSBase, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'))
    group = db.relationship('Group', backref=db.backref('peoples', lazy='dynamic'))

    # def __init__(self, **kwargs):
    #     self.name = kwargs.get('name')
    #     self.group = kwargs.get('group')

    def __repr__(self):
        return '<People %r>' % self.name


class Group(SAFRSBase, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))

    # def __init__(self, name):
    #     self.name = name

    def __repr__(self):
        return '<Group %r>' % self.name


class PeopleSchema(ModelSchema):
    class Meta:
        model = People


class GroupSchema(ModelSchema):
    class Meta:
        model = Group


def create_api(app, HOST='localhost:5000', PORT=5000, API_PREFIX='/api'):
    api = SAFRSAPI(app, host=HOST, port=PORT, prefix=API_PREFIX)
    api.expose_object(Group)
    api.expose_object(People)
    print('Starting API: http://{}:{}/{}'.format(HOST, PORT, API_PREFIX))


def object_as_dict(obj):
    return {c.key: getattr(obj, c.key)
            for c in inspect(obj).mapper.column_attrs}


def dict_to_object(dct):
    model_name = list(dct.keys())[0]
    for c in People.__table__.columns:
        new_people = People()
        if dct.get(c.name):
            setattr(new_people, c.name, dct[c.name])
    print(new_people)


def create_app(config_filename = None):
    #db.init_app(app)
    with app.app_context():
        db.create_all()
        gr = Group(name='Russians')
        gr2 = Group(name='Germans')
        gr3 = Group(name='American')
        p1 = People(name='Malkov', group=gr)
        p2 = People(name='Petrov', group=gr)
        p3 = People(name='Shnider', group=gr2)
        p4 = People(name='Bob', group=gr3)
        # db.session.commit()
        create_api(app)


if __name__ == "__main__":
    create_app()
    app.run()


@app.route("/")
def hello():
    return "Hello World"


@app.route("/people")
def get_people():
    peoples = People.query.all()
    print(peoples)
    return jsonify(json_list=peoples)


@app.route("/group")
def get_group():
    groups = Group.query.all()
    return render_template('index.html', groups=groups)


@app.route("/add_group", methods=['POST', 'GET'])
def add_group():
    if request.method == 'GET':
        return render_template('add_group.html')

    group_name = request.form.get('group_name')

    group = Group(group_name)
    db.session.add(group)
    db.session.commit()

    return render_template('add_group.html', group=group)


@app.route("/api/get_<type>")
def api_get(type):
    if type == 'peoples':
        peoples = []
        for people in People.query.all():
            peoples.append(object_as_dict(people))
        return jsonify(peoples)
    if type == 'groups':
        groups = []
        for group in Group.query.all():
            groups.append(object_as_dict(group))
        return jsonify(groups)


@app.route("/api/get_people/<id>")
def api_get_people(id):
    p = People.query.get(id)
    people_schema = PeopleSchema()
    return jsonify(people_schema.dump(p).data)


@app.route("/api/add_people", methods=['POST'])
def api_add_people():
    data = request.data
    data = json.loads(data)
    people_schema = PeopleSchema()
    ses = db.session
    p_new = people_schema.load(data, session=ses,transient=True).data
    print(p_new)
    return "ASdfasdf"


@app.route("/api/add_group", methods=['POST'])
def api_add_group():
    data = request.data
    #data = json.loads(data)
    group_schema = GroupSchema()
    ses = db.session
    g_new = group_schema.load(data, session=ses).data
    print(g_new)
    return "add group"


@app.route("/add_people/<group_id>", methods=['POST', 'GET'])
def add_people(group_id):
    group = Group.query.get(group_id)

    if request.method == 'GET':
        return render_template('add_people.html', group=group)

    people_name = request.form.get('people_name')

    people = People(people_name, group)
    db.session.add(people)
    db.session.commit()

    return render_template('add_people.html', people=people, group=group)

