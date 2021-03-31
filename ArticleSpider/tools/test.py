# -*- encoding: utf-8 -*-
class SqlConnection(object):
    __instance = None

    def __init__(self):
        self.conn = 1111
        self.cursor = 2222

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super(SqlConnection, cls).__new__(cls)
        return cls.__instance

    def exec(self, sql):
        pass

    def commit_(self):
        pass


a = SqlConnection()
b = SqlConnection()

print(id(a.conn), id(b.conn))
