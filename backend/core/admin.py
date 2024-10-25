from django import forms
from django.utils.safestring import mark_safe


class ModelLinkWidget(forms.Widget):
    def __init__(self, obj, attrs=None):
        self.object = obj
        super().__init__(attrs)

    def render(self, name, value, attrs=None):
        if self.object.pk:
            return mark_safe(
                u'<a target="_blank" href="../../../%s/%s/%s/">%s</a>' % \
                (
                    self.object._meta.app_label,
                    self.object._meta.object_name.lower(),
                    self.object.pk, self.object
                )
            )
        else:
            return mark_safe(u'')


class LinkInlineForm(forms.ModelForm):
    ...
    # required=False is essential cause we don't
    # render input tag so there will be no value submitted.
    link = forms.CharField(label='link', required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # instance is always available, it just does or doesn't have pk.
        self.fields['link'].widget = ModelLinkWidget(self.instance)
