import requests
import asyncio
import json

# "source_url": f"https://google-extension2.s3.ap-northeast-2.amazonaws.com/upload/{key}"


async def create_did(key, img_url):
    url = "https://api.d-id.com/talks"

    payload = {
        "script": {
            "type": "text",
            "provider": {"type": "microsoft", "voice_id": "ko-KR-SeoHyeonNeural"},
            "ssml": "false",
            "input": f"{key}",
        },
        "config": {
            "fluent": "false",
            "pad_audio": "0.0",
            "result_format": "mp4",
            "stitch": True,
            "sharpen": True,
            "align_expand_factor": 0,
        },
        "source_url": img_url,
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": "Basic YzJWdmJtZGxiMjR3T0RSQVoyMWhhV3d1WTI5dDpQN0ljdzR4QUN4SGhBWVJLSWF5U08=",
    }

    response = requests.post(url, json=payload, headers=headers)

    return response.text


async def get_did(talk_id):
    url = f"https://api.d-id.com/talks/{talk_id}"

    headers = {
        "accept": "application/json",
        "authorization": "Basic YzJWdmJtZGxiMjR3T0RSQVoyMWhhV3d1WTI5dDpQN0ljdzR4QUN4SGhBWVJLSWF5U08=",
    }

    response = requests.get(url, headers=headers)

    return response.text


# D-ID 영상 생성
async def make_d_id(msg, URL):
    creation = json.loads(await create_did(msg, URL))
    print(creation)
    while True:
        result = json.loads(await get_did(creation["id"]))
        result_url = result.get("result_url")
        if result_url:
            break
    print("생성~")
    return result_url


if __name__ == "__main__":
    img_url = "https://d2frc9lzfoaix3.cloudfront.net/youknow.jpg"
    tmp = asyncio.run(make_d_id("안녕하세요", img_url))
    print(tmp)
