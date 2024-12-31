from sqlalchemy import Column, Integer, String, Float, Boolean, Date, MetaData, Table, ForeignKey, text
from sqlalchemy.orm import relationship
from flask_sqlalchemy import SQLAlchemy
from datetime import date
import uuid

db = SQLAlchemy()

def generate_unique_id(table_name):
    """Generate a unique ID for each table in the format 'Expense12', 'Bill12', etc."""
    return f"{table_name}{uuid.uuid4().int % 10000}"  # Simplified unique ID generation

class Bill(db.Model):
    __tablename__ = 'bills'
    
    bill_id = db.Column(db.String(20), primary_key=True, default=lambda: generate_unique_id('Bill'))
    name = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    due_day = db.Column(db.Integer, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('bill_category.id'), nullable=True)  # Link to BillCategory

    def __repr__(self):
        return f'<Bill {self.name}>'



class Income(db.Model):
    __tablename__ = 'incomes'
    
    income_id = db.Column(db.String(20), primary_key=True, default=lambda: generate_unique_id('Income'))
    name = db.Column(db.String(80), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    frequency = db.Column(db.String(20), nullable=False)
    start_date = db.Column(db.Date, nullable=False, default=date.today)
    day_of_week = db.Column(db.String(10), nullable=True)
    
    # Foreign key to IncomeCategory
    category_id = db.Column(db.Integer, db.ForeignKey('income_category.id'), nullable=True)

    def __repr__(self):
        return f"<Income {self.name}, Amount: {self.amount}, Frequency: {self.frequency}, Day: {self.day_of_week}>"

class Expense(db.Model):
    __tablename__ = 'expenses'
    
    expense_id = db.Column(db.String(20), primary_key=True, default=lambda: generate_unique_id('Expense'))  
    description = db.Column(db.String(80), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    cleared = db.Column(db.Boolean, default=False)
    linked_id = db.Column(db.String(20), nullable=True)  # Foreign key to Bill or Income (using their new id)

    # Foreign key to ExpenseCategory
    category_id = db.Column(db.Integer, db.ForeignKey('expense_category.id'), nullable=True)

    def __repr__(self):
        return f"<Expense {self.description}, Amount: {self.amount}, Date: {self.date}>"


class ExpenseCategory(db.Model):
    __tablename__ = 'expense_category'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    # Relationship with Expense, referencing category_id in Expense
    expenses = db.relationship('Expense', backref='category', lazy=True)

    def __repr__(self):
        return f'<ExpenseCategory {self.name}>'


class IncomeCategory(db.Model):
    __tablename__ = 'income_category'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    # Define the relationship between IncomeCategory and Income
    incomes = db.relationship('Income', backref='category', lazy=True)

    def __repr__(self):
        return f'<IncomeCategory {self.name}>'

    
class BillCategory(db.Model):
    __tablename__ = 'bill_category'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    # Define the relationship between BillCategory and Bill
    bills = db.relationship('Bill', backref='category', lazy=True)

    def __repr__(self):
        return f'<BillCategory {self.name}>'

