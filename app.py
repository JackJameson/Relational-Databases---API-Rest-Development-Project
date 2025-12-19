from __future__ import annotations
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column
from sqlalchemy import ForeignKey, Table, Column, String, Integer, Float, DateTime, select
from datetime import datetime, timezone
from marshmallow import ValidationError
from typing import List

# Initialize Flask app
app = Flask(__name__)

# MySQL database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:password@localhost/ecommerce_api'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Creating our Base Model
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy and Marshmallow
db = SQLAlchemy(model_class=Base)
db.init_app(app)
ma = Marshmallow(app)

# Association Table for Many-to-Many relationship
order_product = Table(
    "order_product",
    Base.metadata,
    Column("order_id", ForeignKey("orders.id"), primary_key=True),
    Column("product_id", ForeignKey("products.id"), primary_key=True),
)

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    address: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    orders: Mapped[List["Order"]] = relationship(back_populates="user")

class Order(Base):
    __tablename__ = "orders" 
    id: Mapped[int] = mapped_column(primary_key=True)
    order_date: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped["User"] = relationship(back_populates="orders")
    products: Mapped[List["Product"]] = relationship(secondary=order_product, back_populates="orders")

class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True)
    product_name: Mapped[str] = mapped_column(String(100))
    price: Mapped[float] = mapped_column(Float)
    orders: Mapped[List["Order"]] = relationship(secondary=order_product, back_populates="products")
    
class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        
class OrderSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Order   
        
class ProductSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Product   

user_schema = UserSchema()
users_schema = UserSchema(many=True)
order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)
product_schema = ProductSchema()
products_schema = ProductSchema(many=True)

@app.route('/users', methods=['POST'])
def create_user():
    try:
        user_data = user_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400

    new_user = User(name=user_data['name'], address=user_data['address'], email=user_data['email'])
    db.session.add(new_user)
    db.session.commit()
    return user_schema.jsonify(new_user), 201
    
@app.route('/users', methods=['GET'])
def get_users():
    query = select(User)
    users = db.session.execute(query).scalars().all()
    return users_schema.jsonify(users), 200

@app.route('/users/<int:id>', methods=['GET'])
def get_user(id):
    user = db.session.get(User, id)
    return user_schema.jsonify(user), 200

@app.route('/users/<int:id>', methods=['PUT'])
def update_user(id):
    user = db.session.get(User, id)
    if not user:
        return jsonify({"message": "Invalid user id"}), 400
    try:
        user_data = user_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    user.name = user_data['name']
    user.address = user_data['address']
    user.email = user_data['email']
    db.session.commit()
    return user_schema.jsonify(user), 200

@app.route('/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    user = db.session.get(User, id)
    if not user:
        return jsonify({"message": "Invalid user id"}), 400
    
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": f"succefully deleted user {id}"}), 200


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)