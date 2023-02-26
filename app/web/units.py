def res(app, data):
    #mdict["code"] = mdict.get("code", 0)
    json = {}
    if isinstance(data, dict):
        json['code'] = data.pop("code", 0)
        if "message" in data: json['message'] = data.pop("message")
    else:
        json['code'] = 0
    if data:
        json['data'] = data

    res = app.json.response(json)
    if json['code'] < 0: res.status = 400
    return res
