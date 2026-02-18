import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PushService:

    # 读取环境变量中的敏感信息
    APPID = os.getenv("APP_ID")  # 对应 YAML 中的 env.API_KEY
    SECRET = os.getenv("APP_SECRET")

    URL = "https://api.shadiao.pro/chp"
    TOKEN_URL = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APPID}&secret={SECRET}"
    PUSH_URL = "https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={}"

    def __init__(self):
        pass

    def get_token(self) -> str:
        res = requests.get(self.TOKEN_URL)
        logger.info(f"token res:[{res.text}]")
        token_resp = res.json()
        return token_resp['access_token']

    def push(self, open_id: str, template_id: str) -> str:
        template_message = self.get_wx_mp_template_message(open_id, template_id)

        template_message['data']['love'] = {
            'value': str(self.get_love_day()),
            'color': '#FF1493'
        }
        template_message['data']['word'] = {
            'value': self.get_word(),
            'color': '#FF6347'
        }

        return self.send_message(template_message)

    def push_with_context(self, open_id: str, template_id: str, context: str) -> str:
        template_message = self.get_wx_mp_template_message(open_id, template_id)
        template_message['url'] = "http://101.43.138.173:8090/"

        template_message['data']['context'] = {
            'value': context,
            'color': '#FF6347'
        }

        return self.send_message(template_message)

    def get_wx_mp_template_message(self, open_id: str, template_id: str) -> Dict[str, Any]:
        return {
            'touser': open_id,
            'template_id': template_id,
            'data': {}
        }

    def send_message(self, template_message: Dict[str, Any]) -> str:
        try:
            logger.info(json.dumps(template_message, ensure_ascii=False))
            token = self.get_token()
            url = self.PUSH_URL.format(token)
            req_body = json.dumps(template_message, ensure_ascii=False)
            logger.info(req_body)
            response = requests.post(url, data=req_body.encode('utf-8'),
                                     headers={'Content-Type': 'application/json'})
            logger.info(response.text)
            result = response.json()
            return result.get('msgid', '')
        except Exception as e:
            logger.info(f"推送失败：{str(e)}")
            return str(e)

    def send_template_msg(self, open_id: str, template_id: str) -> str:
        token = self.get_token()
        template_message = self.build_template_req(open_id, template_id)
        return self.send_message_with_token(template_message, token)

    def build_template_req(self, open_id: str, template_id: str) -> Dict[str, Any]:
        weather = self.get_weather()
        return {
            'touser': open_id,
            'template_id': template_id,
            'data': {
                'NOW': {
                    'value': weather[0],
                    'color': '#B462CC'
                },
                'WHETHER': {
                    'value': weather[1],
                    'color': '#B462CC'
                },
                'LOVE': {
                    'value': str(self.get_love_day()),
                    'color': '#FF1493'
                },
                'WORD': {
                    'value': self.get_word(),
                    'color': '#FF6347'
                }
            },
            'topcolor': '#FF0000'
        }

    def send_message_with_token(self, template_message: Dict[str, Any], token: str) -> str:
        logger.info(str(template_message))
        try:
            url = self.PUSH_URL.format(token)
            req_body = json.dumps(template_message, ensure_ascii=False)
            response = requests.post(url, data=req_body.encode('utf-8'),
                                     headers={'Content-Type': 'application/json'})
            logger.info(response.text)
            result = response.json()
            return result.get('msgid', '')
        except Exception as e:
            logger.info(f"推送失败：{str(e)}")
            return str(e)

    def get_word(self) -> str:
        while True:
            s = requests.get(self.URL).text
            data = json.loads(s)
            text = data['data']['text']
            if len(text) <= 20:
                return text
            time.sleep(0.5)

    def get_love_day(self) -> int:
        begin = datetime.strptime("2020-12-20 00:00:00", "%Y-%m-%d %H:%M:%S")
        now = datetime.now()
        day = (now - begin).days
        return day

    def get_weather(self) -> list:
        weather = [None, None]
        try:
            url = "http://t.weather.itboy.net/api/weather/city/101010100"
            response = requests.get(url)
            str_data = response.text
            logger.info(f"getWeather res:{str_data}")
            weather_res = json.loads(str_data)
            forecast = weather_res['data']['forecast'][0]
            split = forecast['ymd'].split('-')
            weather[0] = f"{split[0]}年{split[1]}月{split[2]}日 {forecast['week']}"
            weather[1] = f"{forecast['type']} {forecast['low'].split(' ')[1]}-{forecast['high'].split(' ')[1]} {forecast['notice']}"
        except Exception as exp:
            logger.info(str(exp))
        return weather


if __name__ == "__main__":
    push_service = PushService()

    open_id_li = "od9mK5qoUavbN10xDYBqYZ3Iv_xE"
    open_id_qi = "od9mK5mStJ1R5feTOfGnIyLEEyis"
    template_id = "Z3CJWLQA2qELwH3udOQdN2NA9f9eU-yoQJGpJORaxAU"

    result_li = push_service.send_template_msg(open_id_li, template_id)
    print(f"发送结果: {result_li}")

    result_qi = push_service.send_template_msg(open_id_qi, template_id)
    print(f"发送结果: {result_qi}")
