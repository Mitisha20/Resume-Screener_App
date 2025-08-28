
# standardize success/error responses across the API.

from flask import jsonify

def ok(message=None, **data):
   
    payload = {"status": "success"}
    if message:
        payload["message"] = message
    if data:
        payload["data"] = data
    return jsonify(payload), 200

def created(message=None, **data):
    
    payload = {"status": "success", "created": True}
    if message:
        payload["message"] = message
    if data:
        payload["data"] = data
    return jsonify(payload), 201

def fail(message, code=400, *, details=None):
    
    body = {"status": "error", "message": message}
    if details is not None:
        body["details"] = details
    return jsonify(body), code
