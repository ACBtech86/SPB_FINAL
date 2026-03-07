from pydantic import BaseModel


class MessageSubmit(BaseModel):
    msg_id: str
    form_data: dict
