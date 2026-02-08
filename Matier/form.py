from django import forms

from Ecole_admin.models import Matier


class MatierForm(forms.ModelForm):
    class Meta:
        model = Matier
        fields = '__all__'