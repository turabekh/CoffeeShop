import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)


# db_drop_and_create_all()

## ROUTES
@app.route("/drinks", methods=["GET"])
def get_drinks():
    drinks = Drink.query.all() 
    drinks = [d.short() for d in drinks]
    return jsonify({
        "success": True, 
        "drinks": drinks
    }), 200


@app.route("/drinks-detail")
@requires_auth(permission="get:drinks-detail")
def get_drink_detail(jwt):
    drinks = Drink.query.all() 
    drinks = [d.long() for d in drinks]
    return jsonify({
        "success": True, 
        "drinks": drinks
    }), 200


@app.route("/drinks", methods=["POST"])
@requires_auth(permission="post:drinks")
def create_drink(jwt):
    body = request.get_json() 
    if "title" not in body or "recipe" not in body:
        abort(400)
    title = body.get("title", None)
    recipe = body.get("recipe", None) 
    try:
        drink = Drink(title=title, recipe=json.dumps(recipe))
        drink.insert()
    except:
        abort(422) 
    return jsonify({"success": True, "drinks": drink.long()})


@app.route("/drinks/<int:id>", methods=["PATCH"])
@requires_auth(permission="patch:drinks")
def update_drink(jwt,id):
    if not id:
        abort(404) 
    body = request.get_json() 
    try:
        recipe = body.get("recipe", None) 
        title = body.get("title", None)
        drink = Drink.query.filter(Drink.id == id).one_or_none()
        if recipe is not None:
            drink.recipe = json.dumps(recipe)
        if title is not None:
            drink.title = title
        drink.update()
    except:
        abort(422)
    return jsonify({"success": True,  "drinks": drink.long()})


@app.route("/drinks/<int:id>", methods=["DELETE"])
@requires_auth(permission="delete:drinks")
def delete_drink(jwt, id):
    if not id:
        abort(404)
    try:
        drink = Drink.query.filter(Drink.id == id).one_or_none()
        drink.delete()
    except:
        abort(422) 
    return jsonify({"success": True, "delete": drink.id})

## Error Handling

@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
                    "success": False, 
                    "error": 422,
                    "message": "unprocessable"
                    }), 422

@app.errorhandler(404)
def not_found(error):
    return jsonify({
                    "success": False, 
                    "error": 404,
                    "message": "not found"
                    }), 404

@app.errorhandler(400)
def bad_request(error):
    return jsonify({
                    "success": False, 
                    "error": 400,
                    "message": "bad request"
                    }), 400
                
@app.errorhandler(401)
def not_authorized(error):
    return jsonify({
                    "success": False, 
                    "error": 401,
                    "message": "Not Authorized"
                    }), 401


@app.errorhandler(AuthError)
def authorization_failed(error):
    return jsonify({
                    "success": False, 
                    "error": error.status_code,
                    "message": error.error
                    }), error.status_code
