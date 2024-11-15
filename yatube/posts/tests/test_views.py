import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..constants import POSTS_PER_PAGE, POSTS_PER_SECOND_PAGE
from ..models import Follow, Group, Post

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


class PostsViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='test_username')
        cls.group = Group.objects.create(
            title='test title',
            slug='1',
            description='test description',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='test post',
            group=cls.group,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_pages_use_correct_template(self):
        """Проверка шаблона при вызове views через пространство имен."""
        reverse_names_templates = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': f'{self.post.id}'}):
            'posts/create_post.html',
            reverse('posts:profile',
                    kwargs={'username': f'{self.user.username}'}):
            'posts/profile.html',
            reverse('posts:group_list',
                    kwargs={'slug': f'{self.group.slug}'}):
            'posts/group_list.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': f'{self.post.id}'}):
            'posts/post_detail.html',
            reverse('posts:follow_index'): 'posts/follow.html',
        }
        for reverse_name, template in reverse_names_templates.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='test_username')
        cls.group = Group.objects.create(
            title='test title',
            slug='1',
            description='test description',
        )
        cls.group_2 = Group.objects.create(
            title='test title2',
            slug='2',
            description='test description2',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded_img = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='test post',
            group=cls.group,
            image=uploaded_img,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.author, self.post.author)
        self.assertEqual(first_object.group, self.post.group)
        self.assertEqual(first_object.id, self.post.id)
        self.assertEqual(first_object.image, self.post.image)

    def test_group_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:group_list',
                                              kwargs={'slug':
                                                      self.group.slug}))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.author, self.post.author)
        self.assertEqual(first_object.group, self.post.group)
        self.assertEqual(first_object.id, self.post.id)
        self.assertEqual(first_object.image, self.post.image)
        self.assertEqual(response.context['group'].title, self.group.title)
        self.assertEqual(
            response.context['group'].description, self.group.description)
        self.assertEqual(response.context['group'].slug, self.group.slug)

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:profile',
                                              kwargs={'username':
                                                      self.post.author.username
                                                      }))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.group, self.post.group)
        self.assertEqual(first_object.id, self.post.id)
        self.assertEqual(first_object.image, self.post.image)
        self.assertEqual(response.context['author'], self.user)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_detail',
                                              kwargs={'post_id':
                                                      self.post.id}))
        first_object = response.context['post']
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.author, self.post.author)
        self.assertEqual(first_object.group, self.post.group)
        self.assertEqual(first_object.id, self.post.id)
        self.assertEqual(first_object.image, self.post.image)

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.ModelChoiceField,
            'image': forms.ImageField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_edit',
            kwargs={'post_id': f'{self.post.id}'}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.ModelChoiceField,
            'image': forms.ImageField
        }
        self.assertEqual(response.context['post'], self.post)
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_appeared_on_the_wrong_groups_page(self):
        """Пост не улетает в другую группу."""
        group_2 = f'/group/{self.group_2.slug}/'
        response = self.authorized_client.get(group_2)
        self.assertNotIn(self.post, response.context['page_obj'])

    def test_post_appeared_on_the_groups_page(self):
        """Пост улетает в нужную группу."""
        group = f'/group/{self.group.slug}/'
        response = self.authorized_client.get(group)
        self.assertIn(self.post, response.context['page_obj'])

    def test_first_post_appeared_on_the_index_page(self):
        """Пост при создании попадает на 1ю позицию на главной странице."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_post = Post.objects.create(
            author=self.user,
            text='test post',
            group=self.group,
        )
        self.assertEqual(response.context['page_obj'][0],
                         first_post)

    def test_first_post_appeared_on_the_group_page(self):
        """Пост при создании попадает на 1ю позицию на странице группы."""
        first_post = Post.objects.create(
            author=self.user,
            text='test post',
            group=self.group,
        )
        group_page = f'/group/{self.group.slug}/'
        response = self.authorized_client.get(group_page)
        self.assertEqual(response.context['page_obj'][0],
                         first_post)

    def test_first_post_appeared_on_the_profile_page(self):
        """Пост при создании попадает на 1ю позицию на странице профиля."""
        first_post = Post.objects.create(
            author=self.user,
            text='test post',
            group=self.group,
        )
        profile_page = f'/profile/{self.user.username}/'
        response = self.authorized_client.get(profile_page)
        self.assertEqual(response.context['page_obj'][0],
                         first_post)

    def test_index_cache(self):
        """Главная страница кэшируется"""
        response_first = self.authorized_client.get(reverse('posts:index'))
        Post.objects.create(
            author=self.user,
            text='test post',
        )
        response_second = self.authorized_client.get(
            (reverse('posts:index'))
        )
        self.assertEqual(response_first.content,
                         response_second.content)
        cache.clear()
        response_after_clear = self.authorized_client.get(
            reverse('posts:index')
        )
        self.assertNotEqual(response_first.content,
                            response_after_clear.content)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='test_username')
        cls.group = Group.objects.create(
            title='test title',
            slug='1',
            description='test description',
        )
        cls.posts = [Post.objects.create(
            author=cls.user,
            text='test post',
            group=cls.group,
        )
            for i in range(POSTS_PER_PAGE
                           + POSTS_PER_SECOND_PAGE)]

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PaginatorViewsTest.user)

    def test_first_page_contains_ten_records(self):
        """Проверит количество постов на первой странице."""
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']),
                            (POSTS_PER_PAGE)
                         )

    def test_second_page_contains_three_records(self):
        """Проверит количество постов на второй странице."""
        response = self.authorized_client.get(reverse(
            'posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']),
                            (POSTS_PER_SECOND_PAGE)
                         )

    def test_group_page_contains_ten_records(self):
        """Проверит количество постов на странице группы."""
        group_page = f'/group/{self.group.slug}/'
        response = self.authorized_client.get(group_page)
        self.assertEqual(len(response.context['page_obj']),
                            (POSTS_PER_PAGE)
                         )

    def test_second_group_page_contains_three_records(self):
        """Проверит количество постов на 2й странице группы."""
        group_page = f'/group/{self.group.slug}/'
        response = self.authorized_client.get((group_page) + '?page=2')
        self.assertEqual(len(response.context['page_obj']),
                            (POSTS_PER_SECOND_PAGE)
                         )

    def test_profile_page_contains_ten_records(self):
        """Проверит количество постов на странице профиля."""
        profile_page = f'/profile/{self.user.username}/'
        response = self.authorized_client.get(profile_page)
        self.assertEqual(len(response.context['page_obj']),
                            (POSTS_PER_PAGE),
                         )

    def test_second_profile_page_contains_three_records(self):
        """Проверит количество постов на 2й странице профиля."""
        profile_page = f'/profile/{self.user.username}/'
        response = self.authorized_client.get((profile_page) + '?page=2')
        self.assertEqual(len(response.context['page_obj']),
                            (POSTS_PER_SECOND_PAGE),
                         )


class SubscribeViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create(username='Автор')
        cls.user_follower = User.objects.create(username='Подписчик')
        cls.user_no_follow = User.objects.create(username='Не подписчик')
        cls.post = Post.objects.create(
            author=cls.user_author,
            text='test author post',
        )
        cls.post_no_follow = Post.objects.create(
            author=cls.user_no_follow,
            text='test user post',
        )

    def setUp(self):
        self.auth_follower = Client()
        self.auth_follower.force_login(self.user_follower)
        self.auth_no_follow = Client()
        self.auth_no_follow.force_login(self.user_no_follow)

    def test_guest_cant_subscribe(self):
        """Не авторизованный пользователь не может подписаться на автора."""
        follows_count = Follow.objects.count()
        self.client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.user_author.username})
        )
        self.assertEqual(Follow.objects.count(), follows_count)

    def test_user_can_subscribe(self):
        """Авторизованный пользователь может подписаться на автора."""
        follows_count = Follow.objects.count()
        self.auth_follower.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.user_author.username})
        )
        self.assertEqual(Follow.objects.count(), follows_count + 1)
        self.assertTrue(
            Follow.objects.filter(
                user=self.user_follower,
                author=self.user_author
            ).exists()
        )

    def test_user_can_unsubscribe(self):
        """Авторизованный пользователь может отписаться от автора."""
        Follow.objects.create(user=self.user_follower,
                              author=self.user_author)
        self.auth_follower.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.user_author.username})
        )
        self.assertFalse(Follow.objects.filter(
            user=self.user_follower,
            author=self.user_author)
        )

    def test_user_see_who_follows(self):
        """Новый пост доступен для просмотра подписчикам."""
        Follow.objects.create(user=self.user_follower, author=self.user_author)
        response_follower = self.auth_follower.get(
            reverse('posts:follow_index')
        )
        self.assertEqual(response_follower.context['page_obj'][0].text,
                         self.post.text)

    def test_user_dont_see_who_not_follows(self):
        """Новый пост не доступен для просмотра тем, кто не подписан."""
        Follow.objects.create(user=self.user_follower, author=self.user_author)
        response_no_follow_user = self.auth_no_follow.get(
            reverse('posts:follow_index')
        )
        self.assertFalse(response_no_follow_user.context['page_obj'])
