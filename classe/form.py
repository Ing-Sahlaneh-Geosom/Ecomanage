from django import forms

from Ecole_admin.models import Classe


class ClasseForm(forms.ModelForm):
    class Meta:
        model = Classe
        fields = "__all__"