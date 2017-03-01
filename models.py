from sqlalchemy import Column, ForeignKey, Integer, String, Text, Float, TIMESTAMP, Boolean, LargeBinary
from sqlalchemy.orm import relationship, deferred
from database import Base, db_session

class Compiler(Base):
    __tablename__ = 'compilers'
    id = Column(Integer, primary_key=True)
    student = Column(String, nullable=False)
    repo_url = Column(String, nullable=False)
    latest_version_id = Column(Integer, ForeignKey('versions.id'))

class Version(Base):
    __tablename__ = 'versions'
    id = Column(Integer, primary_key=True)
    compiler_id = Column(Integer, ForeignKey('compilers.id'), nullable=False)
    sha = Column(String, nullable=False)
    message = Column(String)
    committed_at = Column(TIMESTAMP)
    phase = Column(String, nullable=False)
    status = Column(String, nullable=False)
    builder = Column(String)

class BuildLog(Base):
    __tablename__ = 'build_logs'
    id = Column(Integer, primary_key=True)
    version_id = Column(Integer, ForeignKey('versions.id'), nullable=False)
    build_time = Column(Float)
    created_at = Column(TIMESTAMP, nullable=False)
    builder = Column(String)

class Testcase(Base):
    __tablename__ = 'testcases'
    id = Column(Integer, primary_key=True)
    enabled = Column(Boolean, nullable=False)
    phase = Column(String, nullable=False)
    is_public = Column(Boolean, nullable=False)
    timeout = Column(Float, nullable=False)
    comment = Column(Text, nullable=False)
    content = deferred(Column(Text, nullable=False))
    cnt_run = Column(Integer, nullable=False)
    cnt_hack = Column(Integer, nullable=False)

class TestRun(Base):
    __tablename__ = 'testruns'
    id = Column(Integer, primary_key=True)
    version_id = Column(Integer, ForeignKey('versions.id'), nullable=False)
    testcase_id = Column(Integer, ForeignKey('testcases.id'), nullable=False)
    phase = Column(String, nullable=False)
    status = Column(String, nullable=False)
    created_at = Column(TIMESTAMP, nullable=False)
    running_time = Column(Float)
    compile_time = Column(Float)
    dispatched_to = Column(String)
    dispatched_at = Column(TIMESTAMP)
    finished_at = Column(TIMESTAMP)
