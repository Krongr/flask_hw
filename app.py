import typing
import pydantic
from flask import Flask, request, jsonify
from flask.views import MethodView
from sqlalchemy.orm import sessionmaker

from db import Users, Ads, engine


class HttpError(Exception):
    def __init__(self, status_code, message):
        self.status_code = status_code
        self.message = message


class CreateUser(pydantic.BaseModel):
    name: str
    password: str

class CreateAd(pydantic.BaseModel):
    title: str
    text: str
    user_id: int

class UpdateAd(pydantic.BaseModel):
    title: typing.Optional[str]
    text: typing.Optional[str]

def validate(model, raw_data:dict):
    try:
        return model(**raw_data).dict()
    except pydantic.ValidationError as error:
        raise HttpError(400, error.errors())

Session = sessionmaker(bind=engine)


app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

@app.errorhandler(HttpError)
def http_error_handler(error:HttpError):
    response = jsonify({
        'status': 'error',
        'reason': error.message,
    })
    response.status_code = error.status_code
    return response


class UserView(MethodView):
    def post(self):
        validated = validate(CreateUser, request.json)
        with Session() as session:
            user = Users(
                name=validated['name'],
                password=validated['password']
            )
            session.add(user)
            session.commit()
            return {'id': user.id}


class AdsView(MethodView):
    def get(self):
        with Session() as session:
            ads = session.query(Ads).all()
            result = list()
            for ad in ads:
                result.append({
                    'title': ad.title,
                    'text': ad.text,
                    'owner': ad.ad_owner.name,
                    'created_at': ad.created_at,
                    'id': ad.id,
                })
            return jsonify(result)

    def post(self):
        validated = validate(CreateAd, request.json)
        with Session() as session:
            ad = Ads(
                title=validated['title'],
                text=validated['text'],
                owner=validated['user_id'],
            )
            session.add(ad)
            session.commit()
            return {'id': ad.id}

    def patch(self, ad_id):
        if ad_id is None:
            raise HttpError(400, "ad ID is required")
        validated = validate(UpdateAd, request.json)
        with Session() as session:
            ad = session.query(Ads).get(ad_id)
            if ad is None:
                raise HttpError(410, "requested ad has been removed")
            ad.title = validated.get('title') or ad.title
            ad.text = validated.get('text') or ad.text
            session.add(ad)
            session.commit()
            return {'status': 'ok'}

    def delete(self, ad_id):
        if ad_id is None:
            raise HttpError(400, "ad ID is required")
        with Session() as session:
            ad = session.query(Ads).get(ad_id)
            if ad is None:
                return {'status': 'ok'}
            session.delete(ad)
            session.commit()
            return {'status': 'ok'}


users_view = UserView.as_view('users')
ads_view = AdsView.as_view('ads')

app.add_url_rule('/users/', view_func=users_view, methods=['POST'])
app.add_url_rule('/ads/', view_func=ads_view, methods=['GET', 'POST'])
app.add_url_rule(
    '/ads/<int:ad_id>', view_func=ads_view, methods=['PATCH', 'DELETE'])

if __name__ == "__main__":
    app.run(port=5000)