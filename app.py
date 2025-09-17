import os
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import pandas as pd
from io import BytesIO
from collections import defaultdict

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this in production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///accounting.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Models
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    type = db.Column(db.String(10), nullable=False)  # 'income' or 'expense'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat(),
            'description': self.description,
            'amount': float(self.amount),
            'category': self.category,
            'type': self.type,
            'created_at': self.created_at.isoformat()
        }

# Create database tables
with app.app_context():
    db.create_all()

# Routes
@app.context_processor
def inject_now():
    return {'now': datetime.utcnow().strftime('%Y-%m-%d')}

@app.route('/')
def index():
    transactions = Transaction.query.order_by(Transaction.date.desc()).all()
    balance = sum(t.amount if t.type == 'income' else -t.amount for t in transactions)
    return render_template('index.html', transactions=transactions, balance=balance)

@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    try:
        date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
        description = request.form['description']
        amount = float(request.form['amount'])
        category = request.form['category']
        transaction_type = request.form['type']
        
        transaction = Transaction(
            date=date,
            description=description,
            amount=amount,
            category=category,
            type=transaction_type
        )
        
        db.session.add(transaction)
        db.session.commit()
        flash('Transaction added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding transaction: {str(e)}', 'danger')
    
    return redirect(url_for('index'))

@app.route('/delete_transaction/<int:id>', methods=['POST'])
def delete_transaction(id):
    if request.method == 'POST':
        transaction = Transaction.query.get_or_404(id)
        db.session.delete(transaction)
        db.session.commit()
        flash('Transaction deleted successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/export_excel')
def export_excel():
    transactions = Transaction.query.all()
    data = [{
        'Date': t.date,
        'Description': t.description,
        'Amount': t.amount,
        'Category': t.category,
        'Type': t.type
    } for t in transactions]
    
    df = pd.DataFrame(data)
    output = BytesIO()
    df.to_excel(output, index=False, sheet_name='Transactions')
    output.seek(0)
    
    return send_file(
        output,
        as_attachment=True,
        download_name=f'transactions_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@app.route('/import_excel', methods=['POST'])
def import_excel():
    if 'file' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('index'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for('index'))
    
    if file and file.filename.endswith(('.xlsx', '.xls')):
        try:
            df = pd.read_excel(file)
            required_columns = ['Date', 'Description', 'Amount', 'Category', 'Type']
            
            if not all(col in df.columns for col in required_columns):
                flash('Invalid Excel format. Required columns: Date, Description, Amount, Category, Type', 'danger')
                return redirect(url_for('index'))
            
            for _, row in df.iterrows():
                transaction = Transaction(
                    date=pd.to_datetime(row['Date']).date(),
                    description=row['Description'],
                    amount=float(row['Amount']),
                    category=row['Category'],
                    type=row['Type'].lower()
                )
                db.session.add(transaction)
            
            db.session.commit()
            flash('Transactions imported successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error importing transactions: {str(e)}', 'danger')
    else:
        flash('Invalid file format. Please upload an Excel file (.xlsx or .xls)', 'danger')
    
    return redirect(url_for('index'))

@app.route('/financial-report')
def financial_report():
    # Get date range (last 30 days by default)
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=30)
    
    # Get transactions in the date range
    transactions = Transaction.query.filter(
        Transaction.date.between(start_date, end_date)
    ).order_by(Transaction.date).all()
    
    # Calculate summary statistics
    total_income = sum(t.amount for t in transactions if t.type == 'income')
    total_expenses = sum(t.amount for t in transactions if t.type == 'expense')
    net_flow = total_income - total_expenses
    
    # Group by category
    category_totals = defaultdict(lambda: {'income': 0, 'expense': 0})
    for t in transactions:
        category_totals[t.category][t.type] += t.amount
    
    # Prepare data for charts
    daily_totals = defaultdict(lambda: {'income': 0, 'expense': 0, 'net': 0})
    for t in transactions:
        date_str = t.date.strftime('%Y-%m-%d')
        if t.type == 'income':
            daily_totals[date_str]['income'] += t.amount
            daily_totals[date_str]['net'] += t.amount
        else:
            daily_totals[date_str]['expense'] += t.amount
            daily_totals[date_str]['net'] -= t.amount
    
    # Convert to list of dates for the x-axis
    date_range = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]
    date_labels = [d.strftime('%b %d') for d in date_range]
    
    # Prepare data for the net flow chart
    net_flow_data = [daily_totals[d.strftime('%Y-%m-%d')]['net'] for d in date_range]
    
    return render_template('financial_report.html',
                         start_date=start_date,
                         end_date=end_date,
                         total_income=total_income,
                         total_expenses=total_expenses,
                         net_flow=net_flow,
                         category_totals=dict(category_totals),
                         date_labels=date_labels,
                         net_flow_data=net_flow_data,
                         transactions=transactions)

if __name__ == '__main__':
    app.run(debug=True)
