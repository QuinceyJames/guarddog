from typing import TypeVar, Iterable, Iterator, Any, Collection, Sequence

_T = TypeVar('_T')


def filter_if_present(items: Iterable[_T], haystack: Collection[Any] | Any, key=None) -> Iterator[_T]:
    for item in items:
        try:
            needle = key(item)
        except TypeError:  # key is not a function
            needle = item

        try:
            if len(haystack) == 0 or needle in haystack:
                yield item
        except TypeError:  # haystack is not iterable
            if haystack is None or needle == haystack:
                yield item
            elif type(haystack) == bool and bool(needle) == haystack:
                yield item


def filter_by_attributes(objs: Iterable[_T], **filters) -> Sequence[_T]:
    objs_to_return = list(objs)

    for attribute_name, value_to_find in filters.items():
        objs_to_return = list(filter_if_present(
            items=objs_to_return,
            haystack=value_to_find,
            key=lambda obj: getattr(obj, attribute_name)
        ))

    return objs_to_return
