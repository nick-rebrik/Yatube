from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from http import HTTPStatus

User = get_user_model()


class AboutViewsTests(TestCase):

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='test_user')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_status_about_pages(self):
        url_names = {
            'author': 'about:author',
            'tech': 'about:tech',
        }
        for url_name in url_names.values():
            with self.subTest():
                response = self.guest_client.get(reverse(url_name))
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_correct_template_about_pages(self):
        url_names_templates = {
            'about:author': 'about/author.html',
            'about:tech': 'about/tech.html',
        }
        for url_name, template in url_names_templates.items():
            with self.subTest(template=template):
                response = self.guest_client.get(reverse(url_name))
                self.assertTemplateUsed(response, template)
