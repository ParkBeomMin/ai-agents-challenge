from pydantic import BaseModel

class InputGuardRailOutput(BaseModel):
    is_off_topic: bool
    reason: str

class ComplaintsOutputGuardRailOutput(BaseModel):
    contains_off_topic: bool
    contains_menu_data: bool
    contains_order_data: bool
    contains_reservation_data: bool
    reason: str

class HandoffData(BaseModel):
    to_agent_name: str
    issue_type: str
    issue_description: str
    reason: str