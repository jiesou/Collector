import json
def response(mdict):
    mdict.code = 0 if not mdict.code else mdict.code
    return flask.json.jsonify(mdict)