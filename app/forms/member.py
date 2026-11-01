from pydantic import BaseModel


class MemberForm(BaseModel):
    member_id: int
    role: str
