from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Table, Column, Integer, String, func,DATETIME
Base = declarative_base()

class Host(Base):
    __tablename__ = "HAhosts"
    pxname = Column('HaName', String(40), primary_key=True)
    svname = Column('ServerName', String(40), primary_key=True)
    status = Column('Status', String(40))
    scur = Column('CurrentConnections', Integer)
    addr = Column('Address', String(15))
    port = Column('Port', Integer)
    algo = Column('Algoritm', String(20))
    created_date = Column('DateTime', DATETIME(timezone=False), default=func.now())

