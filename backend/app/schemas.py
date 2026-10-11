from pydantic import BaseModel


class Page(BaseModel):
    page_number: int
    text: str


class UploadResponse(BaseModel):
    filename: str
    page_count: int
    pages: list[Page]
