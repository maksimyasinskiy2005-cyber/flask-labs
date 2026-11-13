import os
import logging
from flask import Flask, render_template, redirect, url_for, flash, request
from forms import ContactForm
from products.routes import products_bp, get_db
from tinydb import Query

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-key-ukraine-2026'

# Створення необхідних директорій
os.makedirs('logs', exist_ok=True)
os.makedirs('data', exist_ok=True)

# Налаштування логування контактної форми
logger = logging.getLogger('contact_logger')
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler('logs/contact.log', encoding='utf-8')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
if not logger.handlers:
    logger.addHandler(file_handler)

# Реєстрація блюпринта продуктів
app.register_blueprint(products_bp)

# Головна сторінка
@app.route('/')
def index():
    return redirect(url_for('products.list_products'))

# Контактна форма
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        try:
            log_entry = (
                f"Name: {form.name.data} | Email: {form.email.data} | "
                f"Phone: {form.phone.data} | Subject: {form.subject.data} | "
                f"Message: {form.message.data}"
            )
            logger.info(log_entry)
            flash("🇺🇦 Дякуємо! Ваше повідомлення успішно надіслано та занесено в журнал.", "success")
            return redirect(url_for('contact'))
        except Exception as e:
            logger.error(f"Помилка під час запису форми: {e}")
            flash("Виникла помилка під час обробки вашого запиту.", "danger")
            return redirect(url_for('contact'))

    return render_template('contact.html', form=form)

# Вкладка Адміністратора (Центр керування)
@app.route('/admin', methods=['GET'])
def admin_dashboard():
    db = get_db()
    products = db.all()
    
    # Статистика
    total_products = len(products)
    total_quantity = sum(p.get('quantity', 0) for p in products)
    total_value = sum(p.get('price', 0) * p.get('quantity', 0) for p in products)
    
    # Зчитування логів контактної форми
    log_file_path = 'logs/contact.log'
    logs_data = []
    if os.path.exists(log_file_path):
        with open(log_file_path, 'r', encoding='utf-8') as f:
            logs_data = [line.strip() for line in f.readlines() if line.strip()]
            logs_data.reverse()  # Нові логи зверху

    return render_template(
        'admin/dashboard.html',
        products=products,
        total_products=total_products,
        total_quantity=total_quantity,
        total_value=total_value,
        logs=logs_data
    )

# Очищення логів з панелі адміна
@app.route('/admin/logs/clear', methods=['POST'])
def clear_logs():
    log_file_path = 'logs/contact.log'
    if os.path.exists(log_file_path):
        open(log_file_path, 'w', encoding='utf-8').close()
        flash("Журнал повідомлень успішно очищено!", "info")
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
