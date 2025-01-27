from pydantic import BaseModel, Field
from datetime import date
from typing import Optional

class LicenceInfo(BaseModel):
    name: Optional[str] = Field(..., description="Full name of the licence holder")
    licence_number: Optional[str] = Field(..., description="Driving licence number")
    nic_number: Optional[str] = Field(..., description="National Identity Card number")
    address: Optional[str] = Field(..., description="Full residential address")
    date_of_birth: Optional[date] = Field(..., description="Date of birth in YYYY-MM-DD format")
    date_of_issue: Optional[date] = Field(..., description="Licence issue date in YYYY-MM-DD format")
    date_of_expiry: Optional[date] = Field(..., description="Licence expiry date in YYYY-MM-DD format")
    blood_group: Optional[str] = Field(None, description="Blood group if available")