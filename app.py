from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, session
from modules.did import make_d_id
from modules.chat import being_call
from modules.aws import AwsQuery
from modules.db import db_select_id, db_insert, db_delete, db_select_url
import asyncio
import requests
import json
import time
from urllib.request import urlopen

app = Flask(__name__)
app.config["SECRET_KEY"] = "PICA"


@app.route("/get_img")
def get_img():
    # db에서 cloudflont url 가져오기
    print(session)
    urls = db_select_url(db_select_id(session.get("user_id")))
    return jsonify({"url": urls[1]})


@app.route("/delete_img", methods=["GET", "POST"])
def delete_img():
    # url 받아오기
    url = request.get_json().get("url")
    user_id, name = url.split("/")[-2], url.split("/")[-1]
    # aws s3 데이터 삭제
    aws = AwsQuery()
    asyncio.run(aws.s3_delete(user_id, name))
    # db & session 삭제
    db_delete(db_select_id(user_id))
    session.pop("user_id", None)

    del aws
    return jsonify({"data": None})


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/chatbot")
def chatbot():
    try:
        # url에 데이터 있는지 화인 없으면 except
        urls = db_select_url(db_select_id(session.get("user_id")))
        res = urlopen(urls[1])
        print(res.status)
        # session 상태 확인
        if "user_id" not in session:
            flash("이미지를 생성하지 못했습니다. 다시 생성해 주세요")
            return redirect(url_for("home"))
        else:
            return render_template("chatbot.html")
    except Exception as e:
        flash("이미지가 삭제되었습니다. 새로운 캐릭터를 만들어주세요!")
        return redirect(url_for("home"))


@app.route("/loading")
def loading():
    time.sleep(5)
    return render_template("loading.html")


# s3 업로드
@app.route("/get_data", methods=["GET", "POST"])
def get_data():
    # 데이터 받아오기
    b_img = request.get_json()["b_img"]
    user_id = request.get_json()["userID"]
    session["user_id"] = user_id

    try:
        # 2. 스테이블 디퓨전 서버에 POST 전송
        res = requests.post(
            "https://10fbde2d-c458-46f1.gradio.live/base64file",
            json.dumps({"base64_file": b_img, "user_id": user_id}),
        )
        print(res.status_code)

        res_text = res.json()
        img_name = json.loads(res_text).get("img_name")

        # 3. url 생성
        aws = AwsQuery()
        url = aws.CLOUD_FLONT_CDN + f"/{user_id}/{img_name}"

        # 4. db-user, url 테이블 삽입
        db_insert("user", user_id)
        id_value = db_select_id(user_id)
        db_insert("url", f"'{url}', '{url}', '{url}', {id_value}")
        print(url)

    except Exception as e:
        print("request error : ", e)

    del aws
    # 웹에 전달
    return jsonify({"url": url})


@app.route("/send_message", methods=["GET", "POST"])
def send_message():
    try:
        # voice
        data = request.get_json()["inputdata"]
        # gpt
        being_msg = asyncio.run(being_call(data))

        # voice 와 bing 대답 로그 DB 저장
        # a_status : 감정 상태
        a_status = 1
        id_value = db_select_id(session["user_id"])
        db_insert("log", f"'{data}', '{being_msg}', {a_status}, {id_value}")

        # 감정 결과 fun,sad,angry -> urls[1], urls[2], urls[3]
        urls = db_select_url(db_select_id(session.get("user_id")))
        # d-id
        d_id = asyncio.run(make_d_id(being_msg, urls[1]))
    except asyncio.TimeoutError:
        print("except error")

    return jsonify({"video_url": d_id})


if __name__ == "__main__":
    app.run(debug=True)
