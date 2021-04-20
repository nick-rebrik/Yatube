import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Group, Post, Follow
from yatube.settings import POST_ON_PAGE


User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        user = User.objects.create_user(username='user')

        image = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded_image = SimpleUploadedFile(
            name='image.gif',
            content=image,
            content_type='image/gif'
        )

        cls.group = Group.objects.create(
            title='Test case',
            slug='test-slug',
            description='test text'
        )
        cls.post = Post.objects.create(
            text='test',
            author=user,
            group=cls.group,
            image=uploaded_image
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='test_user')
        self.user_unfoloowed = User.objects.create_user(username='unfollowed')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(PostsViewsTests.post.author)
        self.authorized_unfoloowed = Client()
        self.authorized_unfoloowed.force_login(self.user_unfoloowed)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def context_check(self, post):
        self.assertEqual(post.text, PostsViewsTests.post.text)
        self.assertEqual(post.group, PostsViewsTests.post.group)
        self.assertEqual(post.author, PostsViewsTests.post.author)
        self.assertEqual(post.image, PostsViewsTests.post.image)

    def test_shows_correct_template(self):
        self.template_url_name = {
            'index.html': reverse('index'),
            'group.html': reverse('group', kwargs={
                'slug': PostsViewsTests.group.slug
            }),
            'new_post.html': reverse('new_post'),
        }
        for template, reverse_name in self.template_url_name.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_correct_fields_form_new_post(self):
        response = self.authorized_client.get(reverse('new_post'))
        form_fields = {
            'group': forms.ModelChoiceField,
            'text': forms.CharField,
        }

        for field, expected in form_fields.items():
            form_field = response.context['form'].fields[field]
            self.assertIsInstance(form_field, expected)

    def test_context_index_page(self):
        response = self.authorized_client.get(reverse('index'))
        self.context_check(response.context['page'][0])

    def test_paginator_index_context(self):
        objects = (Post(
            text=f'Test {n}',
            author=self.user) for n in range(POST_ON_PAGE)
        )
        Post.objects.bulk_create(objects)

        response = self.authorized_client.get(reverse('index'))
        self.assertEqual(len(response.context['page']), POST_ON_PAGE)

    def test_correct_context_group_page(self):
        response = self.authorized_client.get(
            reverse('group', kwargs={'slug': PostsViewsTests.group.slug})
        )
        self.context_check(response.context['page'][0])
        self.assertEqual(
            response.context['group'].title, PostsViewsTests.group.title
        )
        self.assertEqual(
            response.context['group'].slug, PostsViewsTests.group.slug
        )
        self.assertEqual(
            response.context['group'].description,
            PostsViewsTests.group.description
        )

    def test_context_post_edit_page(self):
        response = self.author_client.get(
            reverse('post_edit', kwargs={
                'username': PostsViewsTests.post.author,
                'post_id': PostsViewsTests.post.id,
            })
        )
        self.context_check(response.context['post'])

    def test_correct_fields_form_post_edit(self):
        response = self.author_client.get(reverse('post_edit', kwargs={
            'username': self.post.author,
            'post_id': self.post.id,
        }))
        form_fields = {
            'group': forms.ModelChoiceField,
            'text': forms.CharField,
        }

        for field, expected in form_fields.items():
            form_field = response.context['form'].fields[field]
            self.assertIsInstance(form_field, expected)

    def test_context_profile_page(self):
        response = self.author_client.get(reverse('profile', kwargs={
            'username': self.post.author}))
        self.context_check(response.context['post'])

    def test_context_post_page(self):
        response = self.author_client.get(reverse('post', kwargs={
            'username': self.post.author,
            'post_id': self.post.id,
        }))
        self.context_check(response.context['post'])

    def test_cache_index_page(self):
        response = self.authorized_client.get(reverse('index'))
        Post.objects.create(
            text='cache test',
            author=self.user
        )

        response_after_created = self.authorized_client.get(reverse('index'))
        self.assertEqual(response.content, response_after_created.content)

        cache.clear()
        response_clear_cache = self.authorized_client.get(reverse('index'))
        self.assertNotEqual(
            response_after_created.content, response_clear_cache.content
        )

    def test_authorized_follow(self):
        object_count = Follow.objects.count()
        self.authorized_client.get(reverse('profile_follow', kwargs={
            'username': PostsViewsTests.post.author}
        ))
        self.assertEqual(Follow.objects.count(), object_count + 1)
        last_object = Follow.objects.first()
        self.assertEqual(last_object.user, self.user)
        self.assertEqual(last_object.author, PostsViewsTests.post.author)

    def test_authorized_unfollow(self):
        object_count = Follow.objects.count()
        Follow.objects.create(
            user=self.user,
            author=PostsViewsTests.post.author
        )
        self.authorized_client.get(reverse('profile_unfollow', kwargs={
            'username': PostsViewsTests.post.author}
        ))

        self.assertEqual(Follow.objects.count(), object_count)

    def test_follow_index_context_followed_user(self):
        Follow.objects.create(
            user=self.user,
            author=PostsViewsTests.post.author
        )

        response = self.authorized_client.get(
            reverse('follow_index')
        )
        self.context_check(response.context['page'][0])

    def test_follow_index_context_non_followed_user(self):
        response = self.authorized_unfoloowed.get(
            reverse('follow_index')
        )
        self.assertEqual(len(response.context['page']), 0)
