from pydantic import BaseModel


class Proxy(BaseModel):
    host: str
    port: str
    username: str
    password: str
