import json
import os
from troup.apps import App

__author__ = 'pavle'


class Store:

    def add_app(self, app):
        pass

    def remove_app(self, app_name):
        pass

    def update_app(self, app):
        pass

    def find_app(self, app_name):
        pass

    def search_apps(self, query):
        pass

    def store_settings(self, settings):
        pass

    def get_settings(self):
        pass

    def get_setting(self, setting_name):
        pass

    def set_setting(self, name, value):
        pass


class InMemorySyncedStore(Store):

    APPS_FILE = 'apps.json'
    SETTINGS_FILE = 'settings.json'

    def __init__(self, root_path, apps_file=None, settings_file=None):
        self.root_path = root_path
        self.apps = {}
        self.settings = {}
        self.apps_file = apps_file or InMemorySyncedStore.APPS_FILE
        self.settings_file = settings_file or InMemorySyncedStore.SETTINGS_FILE
        self.__check_storage_files__()
        self.load_from_file()

    def __check_storage_files__(self):
        if not os.path.exists(self.root_path):
            os.makedirs(self.root_path, 0o755)
        self.__check_storage_file__(self.apps_file)
        self.__check_storage_file__(self.settings_file)

    def __check_storage_file__(self, f_path):
        if not self.__exists_and_is_file__(f_path):
            with open(self.__to_path__(f_path), 'w') as file:
                file.write('{}')

    def __exists_and_is_file__(self, path):
        path = self.__to_path__(path)
        return os.path.exists(path) and os.path.isfile(path)

    def __load_apps__(self):
        apps = {}
        apps_json = json.loads(self.__load__(self.__to_path__(self.apps_file)))
        for app_id, app_json in apps_json.items():
            apps[app_id] = self.__get_app__(app_json)
        return apps

    def __get_app__(self, app_json):
        return App(app_json['name'], app_json.get('description'), app_json['command'])

    def __load__settings__(self):
        return json.loads(self.__load__(self.__to_path__(self.apps_file)))

    def __to_path__(self, file_name):
        return os.path.join(self.root_path, file_name)

    def __load__(self, path):
        if os.path.exists(path) and os.path.isfile(path):
            with open(path) as file:
                return file.read()
        raise Exception('Unable to read: %s. File does not exist or is not a file' % path)

    def __store__(self, path, data):
        path = self.__to_path__(path)
        with open(path, 'w') as file:
            file.write(data)

    def load_from_file(self):
        self.apps = self.__load_apps__()
        self.settings = self.__load__settings__()

    def ___store_apps___(self):
        def default_enc(obj):
            return json.dumps(obj.__dict__)

        apps_json = json.dumps(self.apps, default=default_enc)
        self.__store__(self.apps_file, apps_json)

    def __store_settings__(self):
        settings_json = json.dumps(self.settings)
        self.__store__(self.settings_file, settings_json)

    def sync(self):
        self.___store_apps___()
        self.__store_settings__()

    def add_app(self, app):
        self.apps[app.name] = app
        self.___store_apps___()

    def remove_app(self, app_name):
        if self.apps.get(app_name):
            del self.apps[app_name]
            self.___store_apps___()

    def update_app(self, app):
        self.apps[app.name] = app
        self.___store_apps___()

    def find_app(self, app_name):
        return self.apps.get(app_name)

    def search_apps(self, query):
        apps = []
        ql = query.lower()
        for name, app in self.apps.items():
            if ql in name.lower() or (app.description and ql in app.description.lower()):
                apps.append(app)
        return apps

    def store_settings(self, settings):
        self.settings.update(settings)
        self.__store_settings__()

    def get_settings(self):
        return self.settings

    def get_setting(self, setting_name):
        return self.settings.get(setting_name)

    def set_setting(self, name, value):
        self.settings[name] = value
        self.__store_settings__()
