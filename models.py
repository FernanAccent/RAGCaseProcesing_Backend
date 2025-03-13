import uuid
from sqlalchemy import Column, String, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from database import Base

class CaseTypeScenario(Base):
    __tablename__ = "case_type_scenarios"
    
    case_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_type = Column(String)
    prompt_number = Column(Integer)
    prompt_type = Column(String)
    system_prompt = Column(String)
    
    
    def __init__(self, case_type, prompt_number, prompt_type, system_prompt):
        self.case_type = case_type
        self.prompt_number = prompt_number
        self.prompt_type = prompt_type
        self.system_prompt = system_prompt

class CasesCannedResponse(Base):
    __tablename__ = "cases_canned_response"
    
    case_response_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_type = Column(String, nullable=False)
    scenario = Column(String, nullable=False)
    canned_response = Column(Text, nullable=False)
    
    def __init__(self, case_type, scenario, canned_response):
        self.case_type = case_type
        self.scenario = scenario
        self.canned_response = canned_response
