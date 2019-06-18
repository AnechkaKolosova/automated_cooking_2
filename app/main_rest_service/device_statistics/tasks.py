import json

from background_task import background
from django.contrib.auth.models import User
import redis
import time
import traceback

from device_statistics.models import Metric


def redis_get_device_info():
    r = redis.StrictRedis(host='redis', port=6379)  # Connect to local Redis instance
    try:
        #
        # if r.get("running"):
        #     return
        # else:
        #     r.set("running", "true")
        p = r.pubsub()
        p.subscribe('sous-vide')

        while True:
            message = p.get_message()  # Checks for message
            if message and message['type'] != "subscribe":
                msg = message['data']  # Get data from message
                msg = msg.decode("utf-8").replace("'", '"')
                redis_msg = json.loads(msg)
                print(redis_msg, flush=True)
                msg_type = redis_msg.get("type", None)
                user = redis_msg.get('user', None)
                device = redis_msg.get("device", None)
                if msg_type is not None and msg_type == "show_temp" and user is not None and device is not None:
                    if redis_msg["latitude"] == "" or redis_msg["longitude"] == "":
                        Metric.objects.create(device=device, user_id=user, temp=redis_msg["temp"],
                                              photo=redis_msg["photo"], humidity=redis_msg["humidity"], type=msg_type)

                    else:
                        Metric.objects.create(device=device, user_id=user, temp=redis_msg["temp"],
                                              longitude=redis_msg["longitude"], latitude=redis_msg["latitude"],
                                              photo=redis_msg["photo"], humidity=redis_msg["humidity"], type=msg_type)

            time.sleep(1)

    except Exception as e:
        print(e, flush=True)


@background
def update_stats():
    redis_get_device_info()
