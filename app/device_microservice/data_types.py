from typing import Optional

from pydantic import BaseModel


class Device(BaseModel):
    id: int
    description: str
    status: str


class DeviceRequest(BaseModel):
    description: str
