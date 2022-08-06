from django.contrib.auth import get_user_model
from django.test import TestCase, Client


User = get_user_model()


class PostsTests(TestCase):
    def setUp(self):
        self.guest = Client()

    def test_404_uses_custom_template(self):
        """404 использует кастомный шаблон."""
        response = self.guest.get('/notexistingpage/')
        self.assertTemplateUsed(response, 'core/404.html')

    def test_403_uses_custom_template(self):
        """403 использует кастомный шаблон."""
        response = self.guest.get('/permissiondenied/')
        self.assertTemplateUsed(response, 'core/403.html')

    def test_403csrf_uses_custom_template(self):
        """403csrf использует кастомный шаблон."""
        response = self.guest.get('/csrffailure/')
        self.assertTemplateUsed(response, 'core/403csrf.html')

    def test_500_uses_custom_template(self):
        """500 использует кастомный шаблон."""
        response = self.guest.get('/servererror/')
        self.assertTemplateUsed(response, 'core/500.html')
