from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import datetime

from database_setup import Category, Base, Item, User

engine = create_engine('postgresql://catalog:candy2017@localhost/catalog')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


# Create dummy user
User1 = User(name="Robo Barista", email="tinnyTim@udacity.com",
             picture='https://pbs.twimg.com/profile_images/2671170543/18debd694829ed78203a5a36dd364160_400x400.png')
session.add(User1)
session.commit()

# Items for Seeds
seeds_category = Category(name="Seeds")
session.add(seeds_category)
session.commit()

now = datetime.datetime.now()
item1 = Item(user_id=1, title="Marigold", description="Marigold annual seeds",created=now, category=seeds_category)
session.add(item1)
item2 = Item(user_id=1, title="Zinnia", description="Zinnia annual seeds",created=now, category=seeds_category)
session.add(item2)
item3 = Item(user_id=1, title="Pansy", description="Pansy annual seeds",created=now, category=seeds_category)
session.add(item3)
session.commit()

# Items for Vegetable
veg_plants_category = Category(name="Vegetable plants")
session.add(veg_plants_category)
session.commit()

now = datetime.datetime.now()
item1 = Item(user_id=1, title="Tomato", description="Tomato plants",created=now, category=veg_plants_category)
session.add(item1)
item2 = Item(user_id=1, title="Bell Pepper", description="Bell pepper plants",created=now, category=veg_plants_category)
session.add(item2)
item3 = Item(user_id=1, title="Red Leaf Lettuce", description="Red Leaf Lettuce plants",created=now, category=veg_plants_category)
session.add(item3)
session.commit()

# Items for Bushes
bushes_category = Category(name="Bushes")
session.add(bushes_category)
session.commit()

now = datetime.datetime.now()
item1 = Item(user_id=1, title="Flame Azalea", description="Flame azalea plants",created=now, category=bushes_category)
session.add(item1)
item2 = Item(user_id=1, title="Native Azalea", description="Native azalea plants to Georgia",created=now, category=bushes_category)
session.add(item2)
item3 = Item(user_id=1, title="Rose", description="Red rose bush",created=now, category=bushes_category)
session.add(item3)
session.commit()

# Items for Trees
trees_category = Category(name="Trees")
session.add(trees_category)
session.commit()

now = datetime.datetime.now()
item1 = Item(user_id=1, title="Apple", description="Apple trees",created=now, category=trees_category)
session.add(item1)
item2 = Item(user_id=1, title="Pear", description="Pear trees",created=now, category=trees_category)
session.add(item2)
item3 = Item(user_id=1, title="Peach", description="Peach trees",created=now, category=trees_category)
session.add(item3)
session.commit()

print "Added catalog items!"
