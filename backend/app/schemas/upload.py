from datetime import datetime
from pydantic import BaseModel


class UploadResponse(BaseModel):
    id: int
    filename: str
    file_type: str
    file_size: int
    uploaded_at: datetime

    model_config = {"from_attributes": True}
