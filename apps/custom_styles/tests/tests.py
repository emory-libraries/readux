# pylint: disable = no-self-use
"""Testcases for CustomStyles"""
import pytest
from django.test import TestCase, RequestFactory
from .factories import StyleFactory
from ..context_processors import add_custom_style
from ..models import Style

pytestmark = pytest.mark.django_db # pylint: disable = invalid-name

class TestCustomStyle(TestCase):
    """Test suite for CustomStyles."""
    def test_for_active_style(self):
        """
        When an inactive style is saved as active. Any styles
        marked active should become inactive.
        """
        style = Style.objects.all().first()
        other_style = StyleFactory.create()
        assert style.active
        assert other_style.active is False
        other_style.active = True
        other_style.save()
        style.refresh_from_db()
        assert style.active is False
        assert other_style.active

    def test_create_style_with_no_styles_existing(self):
        """
        If no style is saved in the database. The first new one
        will be marked as active.
        """
        for style in Style.objects.all():
            style.delete()
        style = StyleFactory.create()
        other_style = StyleFactory.create()
        assert style.active
        assert other_style.active is False

    def test_css_property(self):
        """
        The `css` property should be css based other properties.
        """
        style = Style.objects.all().first()
        assert style.css == ':root{.primary-color:#FFFFFF;}'

    def test_model_string_value(self):
        """
        The str value should start with "Style - " and the objects
        id number.
        """
        style = StyleFactory.create()
        assert str(style) == 'Style - {id}'.format(id=style.id)

    def test_style_context(self):
        """
        The context processor should return a dict with one key `css`
        and the value is the `css` property of the active Style objects.
        """
        StyleFactory.create(primary_color='#00000', active=True)
        style = Style.objects.get(active=True)
        req = RequestFactory()
        context_css = add_custom_style(req)
        assert isinstance(context_css, dict)
        assert context_css['css'] == ':root{.primary-color:#00000;}'
        assert style.css == context_css['css']

    def test_no_style_exists(self):
        """
        If no active style is found, the context dict's css value
        will be an empty string.
        """
        for style in Style.objects.all():
            style.delete()
        req = RequestFactory()
        context_css = add_custom_style(req)
        assert context_css['css'] == ''
