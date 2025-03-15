class StafferPermissionMixin:
    def has_module_permission(self, *args, **kwargs):
        return True

    def has_view_permission(self, *args, **kwargs):
        return True

    def has_change_permission(self, *args, **kwargs):
        return True

    def has_add_permission(self, *args, **kwargs):
        return True