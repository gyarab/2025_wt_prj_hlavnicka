from django.test import TestCase, Client
from django.contrib.auth.models import User
import json
from .models import Prvek

class NinjaAPITestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='api_user', password='password123')
        self.client = Client()
        self.client.login(username='api_user', password='password123')
        
        self.prvek = Prvek.objects.create(
            nazev="Testovací prvek",
            obsah="Obsah testovacího prvku",
            vlastnik=self.user
        )

    def test_list_prvky(self):
        response = self.client.get('/api/prvek/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertTrue(any(p['nazev'] == "Testovací prvek" for p in data))

    def test_get_prvek_detail(self):
        response = self.client.get(f'/api/prvek/{self.prvek.id}/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['nazev'], "Testovací prvek")

    def test_create_prvek(self):
        payload = {
            "nazev": "Nový API prvek",
            "obsah": "Tento prvek byl vytvořen přes API"
        }
        response = self.client.post(
            '/api/prvek/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['nazev'], "Nový API prvek")
        self.assertTrue(Prvek.objects.filter(nazev="Nový API prvek").exists())

    def test_update_prvek_put(self):
        payload = {
            "nazev": "Upravený název",
            "obsah": "Upravený obsah"
        }
        response = self.client.put(
            f'/api/prvek/{self.prvek.id}/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.prvek.refresh_from_db()
        self.assertEqual(self.prvek.nazev, "Upravený název")
        self.assertEqual(self.prvek.obsah, "Upravený obsah")

    def test_create_seznam_bonus(self):
        payload = {
            "nazev": "Můj nový seznam",
            "popis": "Popis seznamu"
        }
        response = self.client.post(
            '/api/seznam/',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['nazev'], "Můj nový seznam")
