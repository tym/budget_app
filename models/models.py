# models.py
from sqlalchemy import Column, Integer, String, Float, Boolean, Date, MetaData, Table, ForeignKey, text
from sqlalchemy.orm import relationship
from flask_sqlalchemy import SQLAlchemy
from datetime import date

db = SQLAlchemy()

# Define your models as they are
class Bill(db.Model):
    __tablename__ = 'bills'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    due_day = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(255), nullable=True)


    def __repr__(self):
        return f'<Bill {self.name}>'
    
class Income(db.Model):
    __tablename__ = 'incomes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    frequency = db.Column(db.String(20), nullable=False)
    start_date = db.Column(db.Date, nullable=False, default=date.today)
    day_of_week = db.Column(db.String(10), nullable=True) 


    def __repr__(self):
        return f"<Income {self.name}, Amount: {self.amount}, Frequency: {self.frequency}, Day: {self.day}>"


class Expense(db.Model):
    __tablename__ = 'expenses'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(80), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    category = db.Column(db.String(50), nullable=True)
    cleared = db.Column(db.Boolean, default=False)
    linked_id = db.Column(Integer, nullable=True) 


    def __repr__(self):
        return f"<Expense {self.description}, Amount: {self.amount}, Date: {self.date}>"

# Function to create the budget_view materialized view and setup triggers
