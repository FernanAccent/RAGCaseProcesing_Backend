import uuid
from sqlalchemy import Column, String, Integer, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from database import Base
from sqlalchemy.orm import relationship

class CaseTypeResolution(Base):
    __tablename__ = "case_type_resolution"
    
    # Primary key for case_type_resolution
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Case type identifier
    case_type = Column(String(10), unique=True, nullable=False)
    
    # Canned response for the case type
    canned_response = Column(Text, nullable=False)
    
    # Relationship to resolution_steps
    resolution_steps = relationship("ResolutionSteps", backref="case_type_resolution", cascade="all, delete-orphan")
    
    def __init__(self, case_type, canned_response):
        self.case_type = case_type
        self.canned_response = canned_response


class ResolutionSteps(Base):
    __tablename__ = "resolution_steps"
    
    # Primary key for resolution_steps
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key referencing case_type_resolution (case_type)
    case_type = Column(String(10), ForeignKey("case_type_resolution.case_type"), nullable=False)
    
    # Step number to define order of resolution steps
    step_number = Column(Integer, nullable=False)
    
    # Description of the resolution step
    step_description = Column(Text, nullable=False)
    
    def __init__(self, case_type, step_number, step_description):
        self.case_type = case_type
        self.step_number = step_number
        self.step_description = step_description
