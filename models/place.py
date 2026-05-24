import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, Enum, JSON, DateTime, SmallInteger
from database import Base

class PlaceCategory(enum.Enum):
    gym = "gym"
    park = "park"
    pool = "pool"
    badminton = "badminton"
    tennis = "tennis"
    pickleball = "pickleball"
    hospital = "hospital"
    police = "police"

class Place(Base):
    __tablename__ = "places"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    name_ja = Column(String)
    address = Column(String)
    lat = Column(Float)
    lng = Column(Float)
    category = Column(Enum(PlaceCategory))
    is_indoor = Column(Boolean, default=False)
    has_japanese_support = Column(Boolean, default=False)
    opening_hours = Column(JSON, nullable=True)
    phone = Column(String, nullable=True)
    rating = Column(Float, default=0.0)
    safety_level = Column(SmallInteger, default=2)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
