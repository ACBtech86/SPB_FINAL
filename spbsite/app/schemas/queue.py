from pydantic import BaseModel


class QueueProcessRequest(BaseModel):
    processados: str  # Pipe-delimited sequence IDs
