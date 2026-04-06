from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.template.context_processors import request
from .models import User, Eleve, Proffeseur, Classe, Paiment, Absence, Matier, Message, AnneeScolaire, Note , ProfesseurAbsence ,   EmploiDuTemps , Ressource , Specialite , Niveau , Batiment
from .utils.utils import get_annee_active
from django.core.exceptions import ValidationError


class UserForm(UserCreationForm):
    class Meta:
        model = User
        fields = [
            'username',
            'nom_complet',
            'sexe',
            'date_naissance',
            'Pays',
            'Ville',
            'Adresse',
            'num_tel',
            'email',
            
            'ecole',
            'password1',
            'password2',
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'nom_complet': forms.TextInput(attrs={'class': 'form-control'}),
            'sexe': forms.Select(attrs={'class': 'form-select'}),
            'date_naissance': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'Pays': forms.TextInput(attrs={'class': 'form-control'}),
            'Ville': forms.TextInput(attrs={'class': 'form-control'}),
            'Adresse': forms.TextInput(attrs={'class': 'form-control'}),
            'num_tel': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'ecole': forms.Select(),
            'password1': forms.PasswordInput(attrs={'class': 'form-control'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control'}),
        }


class UserUpdateForm(forms.ModelForm):

    class Meta:
        model = User
        fields = [
            'username',
            'nom_complet',
            'sexe',
            'date_naissance',
            'Pays',
            'Ville',
            'Adresse',
            'num_tel',
            'email',
            'ecole',
        ]

    def clean_username(self):
        username = self.cleaned_data.get("username")

        qs = User.objects.filter(username=username)

        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise forms.ValidationError("Ce nom d'utilisateur existe déjà.")

        return username





class ConnectionForm(forms.Form):
    username = forms.CharField(max_length=255, widget=forms.TextInput(attrs={"class":"form-control"}))
    password = forms.CharField(max_length=255, widget=forms.PasswordInput(attrs={"class":"form-control"}))

class EleveForm(forms.ModelForm):
    class Meta:
        model = Eleve
        fields = [
            'nom','date_naissancce','Sexe','adrress','telephone','email','photo',
            'classe','parent','telephone_parent','email_parent','status',
        ]
        widgets = {
            'nom': forms.TextInput(attrs={"class":"form-control"}),
            'date_naissancce': forms.DateInput(
                attrs={
                    'class': 'form-control',
                    'type': 'date'
                }
            ),
            'Sexe': forms.Select(attrs={"class":"form-select"}),
            'adrress': forms.TextInput(attrs={"class":"form-control"}),
            'telephone': forms.TextInput(attrs={"class":"form-control"}),
            'email': forms.EmailInput(attrs={"class":"form-control"}),
            'photo': forms.FileInput(attrs={"class":"form-control"}),
            'classe': forms.Select(attrs={"class":"form-select"}),
            'parent': forms.TextInput(attrs={"class":"form-control"}),
            'telephone_parent': forms.TextInput(attrs={"class":"form-control"}),
            'email_parent': forms.EmailInput(attrs={"class":"form-control"}),
            'status': forms.Select(attrs={"class":"form-select"}),
        }

class ProfesseurForm(forms.ModelForm):
    class Meta:
        model = Proffeseur
        fields = [
            'nom_conplet','sexe','telephone','email','adresse',''
            'matieres','classes','actif','diplome','date_empauche','status'


        ]
        widgets = {
            'nom_conplet': forms.TextInput(attrs={"class":"form-control"}),
            'sexe': forms.Select(attrs={"class":"form-select"}),
            'telephone': forms.TextInput(attrs={"class":"form-control"}),
            'email': forms.EmailInput(attrs={"class":"form-control"}),
            'adresse': forms.TextInput(attrs={"class":"form-control"}),
            'matieres': forms.Select(attrs={"class":"form-select"}),
            'classes': forms.CheckboxSelectMultiple(),
            'actif': forms.CheckboxInput(attrs={"class":"form-check-input"}),
            'date_empauche':forms.DateInput(attrs={
                    'class': 'form-control',
                    'type': 'date'
                })
        }

        

class ClasseForm(forms.ModelForm):
    class Meta:
        model = Classe
        fields = ['niveau', 'nom', 'a_specialite', 'specialite']

    def __init__(self, *args, ecole=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._ecole = ecole

        qs = Niveau.objects.filter(actif=True)

        if ecole is not None:
            qs = qs.filter(ecole=ecole)

        self.fields['niveau'].queryset = qs  # ✅ Ici le filtre
        # optionnel: self.fields['niveau'].empty_label = "— Choisir —"

    def clean_niveau(self):
        niveau = self.cleaned_data.get("niveau")
        if self._ecole and niveau and niveau.ecole_id != self._ecole.id:
            raise ValidationError("Niveau invalide pour cette école.")
        return niveau

    def save(self, commit=True):
        obj = super().save(commit=False)
        if self._ecole:
            obj.ecole = self._ecole  # ✅ IMPORTANT si Classe a ecole
        if commit:
            obj.save()
            self.save_m2m()
        return obj

class PaimentForm(forms.ModelForm):
    class Meta:
        model = Paiment
        fields = [
            'eleve',
            'montant',
            'date_paiement',
            'periode',
            'moyen'
        ]
        widgets = {
            'eleve' : forms.Select(),
            'montant' : forms.NumberInput(),
            'date_paiement' : forms.DateInput(attrs={'type': 'date'}),
            'periode' : forms.TextInput(),
            'moyen' : forms.TextInput()
        }


class AbsenceForm(forms.ModelForm):
    class Meta:
        model = Absence
        fields = [
            'eleve',
            'date',
            'h_debut',
            'h_fin',
            'motif',
            'justifiee'
        ]
        widgets ={
            'eleve': forms.Select(),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'motif': forms.TextInput(),
            'justifiee': forms.CheckboxInput()
        }



class ProfesseurAbsenceForm(forms.ModelForm):
    class Meta:
        model = ProfesseurAbsence
        fields = ["professeur", "statut", "date", "h_debut", "h_fin", "motif", "justifiee", "piece"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "h_debut": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
            "h_fin": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
            "motif": forms.TextInput(attrs={"class": "form-control"}),
            "statut": forms.Select(attrs={"class": "form-select"}),
            "professeur": forms.Select(attrs={"class": "form-select"}),
        }




class MatierForm(forms.ModelForm):
    class Meta:
        model = Matier
        fields = [
            'nom',
            'classe'
        ]
        widgets = {
            'nom': forms.TextInput(),
            'classe': forms.Select()
        }

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = [
            
            'sujet',
            'contenu',
            
        ]
#         widgets = {
#             'titre' : forms.TextInput(attrs={'classe':'form-control'}),
#             'contenu' : forms.Textarea(attrs={'classe':'form=control','row': 4}),
            
#         }

#         def __init__(self , *args , **kwarks):
#             user = kwarks.pop('user',None)
#             super().__init__(*args, **kwarks)
#             if user:
#                 self.fields['receiver'].queryset = self.fields['receiver'].queryset.exclude(id=user.id)

class AnneeScolaireForm(forms.ModelForm):
    class Meta:
        model = AnneeScolaire
        fields = {
            'nom',
            'debut',
            'fin'
        }
        widgets = {
            'nom' : forms.TextInput(),
            'debut' : forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fin' : forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = {
            'eleve',
            'matiere',
            'trimestre',
            'note'
        }
        widgets = {
            'eleve' : forms.Select(),
            'matiere': forms.Select(),
            'trimestre': forms.Select(),
            'note' : forms.NumberInput()
        }







from django import forms
from django.forms import modelformset_factory
from .models import PeriodeScolaire, Devoir, Note, DispenseMatiere, Niveau, Classe, Proffeseur, Matier, Eleve, AnneeScolaire

class PeriodeScolaireForm(forms.ModelForm):
    class Meta:
        model = PeriodeScolaire
        fields = ["nom", "debut", "fin", "est_active", "annee_scolaire"]

class DevoirForm(forms.ModelForm):
    class Meta:
        model = Devoir
        fields = ["nom", "niveau", "classes", "professeur", "matiere", "periode", "annee_scolaire", "points", "coefficient"]
        widgets = {
            "classes": forms.SelectMultiple(attrs={"class": "form-select"}),
        }

class FiltreSaisieForm(forms.Form):
    niveau = forms.ModelChoiceField(queryset=Niveau.objects.all(), required=True)
    professeur = forms.ModelChoiceField(queryset=Proffeseur.objects.all(), required=True)
    classe = forms.ModelChoiceField(queryset=Classe.objects.all(), required=True)
    matiere = forms.ModelChoiceField(queryset=Matier.objects.all(), required=True)
    periode = forms.ModelChoiceField(queryset=PeriodeScolaire.objects.all(), required=True)
    devoir = forms.ModelChoiceField(queryset=Devoir.objects.all(), required=False)

class ImportNotesForm(FiltreSaisieForm):
    fichier = forms.FileField(required=True)

class BulletinFiltreForm(forms.Form):
    annee_scolaire = forms.ModelChoiceField(queryset=AnneeScolaire.objects.all(), required=True)
    niveau = forms.ModelChoiceField(queryset=Niveau.objects.all(), required=True)
    classe = forms.ModelChoiceField(queryset=Classe.objects.all(), required=True)
    periode = forms.ModelChoiceField(queryset=PeriodeScolaire.objects.all(), required=True)
    eleve = forms.ModelChoiceField(queryset=Eleve.objects.all(), required=True)
    images_on = forms.BooleanField(required=False)







# forms.py
from django import forms
from django.db.models import Q
from Ecole_admin.models import EmploiDuTemps, Salle, Matier, Proffeseur


class EmploiDuTempsForm(forms.ModelForm):
    class Meta:
        model = EmploiDuTemps
        fields = ["classe", "jour", "heure_debut", "heure_fin", "salle", "professeur", "matiere"]

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

        # bootstrap
        for f in self.fields.values():
            f.widget.attrs.update({"class": "form-control"})

        # rendre obligatoire côté form (même si model allow null)
        self.fields["salle"].required = True

        if self.request:
            ecole = self.request.user.ecole
            self.fields["salle"].queryset = Salle.objects.filter(ecole=ecole)
            self.fields["professeur"].queryset = Proffeseur.objects.filter(ecole=ecole, actif=True)
            self.fields["matiere"].queryset = Matier.objects.filter(ecole=ecole)

    def clean(self):
        cleaned = super().clean()

        classe = cleaned.get("classe")
        jour = cleaned.get("jour")
        hd = cleaned.get("heure_debut")
        hf = cleaned.get("heure_fin")
        salle = cleaned.get("salle")
        prof = cleaned.get("professeur")
        mat = cleaned.get("matiere")

        if not self.request:
            return cleaned

        if not all([classe, jour, hd, hf, salle, prof, mat]):
            return cleaned

        if hf <= hd:
            raise forms.ValidationError("Heure fin doit être > heure début.")

        ecole = self.request.user.ecole
        annee_active = get_annee_active(self.request)

        # ✅ 1) Matière filtrée par prof (chez toi: prof.matieres = 1 seule matière)
        if prof.matieres_id:
            if mat.id != prof.matieres_id:
                raise forms.ValidationError("Cette matière ne correspond pas au professeur sélectionné.")
        else:
            raise forms.ValidationError("Ce professeur n'a pas de matière affectée.")

        # ✅ 2) Prof filtré par classe (proffeseur.classes)
        if not prof.classes.filter(id=classe.id).exists():
            raise forms.ValidationError("Ce professeur n'est pas affecté à cette classe.")

        # ✅ base queryset
        qs = EmploiDuTemps.objects.filter(
            ecole=ecole,
            annee_scolaire=annee_active,
            jour=jour,
        )

        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        overlap = Q(heure_debut__lt=hf) & Q(heure_fin__gt=hd)

        # ✅ Conflit CLASSE (même créneau)
        if qs.filter(overlap, classe=classe).exists():
            raise forms.ValidationError("Conflit: cette classe a déjà un cours dans ce créneau.")

        # ✅ Conflit PROF
        if qs.filter(overlap, professeur=prof).exists():
            raise forms.ValidationError("Conflit: ce professeur est déjà occupé dans ce créneau.")

        # ✅ Conflit SALLE
        if qs.filter(overlap, salle=salle).exists():
            raise forms.ValidationError("Conflit: cette salle est déjà utilisée dans ce créneau.")

        return cleaned


# forms.py
from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Ressource, Matier  # adapte si ton modèle s'appelle Matiere

class RessourceForm(forms.ModelForm):
    class Meta:
        model = Ressource
        fields = ["professeur", "matier", "fichier", "description"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["professeur"].widget.attrs.update({"class": "form-select"})
        self.fields["matier"].widget.attrs.update({"class": "form-select"})
        self.fields["fichier"].widget.attrs.update({"class": "form-control"})
        self.fields["description"].widget.attrs.update({
            "class": "form-control",
            "placeholder": _("Description"),
        })

        # ✅ Placeholder des selects (au lieu de "---------")
        if "professeur" in self.fields:
            self.fields["professeur"].empty_label = _("Sélectionner...")

        if "matier" in self.fields:
            self.fields["matier"].empty_label = _("Sélectionner...")

            # ✅ IMPORTANT: par défaut on ne montre AUCUNE matière
            self.fields["matier"].queryset = Matier.objects.none()

            # ✅ si prof choisi (POST) ou instance (update), on autorise la(les) matière(s)
            prof_id = None
            if self.data.get("professeur"):
                prof_id = self.data.get("professeur")
            elif getattr(self.instance, "professeur_id", None):
                prof_id = self.instance.professeur_id

            if prof_id and str(prof_id).isdigit():
                # Ton modèle Proffeseur -> Matier via FK "matieres"
                # Donc on met uniquement la matière du prof
                from .models import Proffeseur
                prof = Proffeseur.objects.select_related("matieres").filter(id=int(prof_id)).first()
                if prof and getattr(prof, "matieres_id", None):
                    self.fields["matier"].queryset = Matier.objects.filter(id=prof.matieres_id)



class SpecialiteForm(forms.ModelForm):
    class Meta:
        model = Specialite
        fields = {
            'nom',
            'niveau',
           
        }
        widgets = {
            'eleve' : forms.TextInput(),
            'matiere': forms.Select(),
           
        }


class NiveauForm(forms.ModelForm):
    class Meta:
        model = Niveau
        fields = {
            'nom',
            'ordre',
            'actif'
           
        }
        widgets = {
            'eleve' : forms.TextInput(),
            'order': forms.NumberInput(),
            'actif' : forms.BooleanField()
           
        }





from django import forms
from django.contrib.auth.password_validation import validate_password

class ChangePasswordForm(forms.Form):
    old_password = forms.CharField(
        label="Ancien mot de passe",
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )
    new_password1 = forms.CharField(
        label="Nouveau mot de passe",
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )
    new_password2 = forms.CharField(
        label="Confirmer le nouveau mot de passe",
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("new_password1")
        p2 = cleaned.get("new_password2")

        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Les deux mots de passe ne correspondent pas.")

        if p1:
            validate_password(p1)

        return cleaned








from django import forms
from django.db.models import Q
from .models import PeriodeScolaire, Devoir, Note, DispenseMatiere, Classe, Matier, Niveau, Eleve, Proffeseur

from django.utils.translation import gettext_lazy as _

class PeriodeScolaireForm(forms.ModelForm):
    class Meta:
        model = PeriodeScolaire
        fields = ["nom", "debut", "fin", "est_active"]

        labels = {
            "nom": _("Nom"),
            "debut": _("Début"),
            "fin": _("Fin"),
            "est_active": _("Est active"),
        }

        widgets = {
            "debut": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "fin": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "nom": forms.TextInput(attrs={"class": "form-control"}),
            "est_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

from Ecole_admin.utils.periode import is_periode_allowed_for_actions
from Ecole_admin.models import PeriodeScolaire

from django import forms
from Ecole_admin.models import Devoir, Classe, Niveau, Matier, Proffeseur, PeriodeScolaire
from Ecole_admin.utils.periode import is_periode_allowed_for_actions

from django import forms
from django.utils.translation import gettext_lazy as _

class DevoirForm(forms.ModelForm):
    classes = forms.ModelMultipleChoiceField(
        label=_("Classes"),  # ✅ label traduisible
        queryset=Classe.objects.none(),
        widget=forms.SelectMultiple(attrs={"class": "form-select", "size": "8"}),
        required=True,
    )

    class Meta:
        model = Devoir
        fields = ["nom", "niveau", "classes", "professeur", "matiere", "periode", "points", "coefficient"]

        # ✅ labels traduisibles (c’est ça qui manquait)
        labels = {
            "nom": _("Nom"),
            "niveau": _("Niveau"),
            "professeur": _("Professeur"),
            "matiere": _("Matière"),
            "periode": _("Période"),
            "points": _("Points"),
            "coefficient": _("Coefficient"),
        }

        widgets = {
            "nom": forms.TextInput(attrs={"class": "form-control"}),
            "niveau": forms.Select(attrs={"class": "form-select"}),
            "professeur": forms.Select(attrs={"class": "form-select"}),
            "matiere": forms.Select(attrs={"class": "form-select"}),
            "periode": forms.Select(attrs={"class": "form-select"}),
            "points": forms.NumberInput(attrs={"class": "form-control"}),
            "coefficient": forms.NumberInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        ecole = kwargs.pop("ecole", None)
        annee_scolaire = kwargs.pop("annee_scolaire", None)

        super().__init__(*args, **kwargs)

        if ecole:
            self.fields["niveau"].queryset = Niveau.objects.filter(ecole=ecole, actif=True)
            self.fields["classes"].queryset = Classe.objects.filter(ecole=ecole, actif=True)
            self.fields["matiere"].queryset = Matier.objects.filter(ecole=ecole) if hasattr(Matier, "ecole") else Matier.objects.all()
            self.fields["professeur"].queryset = Proffeseur.objects.filter(ecole=ecole, actif=True)

        if ecole and annee_scolaire:
            qs = PeriodeScolaire.objects.filter(ecole=ecole, annee_scolaire=annee_scolaire).order_by("debut")
            allowed_ids = [p.id for p in qs if is_periode_allowed_for_actions(ecole, annee_scolaire, p)]
            self.fields["periode"].queryset = PeriodeScolaire.objects.filter(id__in=allowed_ids).order_by("debut")
        else:
            self.fields["periode"].queryset = PeriodeScolaire.objects.none()

        niveau_val = self.data.get("niveau") or (self.initial.get("niveau") if self.initial else None)
        if niveau_val and ecole:
            try:
                nid = int(niveau_val)
                self.fields["classes"].queryset = Classe.objects.filter(ecole=ecole, niveau_id=nid, actif=True)
            except Exception:
                pass


from django import forms
from django.utils.translation import gettext_lazy as _

class NotesFilterForm(forms.Form):
    classe = forms.ModelChoiceField(
        label=_("Classe"),
        queryset=Classe.objects.none(),
        required=False,
        empty_label=_("Sélectionner..."),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    matiere = forms.ModelChoiceField(
        label=_("Matière"),
        queryset=Matier.objects.none(),
        required=False,
        empty_label=_("Sélectionner..."),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    devoir = forms.ModelChoiceField(
        label=_("Devoir"),
        queryset=Devoir.objects.none(),
        required=False,
        empty_label=_("Sélectionner..."),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    periode = forms.ModelChoiceField(
        label=_("Période"),
        queryset=PeriodeScolaire.objects.none(),
        required=False,
        empty_label=_("Sélectionner..."),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    q = forms.CharField(
        label=_("Élève"),
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Recherche élève..."),
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        ecole = kwargs.pop("ecole", None)
        annee_scolaire = kwargs.pop("annee_scolaire", None)
        super().__init__(*args, **kwargs)

        if ecole:
            self.fields["classe"].queryset = Classe.objects.filter(ecole=ecole, actif=True)
            self.fields["matiere"].queryset = Matier.objects.filter(ecole=ecole) if hasattr(Matier, "ecole") else Matier.objects.all()

        if ecole and annee_scolaire:
            self.fields["devoir"].queryset = Devoir.objects.filter(ecole=ecole, annee_scolaire=annee_scolaire)
            self.fields["periode"].queryset = PeriodeScolaire.objects.filter(ecole=ecole, annee_scolaire=annee_scolaire)

from django import forms
from django.utils.translation import gettext_lazy as _

class NoteSaisieSetupForm(forms.Form):
    devoir = forms.ModelChoiceField(
        label=_("Devoir"),
        queryset=Devoir.objects.none(),
        required=True,
        empty_label=_("Sélectionner..."),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    classe = forms.ModelChoiceField(
        label=_("Classe"),
        queryset=Classe.objects.none(),
        required=True,
        empty_label=_("Sélectionner..."),
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def __init__(self, *args, **kwargs):
        ecole = kwargs.pop("ecole", None)
        annee_scolaire = kwargs.pop("annee_scolaire", None)
        super().__init__(*args, **kwargs)

        if ecole and annee_scolaire:
            self.fields["devoir"].queryset = Devoir.objects.filter(ecole=ecole, annee_scolaire=annee_scolaire)

        if ecole:
            self.fields["classe"].queryset = Classe.objects.filter(ecole=ecole, actif=True)


from django import forms
from django.utils.translation import gettext_lazy as _

class DispenseMatiereForm(forms.ModelForm):
    class Meta:
        model = DispenseMatiere
        fields = ["eleve", "matiere", "periode", "valeur", "motif"]

    # ✅ labels traduisibles
        labels = {
            "eleve": _("Élève"),
            "matiere": _("Matière"),
            "periode": _("Période"),
            "valeur": _("Valeur"),
            "motif": _("Motif"),
        }

        widgets = {
            "eleve": forms.Select(attrs={"class": "form-select"}),
            "matiere": forms.Select(attrs={"class": "form-select"}),
            "periode": forms.Select(attrs={"class": "form-select"}),
            "valeur": forms.TextInput(attrs={"class": "form-control"}),
            "motif": forms.TextInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        ecole = kwargs.pop("ecole", None)
        annee_scolaire = kwargs.pop("annee_scolaire", None)
        super().__init__(*args, **kwargs)

        # ✅ remplace "---------" par "Sélectionner..." (traduisible)
        self.fields["eleve"].empty_label = _("Sélectionner...")
        self.fields["matiere"].empty_label = _("Sélectionner...")
        self.fields["periode"].empty_label = _("Sélectionner...")

        if ecole:
            self.fields["eleve"].queryset = (
                Eleve.objects.filter(ecole=ecole, annee_scolaire=annee_scolaire).select_related("classe")
            )
            self.fields["matiere"].queryset = Matier.objects.filter(ecole=ecole) if hasattr(Matier, "ecole") else Matier.objects.all()
            self.fields["periode"].queryset = PeriodeScolaire.objects.filter(ecole=ecole, annee_scolaire=annee_scolaire)


class BulletinForm(forms.Form):
    eleve = forms.ModelChoiceField(queryset=Eleve.objects.none(), widget=forms.Select(attrs={"class": "form-select"}))
    periode = forms.ModelChoiceField(queryset=PeriodeScolaire.objects.none(), widget=forms.Select(attrs={"class": "form-select"}))

    def __init__(self, *args, **kwargs):
        ecole = kwargs.pop("ecole", None)
        annee_scolaire = kwargs.pop("annee_scolaire", None)
        super().__init__(*args, **kwargs)
        if ecole and annee_scolaire:
            self.fields["eleve"].queryset = Eleve.objects.filter(ecole=ecole, annee_scolaire=annee_scolaire).select_related("classe")
            self.fields["periode"].queryset = PeriodeScolaire.objects.filter(ecole=ecole, annee_scolaire=annee_scolaire)





from Ecole_admin.models import (
    AppreciationPeriode, AppreciationAnnuelle, AppreciationAbsence,
    ConfigMoyenne, ProlongationSaisieNotes
)

class AppreciationPeriodeForm(forms.ModelForm):
    class Meta:
        model = AppreciationPeriode
        fields = ["nom", "note_min", "note_max", "actif"]
        widgets = {
            "nom": forms.TextInput(attrs={"class": "form-control", "placeholder": _("Nom")}),
            "note_min": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "note_max": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "actif": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

class AppreciationAnnuelleForm(forms.ModelForm):
    class Meta:
        model = AppreciationAnnuelle
        fields = ["nom", "note_min", "note_max", "actif"]
        widgets = {
            "nom": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nom"}),
            "note_min": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "note_max": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "actif": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

class AppreciationAbsenceForm(forms.ModelForm):
    class Meta:
        model = AppreciationAbsence
        fields = ["nom", "abs_min", "abs_max", "actif"]
        widgets = {
            "nom": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nom"}),
            "abs_min": forms.NumberInput(attrs={"class": "form-control"}),
            "abs_max": forms.NumberInput(attrs={"class": "form-control"}),
            "actif": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

class ConfigMoyenneForm(forms.ModelForm):
    class Meta:
        model = ConfigMoyenne
        fields = ["niveau", "moyenne_de", "moyenne_a", "status", "actif"]
        widgets = {
            "niveau": forms.Select(attrs={"class": "form-select"}),
            "moyenne_de": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "moyenne_a": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "actif": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

class ProlongationSaisieNotesForm(forms.ModelForm):
    class Meta:
        model = ProlongationSaisieNotes
        fields = ["actif", "prolonger_jours"]
        widgets = {
            "actif": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "prolonger_jours": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
        }




from django import forms
from Ecole_admin.models import DecisionPromotion, DecisionAbsence, CloturePeriode, SignatureConfig

class DecisionPromotionForm(forms.ModelForm):
    class Meta:
        model = DecisionPromotion
        fields = ["decision", "description", "actif"]
        widgets = {
            "decision": forms.TextInput(attrs={"class":"form-control", "placeholder":"Name"}),
            "description": forms.TextInput(attrs={"class":"form-control", "placeholder":"description"}),
            "actif": forms.CheckboxInput(attrs={"class":"form-check-input"}),
        }

class DecisionAbsenceForm(forms.ModelForm):
    class Meta:
        model = DecisionAbsence
        fields = ["max_abs", "statut", "actif"]
        widgets = {
            "max_abs": forms.NumberInput(attrs={"class":"form-control", "placeholder":"Max Abs", "min":"0"}),
            "statut": forms.Select(attrs={"class":"form-select"}),
            "actif": forms.CheckboxInput(attrs={"class":"form-check-input"}),
        }

class CloturePeriodeForm(forms.ModelForm):
    class Meta:
        model = CloturePeriode
        fields = ["periode_scolaire", "annee_scolaire", "description"]
        widgets = {
            "periode_scolaire": forms.Select(attrs={"class":"form-select"}),
            "annee_scolaire": forms.Select(attrs={"class":"form-select"}),
            "description": forms.TextInput(attrs={"class":"form-control", "placeholder":"Description"}),
        }

class SignatureConfigForm(forms.ModelForm):
    class Meta:
        model = SignatureConfig
        fields = ["nom", "fonction", "image", "actif"]
        widgets = {
            "nom": forms.TextInput(attrs={"class":"form-control"}),
            "fonction": forms.TextInput(attrs={"class":"form-control"}),
            "actif": forms.CheckboxInput(attrs={"class":"form-check-input"}),
        }


from Ecole_admin.models import RaisonConvocation

class RaisonConvocationForm(forms.ModelForm):
    class Meta:
        model = RaisonConvocation
        fields = ["libelle"]
        widgets = {
            "libelle": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ex: Absence répétitive"
            })
        }


class ConvocationParentFilterForm(forms.Form):
    niveau_id = forms.IntegerField(required=False)
    classe_id = forms.IntegerField(required=False)
    eleve_id = forms.IntegerField(required=False)

    responsable = forms.CharField(required=False, widget=forms.TextInput(attrs={
        "class": "form-control",
        "readonly": True
    }))

    date_convocation = forms.DateField(required=False, widget=forms.DateInput(attrs={
        "type": "date",
        "class": "form-control"
    }))

    time_convocation = forms.TimeField(required=False, widget=forms.TimeInput(attrs={
        "type": "time",
        "class": "form-control"
    }))


from django import forms
from Ecole_admin.models import Employe

class EmployeForm(forms.ModelForm):
    class Meta:
        model = Employe
        fields = [
            "nom_complet",
            "sexe",
            "telephone",
            "email",
            "fonction",
            "autre_fonction",
            "statut",
            "bureau",
            "date_embauche",
            "working_hours",
        ]
        widgets = {
            "date_embauche": forms.DateInput(attrs={"type": "date"}),
        }

    def clean(self):
        cleaned = super().clean()
        fonction = cleaned.get("fonction")
        autre = (cleaned.get("autre_fonction") or "").strip()

        if fonction == "autre" and autre == "":
            self.add_error("autre_fonction", "Précise la fonction si tu choisis 'Autre'.")
        if fonction != "autre":
            cleaned["autre_fonction"] = ""
        return cleaned





class BatimentForm(forms.ModelForm):
    class Meta:
        model = Batiment
        fields = ["nom", "code", "adresse", "nb_etages", "actif", "description"]
        widgets = {
            "nom": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex: Bâtiment A"}),
            "code": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex: A / B1 (optionnel)"}),
            "adresse": forms.TextInput(attrs={"class": "form-control", "placeholder": "Adresse (optionnel)"}),
            "nb_etages": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "actif": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Description (optionnel)"}),
        }


# app/forms.py
from django import forms
from .models import TypePaiement

class TypePaiementForm(forms.ModelForm):
    class Meta:
        model = TypePaiement
        fields = ["nom", "description", "actif"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ✅ Pas bootstrap pour les inputs (tu as dit modal custom)
        self.fields["nom"].widget.attrs.update({
            "placeholder": _("Nom"),
            "autocomplete": "off",
        })
        self.fields["description"].widget.attrs.update({
            "placeholder": _("Description"),
            "rows": 4,
        })


from django import forms
from django.utils.translation import gettext_lazy as _

from .models import (
    AnneeScolaire,
    Classe,
    DecisionPromotion,
    Niveau,
    PromotionDecisionCode,
    PromotionEleve,
    PromotionEtat,
    Specialite,
)
from .promotion_utils import (
    classe_a_specialite_fixee,
    classe_demande_choix_specialite,
    get_prochaine_classe_par_defaut,
    get_queryset_prochaine_classe,
    get_specialites_queryset_for_classe,
)


class PromotionListeFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        label=_("Recherche"),
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": _("Nom ou identifiant de l'élève"),
        })
    )

    annee_scolaire = forms.ModelChoiceField(
        queryset=AnneeScolaire.objects.none(),
        required=False,
        label=_("Année scolaire"),
        widget=forms.Select(attrs={"class": "form-select"})
    )

    niveau = forms.ModelChoiceField(
        queryset=Niveau.objects.none(),
        required=False,
        label=_("Niveau"),
        widget=forms.Select(attrs={"class": "form-select"})
    )

    classe = forms.ModelChoiceField(
        queryset=Classe.objects.none(),
        required=False,
        label=_("Classe"),
        widget=forms.Select(attrs={"class": "form-select"})
    )

    decision = forms.ChoiceField(
        required=False,
        label=_("Décision"),
        choices=[("", _("Toutes"))] + list(PromotionDecisionCode.choices),
        widget=forms.Select(attrs={"class": "form-select"})
    )

    etat = forms.ChoiceField(
        required=False,
        label=_("État"),
        choices=[("", _("Tous"))] + list(PromotionEtat.choices),
        widget=forms.Select(attrs={"class": "form-select"})
    )

    def __init__(self, *args, **kwargs):
        ecole = kwargs.pop("ecole", None)
        super().__init__(*args, **kwargs)

        self.fields["annee_scolaire"].queryset = AnneeScolaire.objects.order_by("-debut")
        self.fields["niveau"].queryset = Niveau.objects.none()
        self.fields["classe"].queryset = Classe.objects.none()

        selected_niveau_id = None

        if self.is_bound:
            selected_niveau_id = self.data.get(self.add_prefix("niveau")) or None
        else:
            niveau_initial = self.initial.get("niveau")
            if niveau_initial:
                selected_niveau_id = getattr(niveau_initial, "pk", niveau_initial)

        # ✅ Les niveaux dépendent seulement de l'école
        if ecole:
            self.fields["niveau"].queryset = Niveau.objects.filter(
                ecole=ecole,
                actif=True
            ).order_by("ordre", "nom")

        # ✅ Les classes dépendent seulement du niveau choisi
        if ecole and selected_niveau_id:
            self.fields["classe"].queryset = Classe.objects.filter(
                ecole=ecole,
                actif=True,
                niveau_id=selected_niveau_id
            ).select_related("niveau").order_by("ordre", "nom")
class PromotionEvaluationForm(forms.ModelForm):
    class Meta:
        model = PromotionEleve
        fields = [
            "prochaine_classe",
            "prochaine_specialite",
            "commentaire",
        ]
        widgets = {
            "prochaine_classe": forms.Select(attrs={"class": "form-select"}),
            "prochaine_specialite": forms.Select(attrs={"class": "form-select"}),
            "commentaire": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": _("Commentaire ou observation"),
            }),
        }

    def __init__(self, *args, **kwargs):
        ecole = kwargs.pop("ecole", None)
        niveau_actuel = kwargs.pop("niveau_actuel", None)  # gardé si besoin futur
        decision = kwargs.pop("decision", None)
        super().__init__(*args, **kwargs)

        self.fields["prochaine_classe"].required = False
        self.fields["prochaine_specialite"].required = False
        self.fields["commentaire"].required = False

        classe_actuelle = getattr(self.instance, "classe_actuelle", None)
        decision = decision or getattr(self.instance, "decision_proposee", None) or PromotionDecisionCode.ADMIS

        # queryset des classes possibles
        self.fields["prochaine_classe"].queryset = get_queryset_prochaine_classe(
            classe_actuelle=classe_actuelle,
            decision=decision,
        )

        # valeur par défaut de prochaine classe
        if not self.is_bound and classe_actuelle and not self.instance.prochaine_classe_id:
            default_classe = get_prochaine_classe_par_defaut(
                classe_actuelle=classe_actuelle,
                decision=decision,
            )
            if default_classe:
                self.fields["prochaine_classe"].initial = default_classe

        selected_classe = self._get_selected_prochaine_classe()

        # gestion intelligente du champ spécialité
        self.show_specialite = False
        self.fields["prochaine_specialite"].queryset = Specialite.objects.none()

        if selected_classe:
            if classe_a_specialite_fixee(selected_classe):
                self.fields["prochaine_specialite"].initial = selected_classe.specialite
                self.fields["prochaine_specialite"].widget = forms.HiddenInput()
            elif classe_demande_choix_specialite(selected_classe):
                self.show_specialite = True
                self.fields["prochaine_specialite"].queryset = get_specialites_queryset_for_classe(selected_classe)
            else:
                self.fields["prochaine_specialite"].widget = forms.HiddenInput()
        else:
            self.fields["prochaine_specialite"].widget = forms.HiddenInput()

        

    def _get_selected_prochaine_classe(self):
        if self.is_bound:
            classe_id = self.data.get(self.add_prefix("prochaine_classe"))
            if classe_id:
                try:
                    return Classe.objects.select_related("niveau", "specialite").get(pk=classe_id)
                except Classe.DoesNotExist:
                    return None

        if self.instance and self.instance.prochaine_classe_id:
            return self.instance.prochaine_classe

        initial = self.fields["prochaine_classe"].initial
        if isinstance(initial, Classe):
            return initial
        if initial:
            try:
                return Classe.objects.select_related("niveau", "specialite").get(pk=initial)
            except Classe.DoesNotExist:
                return None

        return None

    def clean(self):
        cleaned_data = super().clean()
        prochaine_classe = cleaned_data.get("prochaine_classe")
        prochaine_specialite = cleaned_data.get("prochaine_specialite")

        if prochaine_classe:
            if classe_a_specialite_fixee(prochaine_classe):
                cleaned_data["prochaine_specialite"] = prochaine_classe.specialite
            elif classe_demande_choix_specialite(prochaine_classe):
                if not prochaine_specialite:
                    raise forms.ValidationError(
                        _("Veuillez choisir la spécialité pour la classe cible.")
                    )
            else:
                cleaned_data["prochaine_specialite"] = None

        return cleaned_data


class PromotionValidationForm(forms.ModelForm):
    class Meta:
        model = PromotionEleve
        fields = [
            "decision_finale",
            "decision_personnalisee",
            "prochaine_classe",
            "prochaine_specialite",
            "commentaire",
        ]
        widgets = {
            "decision_finale": forms.Select(attrs={"class": "form-select"}),
            "decision_personnalisee": forms.Select(attrs={"class": "form-select"}),
            "prochaine_classe": forms.Select(attrs={"class": "form-select"}),
            "prochaine_specialite": forms.Select(attrs={"class": "form-select"}),
            "commentaire": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": _("Motif / décision finale / remarque"),
            }),
        }

    def __init__(self, *args, **kwargs):
        ecole = kwargs.pop("ecole", None)
        niveau_actuel = kwargs.pop("niveau_actuel", None)  # gardé si besoin futur
        super().__init__(*args, **kwargs)

        self.fields["decision_personnalisee"].required = False
        self.fields["prochaine_classe"].required = False
        self.fields["prochaine_specialite"].required = False
        self.fields["commentaire"].required = False

        self.fields["decision_personnalisee"].queryset = DecisionPromotion.objects.none()

        if self.instance and self.instance.decision_proposee:
            self.fields["decision_finale"].initial = self.instance.decision_proposee

        if ecole:
            self.fields["decision_personnalisee"].queryset = DecisionPromotion.objects.filter(
                ecole=ecole,
                annee_scolaire=self.instance.annee_scolaire,
                actif=True
            ).order_by("decision")

        decision = self._get_selected_decision()
        classe_actuelle = getattr(self.instance, "classe_actuelle", None)

        self.fields["prochaine_classe"].queryset = get_queryset_prochaine_classe(
            classe_actuelle=classe_actuelle,
            decision=decision,
        )

        if not self.is_bound and classe_actuelle and not self.instance.prochaine_classe_id:
            default_classe = get_prochaine_classe_par_defaut(
                classe_actuelle=classe_actuelle,
                decision=decision,
            )
            if default_classe:
                self.fields["prochaine_classe"].initial = default_classe

        selected_classe = self._get_selected_prochaine_classe()

        self.show_specialite = False
        self.fields["prochaine_specialite"].queryset = Specialite.objects.none()

        if selected_classe:
            if classe_a_specialite_fixee(selected_classe):
                self.fields["prochaine_specialite"].initial = selected_classe.specialite
                self.fields["prochaine_specialite"].widget = forms.HiddenInput()
            elif classe_demande_choix_specialite(selected_classe):
                self.show_specialite = True
                self.fields["prochaine_specialite"].queryset = get_specialites_queryset_for_classe(selected_classe)
            else:
                self.fields["prochaine_specialite"].widget = forms.HiddenInput()
        else:
            self.fields["prochaine_specialite"].widget = forms.HiddenInput()

    def _get_selected_decision(self):
        if self.is_bound:
            return self.data.get(self.add_prefix("decision_finale"))
        return self.instance.decision_finale or self.instance.decision_proposee

    def _get_selected_prochaine_classe(self):
        if self.is_bound:
            classe_id = self.data.get(self.add_prefix("prochaine_classe"))
            if classe_id:
                try:
                    return Classe.objects.select_related("niveau", "specialite").get(pk=classe_id)
                except Classe.DoesNotExist:
                    return None

        if self.instance and self.instance.prochaine_classe_id:
            return self.instance.prochaine_classe

        initial = self.fields["prochaine_classe"].initial
        if isinstance(initial, Classe):
            return initial
        if initial:
            try:
                return Classe.objects.select_related("niveau", "specialite").get(pk=initial)
            except Classe.DoesNotExist:
                return None

        return None

    def clean(self):
        cleaned_data = super().clean()
        decision_finale = cleaned_data.get("decision_finale")
        prochaine_classe = cleaned_data.get("prochaine_classe")
        prochaine_specialite = cleaned_data.get("prochaine_specialite")

        if decision_finale in [
            PromotionDecisionCode.ADMIS,
            PromotionDecisionCode.AUTORISE,
            PromotionDecisionCode.ORIENTE,
        ] and not prochaine_classe:
            raise forms.ValidationError(
                _("Veuillez choisir la prochaine classe pour cette décision.")
            )

        if prochaine_classe:
            if classe_a_specialite_fixee(prochaine_classe):
                cleaned_data["prochaine_specialite"] = prochaine_classe.specialite
            elif classe_demande_choix_specialite(prochaine_classe):
                if not prochaine_specialite:
                    raise forms.ValidationError(
                        _("Veuillez choisir la spécialité pour la classe cible.")
                    )
            else:
                cleaned_data["prochaine_specialite"] = None

        return cleaned_data
    






from django import forms
from .models import ProgrammeOrientation


class ProgrammeOrientationForm(forms.ModelForm):
    class Meta:
        model = ProgrammeOrientation
        fields = ["code", "libelle", "ordre", "actif"]
        widgets = {
            "code": forms.TextInput(attrs={"class": "form-control"}),
            "libelle": forms.TextInput(attrs={"class": "form-control"}),
            "ordre": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
            "actif": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_code(self):
        code = (self.cleaned_data.get("code") or "").strip().upper()
        if not code:
            raise forms.ValidationError("Le code est obligatoire.")
        return code
    



from .models import OrientationScolaire, Niveau, ProgrammeOrientation


class OrientationScolaireForm(forms.ModelForm):
    class Meta:
        model = OrientationScolaire
        fields = ["niveau", "programmes", "date_debut", "date_fin", "actif"]
        widgets = {
            "niveau": forms.Select(attrs={"class": "form-select"}),
            "programmes": forms.SelectMultiple(attrs={"class": "form-select", "size": "6"}),
            "date_debut": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "date_fin": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "actif": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        ecole = kwargs.pop("ecole", None)
        super().__init__(*args, **kwargs)

        if ecole:
            self.fields["niveau"].queryset = Niveau.objects.filter(
                ecole=ecole,
                actif=True
            ).order_by("ordre", "nom")

            self.fields["programmes"].queryset = ProgrammeOrientation.objects.filter(
                ecole=ecole,
                actif=True
            ).order_by("ordre", "code")



from django import forms
from Ecole_admin.models import AnneeScolaire, Niveau, Classe, OrientationScolaire


class FicheVoeuxFilterForm(forms.Form):
    annee_scolaire = forms.ModelChoiceField(
        queryset=AnneeScolaire.objects.all().order_by("-debut"),
        required=True,
        widget=forms.Select(attrs={"class": "form-select", "id": "id_annee_scolaire"})
    )

    niveau = forms.ModelChoiceField(
        queryset=Niveau.objects.none(),
        required=True,
        widget=forms.Select(attrs={"class": "form-select", "id": "id_niveau"})
    )

    classe = forms.ModelChoiceField(
        queryset=Classe.objects.none(),
        required=True,
        widget=forms.Select(attrs={"class": "form-select", "id": "id_classe"})
    )

    def __init__(self, *args, **kwargs):
        ecole = kwargs.pop("ecole", None)
        super().__init__(*args, **kwargs)

        annee_id = self.data.get("annee_scolaire") or self.initial.get("annee_scolaire")
        niveau_id = self.data.get("niveau") or self.initial.get("niveau")

        if ecole and annee_id:
            niveau_ids = OrientationScolaire.objects.filter(
                ecole=ecole,
                annee_scolaire_id=annee_id,
                actif=True
            ).values_list("niveau_id", flat=True)

            self.fields["niveau"].queryset = Niveau.objects.filter(
                ecole=ecole,
                actif=True,
                id__in=niveau_ids
            ).order_by("ordre", "nom")
        else:
            self.fields["niveau"].queryset = Niveau.objects.none()

        if ecole and niveau_id:
            self.fields["classe"].queryset = Classe.objects.filter(
                ecole=ecole,
                actif=True,
                niveau_id=niveau_id
            ).order_by("nom")
        else:
            self.fields["classe"].queryset = Classe.objects.none()


from django import forms
from Ecole_admin.models import AnneeScolaire, Niveau, Classe, OrientationScolaire


class SaisieVoeuxFilterForm(forms.Form):
    annee_scolaire = forms.ModelChoiceField(
        queryset=AnneeScolaire.objects.all().order_by("-debut"),
        required=True,
        widget=forms.Select(attrs={"class": "form-select", "id": "id_annee_scolaire"})
    )

    niveau = forms.ModelChoiceField(
        queryset=Niveau.objects.none(),
        required=True,
        widget=forms.Select(attrs={"class": "form-select", "id": "id_niveau"})
    )

    classe = forms.ModelChoiceField(
        queryset=Classe.objects.none(),
        required=True,
        widget=forms.Select(attrs={"class": "form-select", "id": "id_classe"})
    )

    def __init__(self, *args, **kwargs):
        ecole = kwargs.pop("ecole", None)
        super().__init__(*args, **kwargs)

        annee_id = self.data.get("annee_scolaire") or self.initial.get("annee_scolaire")
        niveau_id = self.data.get("niveau") or self.initial.get("niveau")

        if ecole and annee_id:
            niveau_ids = OrientationScolaire.objects.filter(
                ecole=ecole,
                annee_scolaire_id=annee_id,
                actif=True
            ).values_list("niveau_id", flat=True)

            self.fields["niveau"].queryset = Niveau.objects.filter(
                ecole=ecole,
                actif=True,
                id__in=niveau_ids
            ).order_by("ordre", "nom")
        else:
            self.fields["niveau"].queryset = Niveau.objects.none()

        if ecole and niveau_id:
            self.fields["classe"].queryset = Classe.objects.filter(
                ecole=ecole,
                actif=True,
                niveau_id=niveau_id
            ).order_by("nom")
        else:
            self.fields["classe"].queryset = Classe.objects.none()



from django import forms
from Ecole_admin.models import AnneeScolaire, Niveau, Classe, OrientationScolaire


class AffichageVoeuxFilterForm(forms.Form):
    annee_scolaire = forms.ModelChoiceField(
        queryset=AnneeScolaire.objects.all().order_by("-debut"),
        required=True,
        widget=forms.Select(attrs={"class": "form-select", "id": "id_annee_scolaire"})
    )

    niveau = forms.ModelChoiceField(
        queryset=Niveau.objects.none(),
        required=True,
        widget=forms.Select(attrs={"class": "form-select", "id": "id_niveau"})
    )

    classe = forms.ModelChoiceField(
        queryset=Classe.objects.none(),
        required=True,
        widget=forms.Select(attrs={"class": "form-select", "id": "id_classe"})
    )

    def __init__(self, *args, **kwargs):
        ecole = kwargs.pop("ecole", None)
        super().__init__(*args, **kwargs)

        annee_id = self.data.get("annee_scolaire") or self.initial.get("annee_scolaire")
        niveau_id = self.data.get("niveau") or self.initial.get("niveau")

        if ecole and annee_id:
            niveau_ids = OrientationScolaire.objects.filter(
                ecole=ecole,
                annee_scolaire_id=annee_id,
                actif=True
            ).values_list("niveau_id", flat=True)

            self.fields["niveau"].queryset = Niveau.objects.filter(
                ecole=ecole,
                actif=True,
                id__in=niveau_ids
            ).order_by("ordre", "nom")
        else:
            self.fields["niveau"].queryset = Niveau.objects.none()

        if ecole and niveau_id:
            self.fields["classe"].queryset = Classe.objects.filter(
                ecole=ecole,
                actif=True,
                niveau_id=niveau_id
            ).order_by("nom")
        else:
            self.fields["classe"].queryset = Classe.objects.none()



from django import forms
from Ecole_admin.models import AnneeScolaire, Niveau, Classe, OrientationScolaire


class OrientationFinaleFilterForm(forms.Form):
    annee_scolaire = forms.ModelChoiceField(
        queryset=AnneeScolaire.objects.all().order_by("-debut"),
        required=True,
        widget=forms.Select(attrs={"class": "form-select", "id": "id_annee_scolaire"})
    )

    niveau = forms.ModelChoiceField(
        queryset=Niveau.objects.none(),
        required=True,
        widget=forms.Select(attrs={"class": "form-select", "id": "id_niveau"})
    )

    classe = forms.ModelChoiceField(
        queryset=Classe.objects.none(),
        required=True,
        widget=forms.Select(attrs={"class": "form-select", "id": "id_classe"})
    )

    def __init__(self, *args, **kwargs):
        ecole = kwargs.pop("ecole", None)
        super().__init__(*args, **kwargs)

        annee_id = self.data.get("annee_scolaire") or self.initial.get("annee_scolaire")
        niveau_id = self.data.get("niveau") or self.initial.get("niveau")

        if ecole and annee_id:
            niveau_ids = OrientationScolaire.objects.filter(
                ecole=ecole,
                annee_scolaire_id=annee_id,
                actif=True
            ).values_list("niveau_id", flat=True)

            self.fields["niveau"].queryset = Niveau.objects.filter(
                ecole=ecole,
                actif=True,
                id__in=niveau_ids
            ).order_by("ordre", "nom")
        else:
            self.fields["niveau"].queryset = Niveau.objects.none()

        if ecole and niveau_id:
            self.fields["classe"].queryset = Classe.objects.filter(
                ecole=ecole,
                actif=True,
                niveau_id=niveau_id
            ).order_by("nom")
        else:
            self.fields["classe"].queryset = Classe.objects.none()




from django import forms
from .models import AnneeScolaire, Niveau, OrientationScolaire


class RapportOrientationFilterForm(forms.Form):
    annee_scolaire = forms.ModelChoiceField(
        queryset=AnneeScolaire.objects.all().order_by("-debut"),
        required=True,
        widget=forms.Select(attrs={"class": "form-select", "id": "id_annee_scolaire"})
    )

    niveau = forms.ModelChoiceField(
        queryset=Niveau.objects.none(),
        required=True,
        widget=forms.Select(attrs={"class": "form-select", "id": "id_niveau"})
    )

    def __init__(self, *args, **kwargs):
        ecole = kwargs.pop("ecole", None)
        super().__init__(*args, **kwargs)

        annee_id = self.data.get("annee_scolaire") or self.initial.get("annee_scolaire")

        if ecole and annee_id:
            niveau_ids = OrientationScolaire.objects.filter(
                ecole=ecole,
                annee_scolaire_id=annee_id,
                actif=True
            ).values_list("niveau_id", flat=True)

            self.fields["niveau"].queryset = Niveau.objects.filter(
                ecole=ecole,
                actif=True,
                id__in=niveau_ids
            ).order_by("ordre", "nom")
        else:
            self.fields["niveau"].queryset = Niveau.objects.none()



from django import forms
from .models import AnneeScolaire, Niveau, Classe, OrientationScolaire


class DecisionEleveFilterForm(forms.Form):
    annee_scolaire = forms.ModelChoiceField(
        queryset=AnneeScolaire.objects.all().order_by("-debut"),
        required=True,
        widget=forms.Select(attrs={"class": "form-select", "id": "id_annee_scolaire"})
    )

    niveau = forms.ModelChoiceField(
        queryset=Niveau.objects.none(),
        required=True,
        widget=forms.Select(attrs={"class": "form-select", "id": "id_niveau"})
    )

    classe = forms.ModelChoiceField(
        queryset=Classe.objects.none(),
        required=True,
        widget=forms.Select(attrs={"class": "form-select", "id": "id_classe"})
    )

    def __init__(self, *args, **kwargs):
        ecole = kwargs.pop("ecole", None)
        super().__init__(*args, **kwargs)

        annee_id = self.data.get("annee_scolaire") or self.initial.get("annee_scolaire")
        niveau_id = self.data.get("niveau") or self.initial.get("niveau")

        if ecole and annee_id:
            niveau_ids = OrientationScolaire.objects.filter(
                ecole=ecole,
                annee_scolaire_id=annee_id,
                actif=True
            ).values_list("niveau_id", flat=True)

            self.fields["niveau"].queryset = Niveau.objects.filter(
                ecole=ecole,
                actif=True,
                id__in=niveau_ids
            ).order_by("ordre", "nom")
        else:
            self.fields["niveau"].queryset = Niveau.objects.none()

        if ecole and niveau_id:
            self.fields["classe"].queryset = Classe.objects.filter(
                ecole=ecole,
                actif=True,
                niveau_id=niveau_id
            ).order_by("nom")
        else:
            self.fields["classe"].queryset = Classe.objects.none()





from django import forms
from .models import AnneeScolaire, Niveau, Classe, OrientationScolaire


class RapportDecisionFinaleFilterForm(forms.Form):
    annee_scolaire = forms.ModelChoiceField(
        queryset=AnneeScolaire.objects.all().order_by("-debut"),
        required=True,
        widget=forms.Select(attrs={"class": "form-select", "id": "id_annee_scolaire"})
    )

    niveau = forms.ModelChoiceField(
        queryset=Niveau.objects.none(),
        required=True,
        widget=forms.Select(attrs={"class": "form-select", "id": "id_niveau"})
    )

    classe = forms.ModelChoiceField(
        queryset=Classe.objects.none(),
        required=True,
        widget=forms.Select(attrs={"class": "form-select", "id": "id_classe"})
    )

    def __init__(self, *args, **kwargs):
        ecole = kwargs.pop("ecole", None)
        super().__init__(*args, **kwargs)

        annee_id = self.data.get("annee_scolaire") or self.initial.get("annee_scolaire")
        niveau_id = self.data.get("niveau") or self.initial.get("niveau")

        if ecole and annee_id:
            niveau_ids = OrientationScolaire.objects.filter(
                ecole=ecole,
                annee_scolaire_id=annee_id,
                actif=True
            ).values_list("niveau_id", flat=True)

            self.fields["niveau"].queryset = Niveau.objects.filter(
                ecole=ecole,
                actif=True,
                id__in=niveau_ids
            ).order_by("ordre", "nom")
        else:
            self.fields["niveau"].queryset = Niveau.objects.none()

        if ecole and niveau_id:
            self.fields["classe"].queryset = Classe.objects.filter(
                ecole=ecole,
                actif=True,
                niveau_id=niveau_id
            ).order_by("nom")
        else:
            self.fields["classe"].queryset = Classe.objects.none()