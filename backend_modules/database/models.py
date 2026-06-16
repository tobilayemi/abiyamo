from sqlalchemy import Column, Integer, Float, DateTime, String
from database.db import Base


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True)
    age = Column(Integer)
    parity = Column(Integer)
    systolic_bp = Column(Integer)
    diastolic_bp = Column(Integer)
    hemoglobin = Column(Float)
    gestational_age = Column(Integer)
    previous_cs = Column(Integer)
    hiv_status = Column(Integer)
    risk_probability = Column(Float)
    risk_label = Column(Integer)
    created_at = Column(DateTime)


class MotherBabyRecord(Base):
    __tablename__ = "mother_baby_records"

    id = Column(Integer, primary_key=True, index=True)
    age = Column(Integer)
    parity = Column(Integer)
    maternal_risk_probability = Column(Float)
    maternal_risk_label = Column(Integer)
    birth_weight = Column(Float)
    apgar_score = Column(Integer)
    newborn_risk_label = Column(Integer)
    created_at = Column(DateTime)