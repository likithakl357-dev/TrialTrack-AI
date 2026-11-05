from datetime import datetime,date
from sqlalchemy import String,Integer,Date,DateTime,Text,Boolean,ForeignKey
from sqlalchemy.orm import Mapped,mapped_column,relationship
from .db import Base
class User(Base):
 __tablename__="users"
 id:Mapped[int]=mapped_column(primary_key=True)
 name:Mapped[str]=mapped_column(String(120))
 email:Mapped[str]=mapped_column(String(180),unique=True,index=True)
 password_hash:Mapped[str]=mapped_column(String(255))
 role:Mapped[str]=mapped_column(String(40))
 active:Mapped[bool]=mapped_column(Boolean,default=True)
class Study(Base):
 __tablename__="studies"
 id:Mapped[int]=mapped_column(primary_key=True)
 protocol_id:Mapped[str]=mapped_column(String(50),unique=True,index=True)
 title:Mapped[str]=mapped_column(String(240))
 intervention:Mapped[str]=mapped_column(String(180),default="Ayurveda intervention")
 status:Mapped[str]=mapped_column(String(40),default="Planning")
 pi_name:Mapped[str]=mapped_column(String(120),default="Unassigned")
 site_name:Mapped[str]=mapped_column(String(160),default="AIIA")
 target_enrollment:Mapped[int]=mapped_column(Integer,default=100)
 screened:Mapped[int]=mapped_column(Integer,default=0)
 enrolled:Mapped[int]=mapped_column(Integer,default=0)
 randomized:Mapped[int]=mapped_column(Integer,default=0)
 data_queries:Mapped[int]=mapped_column(Integer,default=0)
 protocol_deviations:Mapped[int]=mapped_column(Integer,default=0)
 ethics_status:Mapped[str]=mapped_column(String(50),default="Pending")
 ctri_status:Mapped[str]=mapped_column(String(50),default="Pending")
 next_milestone:Mapped[str]=mapped_column(String(180),default="Protocol review")
 milestone_due:Mapped[date|None]=mapped_column(Date,nullable=True)
 created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
class SafetyEvent(Base):
 __tablename__="safety_events"
 id:Mapped[int]=mapped_column(primary_key=True)
 case_code:Mapped[str]=mapped_column(String(60),unique=True)
 study_id:Mapped[int]=mapped_column(ForeignKey("studies.id"))
 event_type:Mapped[str]=mapped_column(String(30),default="AE")
 seriousness:Mapped[str]=mapped_column(String(30),default="Non-serious")
 description:Mapped[str]=mapped_column(Text)
 status:Mapped[str]=mapped_column(String(40),default="Received")
 reported_on:Mapped[date]=mapped_column(Date,default=date.today)
 due_on:Mapped[date|None]=mapped_column(Date,nullable=True)
 study=relationship("Study")
class AuditLog(Base):
 __tablename__="audit_logs"
 id:Mapped[int]=mapped_column(primary_key=True)
 actor:Mapped[str]=mapped_column(String(180))
 action:Mapped[str]=mapped_column(String(80))
 entity:Mapped[str]=mapped_column(String(60))
 entity_id:Mapped[str]=mapped_column(String(60))
 details:Mapped[str]=mapped_column(Text,default="")
 created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
