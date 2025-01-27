from pydantic import BaseModel, Field
from datetime import date
from typing import Optional

class PassportInfo(BaseModel):
    name: Optional[str] = Field(..., description="Full given names of the passport holder")
    surname: Optional[str] = Field(..., description="Surname/family name of the passport holder")
    passport_number: Optional[str] = Field(..., description="Passport number")
    nic_number: Optional[str] = Field(None, description="National Identity Card number if available")
    nationality: Optional[str] = Field(..., description="Country of nationality")
    sex: Optional[str] = Field(..., description="Gender (Male/Female)")
    document_type: Optional[str] = Field(..., description="Type of passport")
    date_of_birth: Optional[date] = Field(..., description="Date of birth in YYYY-MM-DD format")
    date_of_issue: Optional[date] = Field(..., description="Passport issue date in YYYY-MM-DD format")
    date_of_expiry: Optional[date] = Field(..., description="Passport expiry date in YYYY-MM-DD format")
    mrz_code: Optional[str] = Field(None, description="Machine Readable Zone code if visible")