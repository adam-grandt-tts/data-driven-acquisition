from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def url_replace(context, **kwargs):
    params = context['request'].GET.copy()
    for k, v in kwargs.items():
        params[str(k)] = v
    return context['request'].path + '?' + params.urlencode()
