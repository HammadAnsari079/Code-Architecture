from django.test import TestCase, Client
from django.urls import reverse

class AnalyzerTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_index_view(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)

    def test_test_view(self):
        response = self.client.get(reverse('test'))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(str(response.content, encoding='utf8'), {'message': 'Backend is working correctly!'})
