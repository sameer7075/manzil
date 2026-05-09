from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
import datetime

db = SQLAlchemy()

favorites = db.Table('favorites',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('property_id', db.Integer, db.ForeignKey('property.id'), primary_key=True)
)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default="user")  
    is_suspended = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    favorite_properties = db.relationship('Property', secondary=favorites, backref=db.backref('favorited_by', lazy='dynamic'))

class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=True)
    is_system_conversation = db.Column(db.Boolean, default=False)  
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    buyer = db.relationship('User', foreign_keys=[buyer_id], backref=db.backref('conversations_as_buyer', lazy=True))
    seller = db.relationship('User', foreign_keys=[seller_id], backref=db.backref('conversations_as_seller', lazy=True))
    property = db.relationship('Property', backref=db.backref('conversations', lazy=True))
    messages = db.relationship('Message', backref='conversation', lazy=True, cascade='all, delete-orphan')

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=True)
    attachment = db.Column(db.String(500), nullable=True)
    is_read = db.Column(db.Boolean, default=False)
    is_deleted = db.Column(db.Boolean, default=False)
    is_system_message = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    edited_at = db.Column(db.DateTime, nullable=True)
    sender = db.relationship('User', backref=db.backref('sent_messages', lazy=True))

class Property(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    purpose = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    area = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20), nullable=False)
    bedrooms = db.Column(db.Integer, nullable=False)
    bathrooms = db.Column(db.Integer, nullable=False)
    floor = db.Column(db.Integer, nullable=True)
    furnished_status = db.Column(db.String(50), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    area_name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    landmarks = db.Column(db.String(200), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    description = db.Column(db.Text, nullable=False)
    images = db.Column(db.String(500), nullable=True)
    amenities = db.Column(db.String(300), nullable=True)
    seller_name = db.Column(db.String(100), nullable=False)
    contact_number = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('properties', lazy=True))
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected, published
    rejection_reason = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class PropertyReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    reason = db.Column(db.String(200), nullable=False)
    reported_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_resolved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    property = db.relationship('Property', backref=db.backref('reports', lazy=True))
    reported_by = db.relationship('User', backref=db.backref('reports', lazy=True))