import pymongo
import uuid


class MongoConfig:

    @staticmethod
    def get_database():
        mongo_uri = "mongodb://localhost:27017/"
        mongo_database = "test"  # 数据库名
        return pymongo.MongoClient(mongo_uri)[mongo_database]


class StrUtils:

    @staticmethod
    def gen_uuid():
        """
        生成uuid（uuid4是基于随机数的）
        :return: uuid
        """
        return "".join(str(uuid.uuid4()).split("-"))
