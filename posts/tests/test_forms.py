import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post, Comment

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.group = Group.objects.create(
            title='New group',
            slug='test-slug'
        )
        cls.post = Post.objects.create(
            text='Test text',
            author=cls.user,
            group=PostsFormTest.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='authorized')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(PostsFormTest.user)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_create_post(self):
        post_count = Post.objects.count()

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
        form_data = {
            'group': PostsFormTest.group.id,
            'text': 'Test text',
            'image': uploaded_image,
        }

        response = self.authorized_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('index'))
        self.assertEqual(Post.objects.count(), post_count + 1)

        last_post = Post.objects.first()
        self.assertEqual(last_post.group, PostsFormTest.group)
        self.assertEqual(last_post.text, form_data['text'])
        self.assertEqual(last_post.author, self.user)

    def test_cant_create_post_guest_client(self):
        post_count = Post.objects.count()
        form_data = {
            'group': PostsFormTest.group.id,
            'text': 'Test text',
        }

        response = self.guest_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'login') + '?next=' + reverse('new_post')
        )
        self.assertEqual(Post.objects.count(), post_count)

    def test_edit_post(self):
        form_data = {
            'group': PostsFormTest.group.id,
            'text': 'Changed text',
        }
        response = self.author_client.post(
            reverse('post_edit', kwargs={
                'username': PostsFormTest.post.author,
                'post_id': PostsFormTest.post.id
            }), data=form_data, follow=True
        )
        self.assertRedirects(response, reverse('post', kwargs={
            'username': PostsFormTest.post.author,
            'post_id': PostsFormTest.post.id,
        }))
        last_post = Post.objects.first()
        self.assertEqual(last_post.text, form_data['text'])
        self.assertEqual(last_post.group.id, form_data['group'])
        self.assertEqual(last_post.author, PostsFormTest.post.author)

    def test_comment_authorized(self):
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Nice!',
        }
        response = self.author_client.post(
            reverse('add_comment', kwargs={
                'username': PostsFormTest.post.author,
                'post_id': PostsFormTest.post.id,
            }), data=form_data, follow=True
        )
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertRedirects(response, reverse('post', kwargs={
            'username': PostsFormTest.post.author,
            'post_id': PostsFormTest.post.id,
        }))
        last_comment = Comment.objects.first()
        self.assertEqual(last_comment.text, form_data['text'])
        self.assertEqual(last_comment.author, PostsFormTest.user)
        self.assertEqual(last_comment.post, PostsFormTest.post)

    def test_cant_comment_unauthorized(self):
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Nice!',
        }

        self.guest_client.post(reverse('add_comment', kwargs={
            'username': PostsFormTest.post.author,
            'post_id': PostsFormTest.post.id,
        }), data=form_data, follow=True
        )
        self.assertEqual(Comment.objects.count(), comment_count)
