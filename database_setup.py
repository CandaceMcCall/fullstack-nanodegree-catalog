from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
 
Base = declarative_base()

class User(Base):
    __tablename__ = 'user'
   
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))

class Category(Base):
    __tablename__ = 'category'
   
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)

    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'name'         : self.name,
           'id'           : self.id
       }
 
class Item(Base):
    __tablename__ = 'item'


    title =Column(String(250), nullable = False)
    id = Column(Integer, primary_key = True)
    description = Column(String(1000))
    created = Column(DateTime)
    category_id = Column(Integer,ForeignKey('category.id'))
    category = relationship(Category)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)


    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'title'         : self.title,
           'description'         : self.description,
           'created'         : self.created,
           'id'         : self.id,
           'category_id'         : self.category_id,
           'user_id'      : self.user_id
       }



#engine = create_engine('sqlite:///catalog.db')
engine = create_engine('postgresql://catalog:candy2017@localhost/catalog')
 

Base.metadata.create_all(engine)
