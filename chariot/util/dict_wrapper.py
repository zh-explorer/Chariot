# from ruamel import yaml
import io
from .context import Context


class DictWrapper(object):
    def __init__(self, dict_data=None):
        self_dict = {}
        if dict_data is not None:
            assert isinstance(dict_data, dict)
            self_dict = self.__dict_wrapper(dict_data)
        super.__setattr__(self, "self_dict", self_dict)
        # self.self_dict = {}

    def __get_list(self, l):
        ll = list()
        for i in l:
            if isinstance(i, DictWrapper):
                ll.append(i.get_dict())
            elif isinstance(i, list):
                ll.append(self.__get_list(i))
            else:
                ll.append(i)
        return ll

    def get_dict(self):
        d = dict()
        for key, value in self.self_dict.items():
            if isinstance(value, DictWrapper):
                value = value.get_dict()
            elif isinstance(value, list):
                value = self.__get_list(value)
            d[key] = value
        return d

    def __getitem__(self, item):
        return self.__getattr__(item)

    def __getattr__(self, item):
        if item not in self.self_dict:
            Context.logger.debug(f"key {item} is not exist, return a None")
            return None
        return self.self_dict[item]

    def __setitem__(self, key, value):
        self.__setattr__(key, value)

    def __setattr__(self, key, value):
        if isinstance(value, dict):
            value = self.__dict_wrapper(value)
        elif isinstance(value, list):
            value = self.__list_wrapper(value)
        self.self_dict[key] = value

    def __delitem__(self, key):
        self.__delattr__(key)

    def __delattr__(self, item):
        del self.self_dict[item]

    def __str__(self):
        return str(self.self_dict)

    def __repr__(self):
        return repr(self.self_dict)

    def __iter__(self):
        return iter(self.self_dict)

    def __dict_wrapper(self, dict_data):
        for key, value in dict_data.items():
            if isinstance(value, dict):
                dict_data[key] = DictWrapper(value)
            elif isinstance(value, list):
                dict_data[key] = self.__list_wrapper(value)
        return dict_data

    def __list_wrapper(self, list_data):
        i = 0
        while i < len(list_data):
            if isinstance(list_data[i], dict):
                list_data[i] = DictWrapper(list_data[i])
            elif isinstance(list_data[i], list):
                list_data[i] = self.__list_wrapper(list_data[i])
            i += 1
        return list_data
