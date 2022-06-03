from pymongo import MongoClient


class Client(MongoClient):

    def __init__(self, **kwargs):
        MongoClient.__init__(self, host=['10.0.2.3:27017'], username="vds_data_versioning", password="data_versioning_password", authSource="videtics")