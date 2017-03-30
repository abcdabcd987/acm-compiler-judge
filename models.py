from sqlalchemy import Index, Column, ForeignKey, Integer, String, Text, Float, TIMESTAMP, Boolean, LargeBinary
from sqlalchemy.orm import relationship, deferred
from database import Base, db_session

class Compiler(Base):
    __tablename__ = 'compilers'
    id = Column(Integer, primary_key=True)
    student = Column(String, nullable=False)
    repo_url = Column(String, nullable=False)
    latest_version_id = Column(Integer, ForeignKey('versions.id'))
    last_check_time = Column(TIMESTAMP)

class Version(Base):
    __tablename__ = 'versions'
    id = Column(Integer, primary_key=True)
    compiler_id = Column(Integer, ForeignKey('compilers.id'), nullable=False, index=True)
    sha = Column(String, nullable=False, index=True)
    phase = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False, index=True)
    message = Column(String)
    committed_at = Column(TIMESTAMP)
    builder = Column(String)
Index('idx_versions_phase_status', Version.phase, Version.status)

class BuildLog(Base):
    __tablename__ = 'build_logs'
    id = Column(Integer, primary_key=True)
    version_id = Column(Integer, ForeignKey('versions.id'), nullable=False, index=True)
    build_time = Column(Float)
    created_at = Column(TIMESTAMP, nullable=False)
    builder = Column(String)

class Testcase(Base):
    __tablename__ = 'testcases'
    id = Column(Integer, primary_key=True)
    enabled = Column(Boolean, nullable=False)
    phase = Column(String, nullable=False)
    is_public = Column(Boolean, nullable=False)
    timeout = Column(Float)
    comment = Column(Text, nullable=False)
    content = deferred(Column(Text, nullable=False))
    cnt_run = Column(Integer, nullable=False)
    cnt_hack = Column(Integer, nullable=False)

class TestRun(Base):
    __tablename__ = 'testruns'
    id = Column(Integer, primary_key=True)
    version_id = Column(Integer, ForeignKey('versions.id'), nullable=False, index=True)
    testcase_id = Column(Integer, ForeignKey('testcases.id'), nullable=False, index=True)
    phase = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False, index=True)
    created_at = Column(TIMESTAMP, nullable=False)
    running_time = Column(Float)
    compile_time = Column(Float)
    dispatched_to = Column(String)
    dispatched_at = Column(TIMESTAMP)
    finished_at = Column(TIMESTAMP)
Index('idx_testruns_versionid_phase', TestRun.version_id, TestRun.phase)
