import os
import uuid
from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, abort
from werkzeug.utils import secure_filename
from tinydb import TinyDB, Query
from forms import ProductForm
from products import products_bp

CATEGORY_LABELS = {
    'electronics': 'Електроніка',
    'books': 'Книги',
    'home': 'Дім і сад',
    'clothing': 'Одяг та взуття',
    'sports': 'Спорт і відпочинок',
}

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


def get_db():
    os.makedirs('data', exist_ok=True)
    return TinyDB('data/products.json')


def get_uploads_dir():
    uploads_dir = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
    os.makedirs(uploads_dir, exist_ok=True)
    return uploads_dir


def is_allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_product_image(file_storage):
    if not file_storage or not file_storage.filename:
        return None

    filename = secure_filename(file_storage.filename)
    if not filename or not is_allowed_file(filename):
        raise ValueError("Непідтримуваний формат файлу. Дозволені лише PNG, JPG, JPEG.")

    file_storage.stream.seek(0, os.SEEK_END)
    file_size = file_storage.stream.tell()
    file_storage.stream.seek(0)
    if file_size > MAX_IMAGE_SIZE_BYTES:
        raise ValueError("Розмір файлу перевищує 5 МБ.")

    ext = filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{uuid.uuid4().hex}.{ext}"
    upload_path = os.path.join(get_uploads_dir(), unique_filename)
    file_storage.save(upload_path)
    return f"uploads/{unique_filename}"


def remove_product_image(relative_path):
    if not relative_path:
        return
    full_path = os.path.join(os.path.dirname(__file__), 'static', relative_path)
    if os.path.exists(full_path) and os.path.isfile(full_path):
        try:
            os.remove(full_path)
        except OSError:
            pass


def get_next_id(table):
    all_items = table.all()
    if not all_items:
        return 1
    return max(item.get('id', 0) for item in all_items) + 1


@products_bp.route('/product')
@products_bp.route('/products')
def list_products():
    with get_db() as db:
        table = db.table('products')
        products = sorted(table.all(), key=lambda x: x.get('id', 0), reverse=True)
    return render_template(
        'products/list.html',
        products=products,
        category_labels=CATEGORY_LABELS,
    )


@products_bp.route('/product/add', methods=['GET', 'POST'])
def add_product():
    form = ProductForm()
    if form.validate_on_submit():
        try:
            image_rel_path = save_product_image(form.image.data)
        except ValueError as err:
            flash(str(err), 'danger')
            return render_template('products/add.html', form=form)

        with get_db() as db:
            table = db.table('products')
            new_id = get_next_id(table)
            created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            product_data = {
                'id': new_id,
                'name': form.name.data.strip(),
                'content': form.content.data.strip(),
                'price': round(float(form.price.data), 2),
                'category': form.category.data,
                'quantity': int(form.quantity.data),
                'image': image_rel_path,
                'created_at': created_at,
            }
            table.insert(product_data)

        flash(f"Товар «{product_data['name']}» успішно додано!", 'success')
        return redirect(url_for('products.list_products'))
    elif request.method == 'POST':
        flash("Не вдалося додати товар. Перевірте коректність заповнення полів.", 'danger')

    return render_template('products/add.html', form=form)


@products_bp.route('/product/<int:id>')
@products_bp.route('/product/<int:id>', endpoint='detail_product')
def product_detail(id):
    with get_db() as db:
        table = db.table('products')
        ProductQuery = Query()
        product = table.get(ProductQuery.id == id)
    if not product:
        abort(404)
    return render_template(
        'products/detail.html',
        product=product,
        item=product,
        category_labels=CATEGORY_LABELS,
    )


@products_bp.route('/product/<int:id>/edit', methods=['GET', 'POST'])
def edit_product(id):
    with get_db() as db:
        table = db.table('products')
        ProductQuery = Query()
        product = table.get(ProductQuery.id == id)
        if not product:
            abort(404)

        form = ProductForm()
        if request.method == 'GET':
            form.name.data = product.get('name')
            form.content.data = product.get('content')
            form.price.data = product.get('price')
            form.category.data = product.get('category')
            form.quantity.data = product.get('quantity')

        if form.validate_on_submit():
            image_rel_path = product.get('image')
            if form.image.data and form.image.data.filename:
                try:
                    new_image_path = save_product_image(form.image.data)
                    remove_product_image(image_rel_path)
                    image_rel_path = new_image_path
                except ValueError as err:
                    flash(str(err), 'danger')
                    return render_template('products/edit.html', form=form, product=product, item=product)

            updated_fields = {
                'name': form.name.data.strip(),
                'content': form.content.data.strip(),
                'price': round(float(form.price.data), 2),
                'category': form.category.data,
                'quantity': int(form.quantity.data),
                'image': image_rel_path,
            }
            table.update(updated_fields, ProductQuery.id == id)
            flash(f"Товар «{updated_fields['name']}» успішно оновлено!", 'success')
            return redirect(url_for('products.product_detail', id=id))
        elif request.method == 'POST':
            flash("Помилка при оновленні товару. Перевірте введені дані.", 'danger')

        return render_template('products/edit.html', form=form, product=product, item=product)


@products_bp.route('/product/<int:id>/delete', methods=['POST'])
def delete_product(id):
    with get_db() as db:
        table = db.table('products')
        ProductQuery = Query()
        product = table.get(ProductQuery.id == id)
        if not product:
            abort(404)

        remove_product_image(product.get('image'))
        table.remove(ProductQuery.id == id)

    flash(f"Товар «{product.get('name')}» успішно видалено.", 'info')
    return redirect(url_for('products.list_products'))
