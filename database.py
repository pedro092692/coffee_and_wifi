from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Boolean, Float, desc, func, ForeignKey
from flask_security import Security, SQLAlchemyUserDatastore, hash_password
from flask_security.models import fsqla_v3 as fsqla
from slugify import slugify
from typing import List
import os


# Create DB
class Base(DeclarativeBase):
    pass


# create extension=
db = SQLAlchemy(model_class=Base)
fsqla.FsModels.set_db_info(db)

#configure tables

class Role(db.Model, fsqla.FsRoleMixin):
    pass


class User(db.Model, fsqla.FsUserMixin):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(250), nullable=False)
    name: Mapped[str] = mapped_column(String(250), nullable=True)
    password: Mapped[str] = mapped_column(String(250), nullable=False)
    fs_uniquifier: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    cafes: Mapped["Cafe"] = relationship(back_populates='author')
    comments: Mapped["Comments"] = relationship(back_populates='comment_author')


class Cafe(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"))
    author: Mapped["User"] = relationship(back_populates='cafes')
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    map_url: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    wifi: Mapped[float] = mapped_column(Boolean, nullable=False)
    power: Mapped[float] = mapped_column(Boolean, nullable=False)
    quiet: Mapped[str] = mapped_column(Boolean, nullable=False)
    coffee: Mapped[float] = mapped_column(Boolean, nullable=False)
    credit_card: Mapped[str] = mapped_column(Boolean, nullable=False)
    food: Mapped[str] = mapped_column(Boolean, nullable=False)
    wifi_rating: Mapped[str] = mapped_column(Integer, nullable=False)
    coffee_rating: Mapped[str] = mapped_column(Integer, nullable=False)
    power_rating: Mapped[str] = mapped_column(Integer, nullable=False)
    open: Mapped[str] = mapped_column(Integer, nullable=False)
    close: Mapped[str] = mapped_column(Integer, nullable=False)
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    slug: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    comments: Mapped[List["Comments"]] = relationship(back_populates='parent_cafe')


class Comments(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"))
    comment_author: Mapped["User"] = relationship(back_populates='comments')
    coffee_id: Mapped[int] = mapped_column(Integer, ForeignKey("cafe.id"))
    comment: Mapped[str] = mapped_column(String(500), nullable=False)
    parent_cafe: Mapped["Cafe"] = relationship(back_populates='comments')


class Database:

    def __init__(self, app):
        self.db = db
        self.app = app

        # setup flask_security
        self.user_datastore = SQLAlchemyUserDatastore(db, User, Role)
        self.app.security = Security(self.app, self.user_datastore)

        # Database init
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///coffee_and_wifi.db'
        self.app.config['SECURITY_PASSWORD_SALT'] = os.environ.get('SECRET_KEY')

        self.db.init_app(self.app)

    def create_tables(self):
        with self.app.app_context():
            self.db.create_all()
            if not self.app.security.datastore.find_user(email=os.environ.get('EMAIL_FOR_LOGIN')):
                self.app.security.datastore.create_user(
                    email=os.environ.get('EMAIL_FOR_LOGIN'),
                    password=hash_password(os.environ.get('PASSWORD_FOR_LOGIN'))
                )
                self.db.session.commit()

    def add_new_coffee_shop(self, name, address_url, description, stable_wife, power_sockets, quiet, coffee_service,
                            food_service, credit_card, coffee_score, wifi_score,
                            power_sockets_score, open_hour, close_hour, image_url, user_id):

        slug = slugify(name)
        unique_slug = slug
        count = 1

        while Cafe.query.filter_by(slug=unique_slug).first():
            unique_slug = f'{unique_slug}-{count}'
            count += 1

        new_coffee = Cafe(
            name=name,
            map_url=address_url,
            description=description,
            wifi=stable_wife,
            power=power_sockets,
            quiet=quiet,
            coffee=coffee_service,
            credit_card=credit_card,
            food=food_service,
            wifi_rating=wifi_score,
            coffee_rating=coffee_score,
            power_rating=power_sockets_score,
            open=open_hour,
            close=close_hour,
            image_url=image_url,
            slug=unique_slug,
            user_id=user_id
        )

        self.db.session.add(new_coffee)
        self.db.session.commit()

        return new_coffee

    def get_coffee_shop(self, slug):
        coffee_shop = self.db.first_or_404(self.db.select(Cafe).filter_by(slug=slug))
        return coffee_shop

    def get_all_coffee_shop(self):
        coffees = self.db.session.execute(self.db.select(Cafe).order_by(desc(Cafe.id)).limit(6)).scalars().all()
        return coffees

    def best_coffee_shop(self):
        best_coffee = self.db.session.query(
            Cafe,
            func.sum((Cafe.coffee_rating + Cafe.wifi_rating + Cafe.power_rating) / 3).label('Average')
        ).group_by(Cafe.name).order_by(desc('Average')).limit(1).all()
        return best_coffee

    def edit_cafe(self, cafe: Cafe, name, address_url, description, stable_wife, power_sockets, quiet, coffee_service,
                            food_service, credit_card, coffee_score, wifi_score,
                            power_sockets_score, open_hour, close_hour, image_url):
        cafe.name = name
        cafe.map_url = address_url
        cafe.description = description
        cafe.wifi = stable_wife
        cafe.power = power_sockets
        cafe.quiet = quiet
        cafe.coffee = coffee_service
        cafe.food = food_service
        cafe.credit_card = credit_card
        cafe.coffee_rating = coffee_score
        cafe.wifi_rating = wifi_score
        cafe.power_rating = power_sockets_score
        cafe.open = open_hour
        cafe.close = close_hour
        cafe.image_url = image_url

        self.db.session.commit()

    def delete_coffe(self, cafe: Cafe):
        self.db.session.delete(cafe)
        self.db.session.commit()

    def add_comment(self, user_id, cafe_id, comment):
        new_comment = Comments(
            user_id=user_id,
            coffee_id=cafe_id,
            comment=comment
        )

        self.db.session.add(new_comment)
        self.db.session.commit()

    def update_comment(self, comment_obj: Comments, comment):
        comment_obj.comment = comment
        self.db.session.commit()

    def delete_comment(self, comment_id):
        comment = self.db.get_or_404(Comments, comment_id)
        self.db.session.delete(comment)
        self.db.session.commit()


    def coffee_number(self):
        coffee_numer = self.db.session.query(Cafe.id).count()
        return coffee_numer
