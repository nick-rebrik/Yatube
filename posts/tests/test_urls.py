from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from http import HTTPStatus
import unittest

from ..models import Group, Post

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        user = User.objects.create_user(username='user')
        cls.group = Group.objects.create(
            title='Test case',
            slug='test-slug',
        )
        cls.post = Post.objects.create(
            text='Create new post',
            group=cls.group,
            author=user,
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='Test_user')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(self.post.author)

        self.templates_urls = {
            'index.html': reverse('index'),
            'group.html': reverse(
                'group', kwargs={'slug': PostsURLTests.group.slug}
            ),
            'new_post.html': reverse('new_post'),
            'profile.html': reverse(
                'profile', kwargs={'username': PostsURLTests.post.author}
            ),
            'post.html': reverse(
                'post', kwargs={
                    'username': PostsURLTests.post.author,
                    'post_id': PostsURLTests.post.id,
                })
        }

    def test_status_web_pages_authorized(self):
        for page in self.templates_urls.values():
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    @unittest.expectedFailure
    def test_status_web_pages_unauthorized(self):
        for page in self.templates_urls.values():
            with self.subTest(page=page):
                response = self.guest_client.get(page)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        for template, url in self.templates_urls.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_status_post_edit_page_unauthorized(self):
        response = self.guest_client.get(reverse('post_edit', kwargs={
            'username': f'{PostsURLTests.post.author}',
            'post_id': f'{PostsURLTests.post.id}'}))
        self.assertRedirects(response, reverse('post', kwargs={
            'username': f'{PostsURLTests.post.author}',
            'post_id': f'{PostsURLTests.post.id}'}))

    def test_status_post_edit_page_authorized(self):
        response = self.authorized_client.get(reverse('post_edit', kwargs={
            'username': f'{PostsURLTests.post.author}',
            'post_id': f'{PostsURLTests.post.id}'}))
        self.assertRedirects(response, reverse('post', kwargs={
            'username': f'{PostsURLTests.post.author}',
            'post_id': f'{PostsURLTests.post.id}'}))

    def test_status_post_edit_page_author(self):
        response = self.author_client.get(reverse('post_edit', kwargs={
            'username': f'{PostsURLTests.post.author}',
            'post_id': f'{PostsURLTests.post.id}'}))
        self.assertEqual(response.status_code, HTTPStatus.OK)
