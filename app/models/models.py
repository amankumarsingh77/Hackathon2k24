from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, handler) -> ObjectId:
        if not isinstance(v, ObjectId):
            if not ObjectId.is_valid(v):
                raise ValueError("Invalid ObjectId")
            v = ObjectId(v)
        return v

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema: Dict[str, Any]) -> Dict[str, Any]:
        field_schema.update(type="string")
        return field_schema

class User(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, json_encoders={ObjectId: str})
    
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    email: EmailStr
    password_hash: str
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Document(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, json_encoders={ObjectId: str})
    
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    filename: str
    content: str
    content_vector: List[float]
    file_type: str
    processed_text: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Report(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, json_encoders={ObjectId: str})
    
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    document_id: PyObjectId
    similarity_scores: Dict[str, float]
    matched_sources: List[Dict]
    overall_score: float
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Cache(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, json_encoders={ObjectId: str})
    
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    key: str
    value: Dict
    created_at: datetime = Field(default_factory=datetime.utcnow) 