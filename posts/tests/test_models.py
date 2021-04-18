from django.contrib.auth import get_user_model
from django.test import TestCase
from posts.models import Post, Group


User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        user = User.objects.create_user(username='TestUser')
        cls.post = Post.objects.create(
            text='Text in post more then 15 simbols',
            author=user
        )

    def test_str_method(self):
        post = PostModelTest.post
        first_15_simbols = post.text[:15]
        self.assertEqual(first_15_simbols, str(post))

    def test_verbose_name(self):
        post = PostModelTest.post
        field_verboses = {
            'text': 'Текст',
            'author': 'Автор',
            'group': 'Группа',
        }
        for field, verbose_name in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, verbose_name)

    def test_help_text(self):
        post = PostModelTest.post
        field_help_text = {
            'group': 'Выберете группу сообщества для публикации.',
            'text': 'Введите текст публикации.'
        }
        for field, help_text in field_help_text.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, help_text)


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Test case',
            slug='test'
        )

    def test_str_method(self):
        group = GroupModelTest.group
        str_method_name = group.title
        self.assertEqual(str_method_name, str(group))

    def test_verbose_name(self):
        group = GroupModelTest.group
        verbose_name = 'Группа'
        self.assertEqual(
            group._meta.get_field('title').verbose_name, verbose_name)
