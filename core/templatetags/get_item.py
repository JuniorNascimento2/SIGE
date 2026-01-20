from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    if not dictionary:
        return None

    # tenta do jeito que veio
    if key in dictionary:
        return dictionary[key]

    # tenta como int
    try:
        ikey = int(key)
        if ikey in dictionary:
            return dictionary[ikey]
    except (TypeError, ValueError):
        pass

    # tenta como string
    return dictionary.get(str(key))
