from collections import defaultdict


class KeyedDefaultDict(defaultdict):
    def __init__(self, default_factory):
        super().__init__()
        self.my_factory = default_factory

    def __str__(self):
        return self.__class__.__name__ + '(default=' + self.my_factory + ', ' \
            + '='.join((repr(k), v) for k, v in self.items()) + ')'

    def __missing__(self, key):
        if self.my_factory is None:
            raise KeyError(key)
        ret = self[key] = self.my_factory(key)
        return ret
