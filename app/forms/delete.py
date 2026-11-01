from pydantic import BaseModel


class DeleteForm(BaseModel):
    member_id: int
    project_id: int