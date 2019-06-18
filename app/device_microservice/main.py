import asyncio
import json
from typing import List, Tuple, Dict, Optional

import databases
import jwt
from aioredis import RedisConnection
from aioredis.abc import AbcChannel
from aioredis.pubsub import Receiver
from backend import BasicAuthBackend
from data_types import Device
from data_types import DeviceRequest
from fastapi import FastAPI, BackgroundTasks
from jwt import DecodeError
from models import devices
from settings import create_redis, DATABASE_URL, SECRET, ALGORITHM
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.requests import Request
from starlette.websockets import WebSocket, WebSocketDisconnect
from starlette.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(CORSMiddleware,
                   allow_origins=['*'],
                   allow_credentials=True,
                   allow_methods=["*"],
                   allow_headers=["*"],
                   )
app.add_middleware(AuthenticationMiddleware, backend=BasicAuthBackend())

pub: RedisConnection = None
sub: RedisConnection = None

# DATABASE_URL = "sqlite:///./test.db"
# DATABASE_URL = "postgresql://user:password@postgresserver/db"

database = databases.Database(DATABASE_URL)
connections: List[Tuple[int, WebSocket, List[Device]]] = []


class DeviceManager:
    def __init__(self, user: int, device_id: int, msg_type: str, extra: Dict):
        self.user = user
        self.device_id = device_id
        self.msg_type = msg_type
        self.extra = extra

    @staticmethod
    def find_connection(user_id: int, device_id: int) -> Optional[WebSocket]:
        for (user, connection, user_devices) in connections:
            if user == user_id:
                for dv in user_devices:
                    if device_id == dv.id:
                        return connection
        return None

    async def receive_update(self):
        connection = DeviceManager.find_connection(self.user, self.device_id)
        if connection is None:
            print(f"Couldn't find connection on this process {connections}")
            return

        if self.msg_type == "show_temp":
            if connection is None:
                raise Exception("Unable to perform update on selected device, it couldn't be found")
            await connection.send_json(
                {"type": self.msg_type, "device": self.device_id, "temp": self.extra["temp"],
                 "photo": self.extra["photo"], "longitude": self.extra["longitude"], "latitude": self.extra["latitude"], "humidity": self.extra["humidity"]})


async def reader(mpsc: Receiver):
    async for channel, msg in mpsc.iter():
        assert isinstance(channel, AbcChannel)

        if channel.name == b"connections":
            try:
                msg = msg.decode("utf-8").replace("'", '"')
                redis_msg = json.loads(msg)

                user = redis_msg["user"]

                if redis_msg.get("device_delta", None) is not None:
                    device_delta = redis_msg["device_delta"]
                    device_id = redis_msg["device"]
                    edit_device(user, device_id, **device_delta)
                    continue

                device = redis_msg["device"]
                device = json.loads(device)
                dv: Device = Device(**device)
                add_device(user, dv)
            except Exception as e:
                print(e, flush=True)

        elif channel.name == b"sous-vide":
            try:
                msg = msg.decode("utf-8").replace("'", '"')
                redis_msg = json.loads(msg)
                user = redis_msg.get("user", None)
                device_id = redis_msg.get("device", None)
                msg_type = redis_msg.get("type", None)

                if user is None or device_id is None or msg_type is None:
                    raise Exception(f"Corrupted response from redis {redis_msg}")
                update_manager = DeviceManager(user, device_id, msg_type, redis_msg)
                await update_manager.receive_update()
            except Exception as e:
                print(e, flush=True)
        print(f"Got {msg} in channel {channel}", flush=True)


@app.on_event("startup")
async def startup():
    await database.connect()
    global sub
    global pub
    sub = await create_redis()
    pub = await create_redis()
    loop = asyncio.get_event_loop()
    mpsc = Receiver(loop=loop)
    await sub.subscribe(mpsc.channel('sous-vide'), mpsc.channel("connections"))
    asyncio.ensure_future(reader(mpsc))


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()
    await sub.close()
    await pub.close()


@app.get("/devices/", response_model=List[Device])
async def read_devices(request: Request):
    query = devices.select().where(devices.c.user == request.user.display_name)
    return await database.fetch_all(query)


@app.post("/devices/", response_model=Device, status_code=201)
async def create_device(request: Request, device: DeviceRequest):
    query = devices.insert().values(description=device.description, status="off",
                                    user=request.user.display_name)
    record_id = await database.execute(query)
    dv: Device = Device(id=record_id, description=device.description, status="off",
                        user=request.user.display_name)
    pub.publish_json('connections', {"user": request.user.display_name, "device": dv.json()})
    return {**dv.dict(), "id": record_id}


def add_device(user_id: int, device: Device) -> bool:
    for (user, connection, user_devices) in connections:
        if user == user_id:
            for dv in user_devices:
                if device.id == dv.id:
                    return False
            user_devices.append(device)
            return True
    return False


def edit_device(user_id: int, device_id: int, **kwargs):
    for (user, connection, user_devices) in connections:
        if user == user_id:
            for i in range(len(user_devices)):
                if device_id == user_devices[i].id:
                    edited_device: Device = user_devices[i].copy(update=kwargs)
                    print(edited_device, flush=True)
                    user_devices[i] = edited_device


def discard_connection(user_id: int):
    for i in range(len(connections)):
        (user, connection, user_devices) = connections[i]
        if user == user_id:
            connections.pop(i)


@app.get("/test")
async def root():
    return {"message": "Hello World"}


@app.websocket_route("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        token = websocket.query_params["token"]
        payload = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
        user_id = payload["user_id"]
        query = devices.select().where(devices.c.user == user_id)
        user_devices: List[Device] = []
        for dv in await database.fetch_all(query):
            user_devices.append(Device(id=dv[0], description=dv[1], status=dv[2], user=dv[3]))
        connections.append((user_id, websocket, user_devices))
        while True:
            await websocket.receive_json()

    except WebSocketDisconnect:
        discard_connection(user_id)
    except DecodeError as e:
        print(e, flush=True)
    except Exception as e:
        print(e, flush=True)
    finally:
        await websocket.close()
