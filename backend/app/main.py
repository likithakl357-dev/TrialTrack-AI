import os,io,csv
from datetime import date,timedelta
from fastapi import FastAPI,Depends,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from .db import Base,engine,get_db
from .models import User,Study,SafetyEvent,AuditLog
from .security import hash_pw,check_pw,token_for,current_user,roles
from pydantic import BaseModel,Field
Base.metadata.create_all(bind=engine)
app=FastAPI(title="TrialTrack AI API",version="1.0.0",description="AIIA CTMS hackathon prototype; synthetic data only")
app.add_middleware(CORSMiddleware,allow_origins=os.getenv("CORS_ORIGINS","http://localhost:5173").split(","),allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
class StudyIn(BaseModel):
 protocol_id:str; title:str; intervention:str="Ayurveda intervention"; status:str="Planning"; pi_name:str="Unassigned"; site_name:str="AIIA"; target_enrollment:int=Field(default=100,ge=1); screened:int=0; enrolled:int=0; randomized:int=0; data_queries:int=0; protocol_deviations:int=0; ethics_status:str="Pending"; ctri_status:str="Pending"; next_milestone:str="Protocol review"; milestone_due:date|None=None
class SafetyIn(BaseModel):
 case_code:str; study_id:int; event_type:str="AE"; seriousness:str="Non-serious"; description:str; status:str="Received"; reported_on:date; due_on:date|None=None
def log(db,u,action,entity,eid,details=""):
 db.add(AuditLog(actor=u.email,action=action,entity=entity,entity_id=str(eid),details=details));db.commit()
def seed(db):
 if not db.query(User).first():
  for name,email,role in [("Demo Administrator","admin@trialtrack.ai","admin"),("Dr. A. Sharma","pi@trialtrack.ai","investigator"),("PV Officer","pv@trialtrack.ai","pharmacovigilance"),("Ethics Reviewer","ethics@trialtrack.ai","ethics"),("Study Coordinator","coordinator@trialtrack.ai","coordinator"),("Study Monitor","monitor@trialtrack.ai","monitor"),("Read-only Regulator","regulator@trialtrack.ai","regulator")]: db.add(User(name=name,email=email,role=role,password_hash=hash_pw("TrialTrack@123")))
  db.commit()
 if not db.query(Study).first():
  t=date.today(); rows=[Study(protocol_id="AIIA-AY-001",title="Ayurvedic Supportive Care: Observational Cohort",intervention="Ayurvedic supportive care",status="Recruiting",pi_name="Dr. A. Sharma",site_name="AIIA Delhi",target_enrollment=120,screened=94,enrolled=76,ethics_status="Approved",ctri_status="Registered",data_queries=4,protocol_deviations=2,next_milestone="Interim monitoring visit",milestone_due=t+timedelta(days=8)),Study(protocol_id="AIIA-AY-002",title="Herbal Formulation Tolerability Study",intervention="Synthetic herbal formulation",status="Active",pi_name="Dr. R. Menon",site_name="AIIA Delhi",target_enrollment=80,screened=45,enrolled=31,randomized=28,ethics_status="Approved",ctri_status="Registered",data_queries=11,protocol_deviations=4,next_milestone="Recruitment review",milestone_due=t-timedelta(days=3)),Study(protocol_id="AIIA-AY-003",title="Yoga and Lifestyle Intervention Pilot",intervention="Yoga and lifestyle",status="Planning",pi_name="Dr. P. Iyer",site_name="Partner Site Chennai",target_enrollment=50,ethics_status="Pending",ctri_status="Pending",next_milestone="Ethics committee review",milestone_due=t+timedelta(days=2)),Study(protocol_id="AIIA-AY-004",title="Ayurveda Follow-up Outcomes Registry",intervention="Usual care follow-up",status="Completed",pi_name="Dr. S. Rao",site_name="AIIA Delhi",target_enrollment=200,screened=210,enrolled=198,ethics_status="Approved",ctri_status="Registered",next_milestone="Close-out report",milestone_due=t+timedelta(days=20))];db.add_all(rows);db.commit();db.refresh(rows[0]);db.refresh(rows[1]);db.add_all([SafetyEvent(case_code="SYN-AE-1001",study_id=rows[0].id,event_type="ADR",seriousness="Non-serious",description="Synthetic example: mild transient nausea during follow-up",status="Under Review",reported_on=t-timedelta(days=2),due_on=t+timedelta(days=5)),SafetyEvent(case_code="SYN-SAE-1002",study_id=rows[1].id,event_type="SAE",seriousness="Serious",description="Synthetic example: serious event requiring investigator assessment",status="Needs Review",reported_on=t,due_on=t+timedelta(days=1))]);db.commit()
with next(get_db()) as db: seed(db)
@app.get("/")
def root(): return {"name":"TrialTrack AI","status":"running","docs":"/docs"}
@app.get("/api/health")
def health(): return {"status":"healthy"}
@app.post("/api/auth/login")
def login(f:OAuth2PasswordRequestForm=Depends(),db:Session=Depends(get_db)):
 u=db.query(User).filter_by(email=f.username,active=True).first()
 if not u or not check_pw(f.password,u.password_hash): raise HTTPException(401,"Incorrect email or password")
 return {"access_token":token_for(u),"token_type":"bearer","user":{"name":u.name,"email":u.email,"role":u.role}}
@app.get("/api/auth/me")
def me(u:User=Depends(current_user)): return {"name":u.name,"email":u.email,"role":u.role}
def study_dict(s): return {k:getattr(s,k) for k in ["id","protocol_id","title","intervention","status","pi_name","site_name","target_enrollment","screened","enrolled","randomized","data_queries","protocol_deviations","ethics_status","ctri_status","next_milestone"]}|{"milestone_due":s.milestone_due.isoformat() if s.milestone_due else None}
def safety_dict(e): return {k:getattr(e,k) for k in ["id","case_code","study_id","event_type","seriousness","description","status"]}|{"reported_on":e.reported_on.isoformat(),"due_on":e.due_on.isoformat() if e.due_on else None}
@app.get("/api/studies")
def studies(db:Session=Depends(get_db),u:User=Depends(current_user)): return [study_dict(s) for s in db.query(Study).order_by(Study.id).all()]
@app.post("/api/studies")
def add_study(p:StudyIn,db:Session=Depends(get_db),u:User=Depends(roles("admin","investigator","coordinator"))):
 if db.query(Study).filter_by(protocol_id=p.protocol_id).first(): raise HTTPException(409,"Protocol ID already exists")
 s=Study(**p.model_dump());db.add(s);db.commit();db.refresh(s);log(db,u,"CREATE","study",s.id,s.protocol_id);return study_dict(s)
@app.patch("/api/studies/{sid}")
def edit_study(sid:int,p:dict,db:Session=Depends(get_db),u:User=Depends(roles("admin","investigator","coordinator","monitor"))):
 s=db.get(Study,sid)
 if not s: raise HTTPException(404,"Study not found")
 allowed=set(StudyIn.model_fields)
 for k,v in p.items():
  if k in allowed: setattr(s,k,v)
 db.commit();log(db,u,"UPDATE","study",sid,','.join(p.keys()));return study_dict(s)
@app.get("/api/safety")
def safety(db:Session=Depends(get_db),u:User=Depends(current_user)): return [safety_dict(e) for e in db.query(SafetyEvent).order_by(SafetyEvent.id.desc()).all()]
@app.post("/api/safety")
def add_safety(p:SafetyIn,db:Session=Depends(get_db),u:User=Depends(roles("admin","pharmacovigilance","investigator"))):
 if not db.get(Study,p.study_id): raise HTTPException(404,"Study not found")
 if db.query(SafetyEvent).filter_by(case_code=p.case_code).first(): raise HTTPException(409,"Case code exists")
 e=SafetyEvent(**p.model_dump());db.add(e);db.commit();db.refresh(e);log(db,u,"CREATE","safety_event",e.id,e.case_code);return safety_dict(e)
@app.patch("/api/safety/{eid}")
def edit_safety(eid:int,p:dict,db:Session=Depends(get_db),u:User=Depends(roles("admin","pharmacovigilance","investigator"))):
 e=db.get(SafetyEvent,eid)
 if not e: raise HTTPException(404,"Safety event not found")
 for k in ["status","description"]:
  if k in p:setattr(e,k,p[k])
 db.commit();log(db,u,"UPDATE","safety_event",eid,str(p));return {"message":"Updated"}
@app.get("/api/dashboard")
def dashboard(db:Session=Depends(get_db),u:User=Depends(current_user)):
 ss=db.query(Study).all();ee=db.query(SafetyEvent).all();target=sum(s.target_enrollment for s in ss);enrolled=sum(s.enrolled for s in ss);return {"total_studies":len(ss),"active_studies":sum(s.status.lower() not in ["completed","closed"] for s in ss),"completed_studies":sum(s.status.lower() in ["completed","closed"] for s in ss),"target_enrollment":target,"enrolled":enrolled,"recruitment_percent":round(enrolled/target*100,1) if target else 0,"pending_ethics":sum(s.ethics_status.lower()!="approved" for s in ss),"pending_ctri":sum(s.ctri_status.lower() not in ["registered","updated"] for s in ss),"open_safety_events":sum(e.status.lower() not in ["closed","resolved"] for e in ee),"open_sae":sum(e.seriousness.lower()=="serious" and e.status.lower() not in ["closed","resolved"] for e in ee),"data_queries":sum(s.data_queries for s in ss),"protocol_deviations":sum(s.protocol_deviations for s in ss)}
@app.get("/api/alerts")
def alerts(db:Session=Depends(get_db),u:User=Depends(current_user)):
 out=[];today=date.today()
 for s in db.query(Study).all():
  if s.ethics_status.lower()!="approved":out.append({"level":"warning","title":"Ethics approval pending","detail":s.protocol_id,"study_id":s.id})
  if s.ctri_status.lower() not in ["registered","updated"]:out.append({"level":"warning","title":"CTRI registration/update pending","detail":s.protocol_id,"study_id":s.id})
  if s.milestone_due and s.milestone_due<today and s.status.lower() not in ["completed","closed"]:out.append({"level":"critical","title":"Milestone overdue","detail":s.protocol_id+" — "+s.next_milestone,"study_id":s.id})
  if s.data_queries>10:out.append({"level":"warning","title":"High open data queries","detail":s.protocol_id+": "+str(s.data_queries),"study_id":s.id})
 for e in db.query(SafetyEvent).all():
  if e.seriousness.lower()=="serious" and e.status.lower() not in ["closed","resolved"]:out.append({"level":"critical","title":"SAE requires human review","detail":e.case_code,"study_id":e.study_id})
 return out
@app.get("/api/trialguard")
def trialguard(db:Session=Depends(get_db),u:User=Depends(current_user)):
 out=[];today=date.today()
 for s in db.query(Study).all():
  score=100;why=[]
  if s.status.lower() not in ["completed","closed"]:
   ratio=min(s.enrolled/s.target_enrollment,1) if s.target_enrollment else 1;score-=round((1-ratio)*25)
   if ratio<.5:why.append("Recruitment below 50% of target")
   if s.ethics_status.lower()!="approved":score-=20;why.append("Ethics approval pending")
   if s.ctri_status.lower() not in ["registered","updated"]:score-=15;why.append("CTRI registration/update pending")
   if s.milestone_due and s.milestone_due<today:score-=15;why.append("Next milestone overdue")
   if s.data_queries>10:score-=10;why.append("More than 10 open data queries")
   if s.protocol_deviations>5:score-=10;why.append("More than 5 protocol deviations")
   sae=db.query(SafetyEvent).filter(SafetyEvent.study_id==s.id,SafetyEvent.seriousness=="Serious",SafetyEvent.status.notin_(["Closed","Resolved"])).count()
   if sae:score-=min(20,sae*10);why.append(f"{sae} serious safety event(s) need review")
  score=max(0,min(100,score));band="Healthy" if score>=80 else "Watch" if score>=60 else "At Risk";actions=[]
  if any("Recruitment" in x for x in why):actions.append("Review recruitment barriers and site enrolment plan.")
  if any("Ethics" in x for x in why):actions.append("Confirm ethics submission and approval status.")
  if any("CTRI" in x for x in why):actions.append("Verify prospective registration and required registry updates.")
  if any("overdue" in x.lower() for x in why):actions.append("Assign an owner and revised date to the overdue milestone.")
  if any("safety event" in x for x in why):actions.append("Escalate the safety case for investigator and PV human review.")
  if not actions:actions=["Continue routine monitoring and keep study records current."]
  out.append({"study_id":s.id,"protocol_id":s.protocol_id,"title":s.title,"score":score,"band":band,"reasons":why,"recommended_actions":actions})
 return out
@app.get("/api/audit")
def audit(db:Session=Depends(get_db),u:User=Depends(roles("admin","monitor","ethics","regulator"))):return [{"id":x.id,"actor":x.actor,"action":x.action,"entity":x.entity,"entity_id":x.entity_id,"details":x.details,"timestamp":x.created_at.isoformat()+"Z"} for x in db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(200).all()]
@app.get("/api/exports/fhir")
def fhir(db:Session=Depends(get_db),u:User=Depends(current_user)):
 return {"resourceType":"Bundle","type":"collection","entry":[{"resource":{"resourceType":"ResearchStudy","id":str(s.id),"identifier":[{"value":s.protocol_id}],"title":s.title,"status":"completed" if s.status.lower() in ["completed","closed"] else "active","description":s.intervention}} for s in db.query(Study).all()],"note":"FHIR R4-oriented starter only; validate profiles and terminology before use."}
@app.get("/api/exports/cdisc")
def cdisc(db:Session=Depends(get_db),u:User=Depends(current_user)):
 buf=io.StringIO();w=csv.DictWriter(buf,fieldnames=["STUDYID","DOMAIN","STATUS","ENROLLED","TARGET","ETHICS","CTRI"]);w.writeheader()
 for s in db.query(Study).all():w.writerow({"STUDYID":s.protocol_id,"DOMAIN":"DS","STATUS":s.status,"ENROLLED":s.enrolled,"TARGET":s.target_enrollment,"ETHICS":s.ethics_status,"CTRI":s.ctri_status})
 return StreamingResponse(iter([buf.getvalue()]),media_type="text/csv",headers={"Content-Disposition":"attachment; filename=trialtrack_cdisc_starter.csv"})
