from models import Knjige, User, FollowItems
import datetime
from app import db

def update_followers():
    current_time = datetime.datetime.utcnow()
    two_weeks_ago = current_time - datetime.timedelta(weeks=2)
    books = Knjige.query.filter(Knjige.timestamp>two_weeks_ago).all
    users = User.query.all()
    for book in books:
        for user in users:
            if user.follow(book):
                pass



# current_time = datetime.datetime.utcnow()
#
# ten_weeks_ago = current_time - datetime.timedelta(weeks=10)
#
# subjects_within_the_last_ten_weeks = session.query(Subject).filter(
#     Subject.time > ten_weeks_ago).all()
