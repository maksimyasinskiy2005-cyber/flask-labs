import io
import os
import unittest
from app import app
from tinydb import TinyDB
import products.routes


class ProductsTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
        self._dbs = []

        os.makedirs('data', exist_ok=True)
        self.test_db_path = 'data/test_products.json'
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

        def _get_test_db():
            db = TinyDB(self.test_db_path)
            self._dbs.append(db)
            return db

        products.routes.get_db = _get_test_db

    def tearDown(self):
        for db in self._dbs:
            try:
                db.close()
            except Exception:
                pass
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

    def test_create_and_read_product(self):
        """Тест додавання та перегляду товару"""
        response = self.client.post(
            '/product/add',
            data={
                'name': 'Тестовий телефон',
                'content': 'Детальний опис тестового смартфона',
                'price': '19999.99',
                'category': 'electronics',
                'quantity': 5,
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('Тестовий телефон'.encode('utf-8'), response.data)

        response_detail = self.client.get('/product/1')
        self.assertEqual(response_detail.status_code, 200)
        self.assertIn('Детальний опис тестового смартфона'.encode('utf-8'), response_detail.data)

    def test_create_product_with_image(self):
        """Тест додавання товару із завантаженням зображення PNG"""
        fake_png = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
            b'\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89'
            b'\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01'
            b'\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        response = self.client.post(
            '/product/add',
            data={
                'name': 'Ноутбук Pro',
                'content': 'Потужний робочий ноутбук для програмування',
                'price': '45000.50',
                'category': 'electronics',
                'quantity': 3,
                'image': (io.BytesIO(fake_png), 'laptop.png'),
            },
            content_type='multipart/form-data',
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('Ноутбук Pro'.encode('utf-8'), response.data)

        with TinyDB(self.test_db_path) as db:
            item = db.table('products').all()[0]
            self.assertIsNotNone(item.get('image'))
            products.routes.remove_product_image(item.get('image'))

    def test_update_product(self):
        """Тест редагування товару без зміни id та created_at"""
        self.client.post(
            '/product/add',
            data={
                'name': 'Стара назва',
                'content': 'Старий опис товару',
                'price': '100.00',
                'category': 'books',
                'quantity': 2,
            },
        )
        with TinyDB(self.test_db_path) as db:
            original = db.table('products').all()[0]

        response = self.client.post(
            '/product/1/edit',
            data={
                'name': 'Нова назва',
                'content': 'Оновлений опис товару',
                'price': '150.00',
                'category': 'books',
                'quantity': 10,
            },
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('Нова назва'.encode('utf-8'), response.data)

        with TinyDB(self.test_db_path) as db:
            updated = db.table('products').all()[0]
            self.assertEqual(updated['id'], original['id'])
            self.assertEqual(updated['created_at'], original['created_at'])

    def test_delete_product(self):
        """Тест видалення товару"""
        self.client.post(
            '/product/add',
            data={
                'name': 'Товар для видалення',
                'content': 'Короткий опис',
                'price': '50.00',
                'category': 'home',
                'quantity': 1,
            },
        )

        response = self.client.post('/product/1/delete', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        response_not_found = self.client.get('/product/1')
        self.assertEqual(response_not_found.status_code, 404)


if __name__ == '__main__':
    unittest.main()
