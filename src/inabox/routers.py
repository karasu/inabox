""" Handle database routing ldap/postgres """

class AuthRouter:
    """
    A router to control all database operations on models in the
    auth and contenttypes applications.
    """

    route_app_labels = {"auth", "contenttypes"}

    def db_for_read(self, model, **_hints):
        """
        Attempts to read auth and contenttypes models go to auth_db.
        """
        if model._meta.app_label in self.route_app_labels:
            return "ldap"
        return None

    def db_for_write(self, model, **_hints):
        """
        Attempts to write auth and contenttypes models go to auth_db.
        """
        if model._meta.app_label in self.route_app_labels:
            return "ldap"
        return None

    def allow_relation(self, obj1, obj2, **_hints):
        """
        Allow relations if a model in the auth or contenttypes apps is
        involved.
        """
        if (
            obj1._meta.app_label in self.route_app_labels
            or obj2._meta.app_label in self.route_app_labels
        ):
            return True
        return None

    def allow_migrate(self, db, app_label, _model_name=None, **_hints):
        """
        Make sure the auth and contenttypes apps only appear in the
        'auth_db' database.
        """
        if app_label in self.route_app_labels:
            return db == "ldap"
        return None

class DefaultRouter:
    """ Router that sends all non auth related to the defaultconfiguration """

    def db_for_read(self, _model, **_hints):
        """ Reads go to default database (non ldap) """
        return "default"

    def db_for_write(self, _model, **_hints):
        """ Writes go to default database (non ldap) """
        return "default"

    def allow_relation(self, obj1, obj2, **_hints):
        """
        Relations between objects are allowed if both objects are
        in the default pool.
        """
        db_set = {"default"}
        if obj1._state.db in db_set and obj2._state.db in db_set:
            return True
        return None

    def allow_migrate(self, _db, _app_label, _model_name=None, **_hints):
        """ All non-auth models end up in this pool. """
        return True
