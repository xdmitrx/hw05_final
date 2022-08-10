from django.core.paginator import Paginator

from . import constants


def get_page_context(post_list, request):
    """Пагинация для шаблонов страниц."""
    paginator = Paginator(post_list, constants.POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return page_obj
