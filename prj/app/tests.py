from django.test import TestCase, Client
from django.contrib.auth.models import User
from datetime import datetime, timedelta
import json
from .models import Prvek, Stitek
from .services import extract_smart_dates


class DateParsingTestCase(TestCase):
    """Testy pro parsování datumů a časů pomocí extract_smart_dates."""
    
    def test_parse_tomorrow_czech(self):
        """Test parsování 'zítra' v češtině."""
        result = extract_smart_dates('zítra')
        self.assertTrue(result['success'])
        self.assertIsNotNone(result['start'])
        
    def test_parse_today_czech(self):
        """Test parsování 'dnes' v češtině."""
        result = extract_smart_dates('dnes')
        self.assertTrue(result['success'])
        self.assertIsNotNone(result['start'])
    
    def test_parse_tomorrow_with_time_czech(self):
        """Test parsování 'zítra v 14:30' v češtině."""
        result = extract_smart_dates('zítra v 14:30')
        self.assertTrue(result['success'])
        if result['start']:
            parsed_date = datetime.fromisoformat(result['start'])
            self.assertEqual(parsed_date.hour, 14)
            self.assertEqual(parsed_date.minute, 30)
    
    def test_parse_next_weekday_czech(self):
        """Test parsování 'příští pondělí' v češtině."""
        result = extract_smart_dates('příští pondělí')
        self.assertTrue(result['success'])
        self.assertIsNotNone(result['start'])
    
    def test_parse_czech_date_format(self):
        """Test parsování českého formátu data: 20.5.2026."""
        result = extract_smart_dates('20.5.2026')
        self.assertTrue(result['success'])
        if result['start']:
            parsed_date = datetime.fromisoformat(result['start'])
            self.assertEqual(parsed_date.day, 20)
            self.assertEqual(parsed_date.month, 5)
    
    def test_parse_time_of_day_czech(self):
        """Test parsování časů dne: 'ráno', 'dopoledne'."""
        result = extract_smart_dates('ráno')
        self.assertTrue(result['success'])
        self.assertIsNotNone(result['start'])
    
    def test_parse_range_with_od_do(self):
        """Test parsování rozsahu: 'od 10:00 do 14:00'."""
        result = extract_smart_dates('od 10:00 do 14:00')
        self.assertTrue(result['success'])
        self.assertIsNotNone(result['start'])
    
    def test_parse_holiday_christmas(self):
        """Test parsování svátku: 'Vánoce'."""
        result = extract_smart_dates('Vánoce')
        self.assertTrue(result['success'])
        if result['start']:
            parsed_date = datetime.fromisoformat(result['start'])
            self.assertEqual(parsed_date.month, 12)
            self.assertEqual(parsed_date.day, 24)
    
    def test_parse_empty_text(self):
        """Test pro prázdný text."""
        result = extract_smart_dates('')
        self.assertFalse(result['success'])
    
    def test_parse_returns_iso_format(self):
        """Test že výsledek je v ISO formátu."""
        result = extract_smart_dates('zítra')
        if result['success'] and result['start']:
            # Pokud lze parsovat, je to validní ISO format
            parsed = datetime.fromisoformat(result['start'])
            self.assertIsInstance(parsed, datetime)
    
    def test_parse_afternoon(self):
        """Test parsování 'odpoledne'."""
        result = extract_smart_dates('odpoledne')
        self.assertTrue(result['success'])
    
    def test_parse_evening(self):
        """Test parsování 'večer'."""
        result = extract_smart_dates('večer')
        self.assertTrue(result['success'])




class PrvekModelTestCase(TestCase):
    """Testy pro model Prvek."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_create_prvek(self):
        """Test vytvoření základního prvku."""
        prvek = Prvek.objects.create(
            nazev='Test Prvek',
            obsah='Testovací obsah',
            vlastnik=self.user
        )
        self.assertEqual(prvek.nazev, 'Test Prvek')
        self.assertEqual(prvek.vlastnik, self.user)
        self.assertFalse(prvek.smazano)
        self.assertFalse(prvek.archivovano)
    
    def test_prvek_with_dates(self):
        """Test vytvoření prvku s datumy."""
        start = datetime.now()
        end = start + timedelta(hours=1)
        
        prvek = Prvek.objects.create(
            nazev='Schůzka',
            obsah='Obsah schůzky',
            vlastnik=self.user,
            datum_zacatku=start,
            datum_konce=end
        )
        
        self.assertIsNotNone(prvek.datum_zacatku)
        self.assertIsNotNone(prvek.datum_konce)
        self.assertLess(prvek.datum_zacatku, prvek.datum_konce)
    
    def test_prvek_with_tags(self):
        """Test vytvoření prvku se štítky."""
        stitek = Stitek.objects.create(
            nazev='Důležité',
            barva='#FF0000',
            vlastnik=self.user
        )
        
        prvek = Prvek.objects.create(
            nazev='Prvek se štítkem',
            obsah='Obsah',
            vlastnik=self.user
        )
        prvek.stitky.add(stitek)
        
        self.assertEqual(prvek.stitky.count(), 1)
        self.assertIn(stitek, prvek.stitky.all())
    
    def test_prvek_soft_delete(self):
        """Test měkkého smazání prvku."""
        prvek = Prvek.objects.create(
            nazev='Prvek k smazání',
            obsah='Obsah',
            vlastnik=self.user
        )
        
        prvek.smazano = True
        prvek.save()
        
        self.assertTrue(prvek.smazano)
        # Prvek by měl být filtrován z normálního seznamu
        self.assertEqual(Prvek.objects.filter(smazano=False, vlastnik=self.user).count(), 0)
    
    def test_prvek_string_representation(self):
        """Test string reprezentace prvku."""
        prvek = Prvek.objects.create(
            nazev='Test',
            obsah='Obsah',
            vlastnik=self.user
        )
        expected = f"Test, ({self.user.username})"
        self.assertEqual(str(prvek), expected)


class PrvekFormTestCase(TestCase):
    """Testy pro vytváření prvků s datumy."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_create_prvek_without_dates(self):
        """Test vytvoření prvku bez datumů."""
        self.client.login(username='testuser', password='testpass123')
        # Fetch the form first to get CSRF token
        get_response = self.client.get('/pridat/')
        self.assertEqual(get_response.status_code, 200)
        
        response = self.client.post(
            '/pridat/',
            {
                'nazev': 'Test prvek',
                'obsah': 'Testovací obsah'
            }
        )
        if response.status_code != 302:
            # Debug: print form errors if submission fails
            if 'form' in response.context:
                print("Form errors:", response.context['form'].errors)
        self.assertEqual(response.status_code, 302)
        prvek = Prvek.objects.get(nazev='Test prvek')
        self.assertEqual(prvek.nazev, 'Test prvek')
        self.assertIsNone(prvek.datum_zacatku)
        self.assertIsNone(prvek.datum_konce)
    
    def test_create_prvek_with_start_date(self):
        """Test vytvoření prvku s počátečním datem."""
        self.client.login(username='testuser', password='testpass123')
        get_response = self.client.get('/pridat/')
        self.assertEqual(get_response.status_code, 200)
        
        tomorrow = (datetime.now() + timedelta(days=1)).isoformat()
        
        response = self.client.post(
            '/pridat/',
            {
                'nazev': 'Test s datem',
                'obsah': 'Obsah',
                'datum_zacatku_hidden': tomorrow
            }
        )
        self.assertEqual(response.status_code, 302)
        prvek = Prvek.objects.get(nazev='Test s datem')
        self.assertIsNotNone(prvek.datum_zacatku)
    
    def test_create_prvek_with_both_dates(self):
        """Test vytvoření prvku s počátečním a koncovým datem."""
        self.client.login(username='testuser', password='testpass123')
        get_response = self.client.get('/pridat/')
        self.assertEqual(get_response.status_code, 200)
        
        start = datetime.now() + timedelta(days=1)
        end = start + timedelta(hours=2)
        
        response = self.client.post(
            '/pridat/',
            {
                'nazev': 'Test s oběma datumy',
                'obsah': 'Obsah',
                'datum_zacatku_hidden': start.isoformat(),
                'datum_konce_hidden': end.isoformat()
            }
        )
        self.assertEqual(response.status_code, 302)
        prvek = Prvek.objects.get(nazev='Test s oběma datumy')
        self.assertIsNotNone(prvek.datum_zacatku)
        self.assertIsNotNone(prvek.datum_konce)
    
    def test_create_prvek_unauthorized(self):
        """Test že nepřihlášený uživatel nemůže vytvořit prvek."""
        response = self.client.get('/pridat/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/prihlasit', response.url)


class DetailPrvkuTestCase(TestCase):
    """Testy pro detail prvku."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            password='pass123'
        )
        self.prvek = Prvek.objects.create(
            nazev='Test Prvek',
            obsah='Obsah',
            vlastnik=self.user
        )
    
    def test_view_own_prvek(self):
        """Test zobrazení vlastního prvku."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(f'/prvek/{self.prvek.id}/')
        self.assertEqual(response.status_code, 200)
    
    def test_cannot_view_other_prvek(self):
        """Test že uživatel nemůže vidět prvek jiného uživatele."""
        self.client.login(username='testuser', password='testpass123')
        other_prvek = Prvek.objects.create(
            nazev='Cizí prvek',
            obsah='Obsah',
            vlastnik=self.other_user
        )
        response = self.client.get(f'/prvek/{other_prvek.id}/')
        self.assertEqual(response.status_code, 404)
    
    def test_view_prvek_unauthorized(self):
        """Test že nepřihlášený uživatel musí být přesměrován."""
        response = self.client.get(f'/prvek/{self.prvek.id}/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/prihlasit', response.url)


class HomeViewTestCase(TestCase):
    """Testy pro domovskou stránku."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_home_page_loads(self):
        """Test načtení domovské stránky."""
        response = self.client.get('/home/')
        self.assertEqual(response.status_code, 200)
    
    def test_home_page_with_prvky(self):
        """Test domovské stránky s prvky."""
        self.client.login(username='testuser', password='testpass123')
        
        # Vytvoř pár prvků
        Prvek.objects.create(nazev='Prvek 1', obsah='Obsah 1', vlastnik=self.user)
        Prvek.objects.create(nazev='Prvek 2', obsah='Obsah 2', vlastnik=self.user)
        
        response = self.client.get('/home/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['prvky']), 2)
    
    def test_home_page_filter_by_tag(self):
        """Test filtrování prvků podle štítku."""
        self.client.login(username='testuser', password='testpass123')
        
        stitek = Stitek.objects.create(
            nazev='Test',
            barva='#FF0000',
            vlastnik=self.user
        )
        
        prvek1 = Prvek.objects.create(nazev='Prvek 1', obsah='Obsah 1', vlastnik=self.user)
        prvek2 = Prvek.objects.create(nazev='Prvek 2', obsah='Obsah 2', vlastnik=self.user)
        
        prvek1.stitky.add(stitek)
        
        response = self.client.get(f'/home/?stitek={stitek.id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['prvky']), 1)
    
    def test_home_page_empty_for_new_user(self):
        """Test domovské stránky pro nového uživatele bez prvků."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/home/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['prvky']), 0)


class StitkTestCase(TestCase):
    """Testy pro model Stitek."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_create_stitek(self):
        """Test vytvoření štítku."""
        stitek = Stitek.objects.create(
            nazev='Důležité',
            barva='#FF0000',
            vlastnik=self.user
        )
        self.assertEqual(stitek.nazev, 'Důležité')
        self.assertEqual(stitek.barva, '#FF0000')
    
    def test_stitek_string_representation(self):
        """Test string reprezentace štítku."""
        stitek = Stitek.objects.create(
            nazev='Test',
            barva='#0000FF',
            vlastnik=self.user
        )
        self.assertEqual(str(stitek), 'Test')
    
    def test_stitek_with_special_meaning(self):
        """Test vytvoření štítku se speciálním významem."""
        stitek = Stitek.objects.create(
            nazev='Urgent',
            barva='#FF0000',
            vlastnik=self.user,
            specialni_vyznam='High priority'
        )
        self.assertEqual(stitek.specialni_vyznam, 'High priority')
