from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Classe, Eleve, Matier, Note, Absence, Paiment, Message, Proffeseur, AnneeScolaire , Ecole , ProfesseurAbsence,  EmploiDuTemps ,EmploiDuTempsSoir , Specialite , Niveau , Ressource , TypePaiement , TarifPaiement , FraisEleve , PaiementFraisEleve , Violence


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    model = User

    list_display = ('username', 'email', 'role','ecole' , 'is_active', 'is_staff')
    list_filter = ('role' , 'is_active', 'is_staff' , 'ecole')
    list_editable = ('role',)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Infos personnelles', {
            'fields': (
                'nom_complet', 'email', 'sexe', 'date_naissance',
                'Pays', 'Ville', 'Adresse', 'num_tel','ecole'
            )
        }),
        ('Permissions', {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Dates importantes', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'email', 'password1', 'password2',
                'nom_complet', 'sexe', 'date_naissance',
                'Pays', 'Ville', 'Adresse', 'num_tel',
                'role', 'ecole' , 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'
            ),
        }),
    )

    search_fields = ('username', 'email', 'nom_complet')
    ordering = ('username',)


@admin.register(Ecole)
class EcoleAdmin(admin.ModelAdmin):
    list_display = ('nom','adresse','telephone','email')
    search_fields = ('nom',)


@admin.register(AnneeScolaire)
class ClasseAdmin(admin.ModelAdmin):
    list_display = ('nom','debut','fin','est_active')
    search_fields = ('est_active',)

@admin.register(Ressource)
class RessourceAdmin(admin.ModelAdmin):
    list_display = ('professeur','matier','fichier','description','created_at')
    search_fields = ('professeur',)


@admin.register(Niveau)
class NiveauAdmin(admin.ModelAdmin):
    list_display = ('nom','actif','ecole','date_creation')
    search_fields = ('nom',)
    list_filter = ('ecole',)

@admin.register(Specialite)
class SpecialiteAdmin(admin.ModelAdmin):
    list_display = ('nom','niveau','ecole')
    search_fields = ('nom',)
    list_filter = ('ecole',)

@admin.register(Classe)
class ClasseAdmin(admin.ModelAdmin):
    list_display = ('nom','a_specialite','specialite')
    search_fields = ('nom',)
    list_filter = ('ecole',)


@admin.register(Eleve)
class EleveAdmin(admin.ModelAdmin):
    list_display = ('identifiant' , 'nom', 'classe', 'user' ,'date_naissancce' , 'ecole' , 'status','annee_scolaire')
    exclude = ['annee_scolaire']
    list_filter = ('classe',)
    search_fields = ('nom',)

@admin.register(Matier)
class MatierAdmin(admin.ModelAdmin):
    list_display = ('nom','classe')
    list_filter = ('nom',)


@admin.register(EmploiDuTemps)
class EmploisDuTempsAdmin(admin.ModelAdmin):
    list_display = ('classe','matiere','professeur','heure_debut','heure_fin')
    list_filter = ('classe',)


@admin.register(EmploiDuTempsSoir)
class EmploisDuTempsSoireAdmin(admin.ModelAdmin):
    list_display = ('classe','matiere','professeur','heure_debut','heure_fin')
    list_filter = ('classe',)



@admin.register(Note)
class NotesAdmin(admin.ModelAdmin):
    list_display = ('eleve','matiere','trimestre','note' , 'user')
    list_filter = ('trimestre','matiere')


@admin.register(Absence)
class AbsenceAdmin(admin.ModelAdmin):
    list_display = ('eleve','date','h_debut','h_fin','motif','justifiee')
    list_filter = ('justifiee',)


@admin.register(ProfesseurAbsence)
class AbsenceProAdmin(admin.ModelAdmin):
    list_display = ('professeur','date','statut','motif','justifiee')
    list_filter = ('justifiee',)



@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender',
                    'receiver',
                    'sujet',
                    'contenu',
                    'date_envoi',
                    'lu',)
    list_filter = ('lu','date_envoi',)

@admin.register(Paiment)
class PaimentAdmin(admin.ModelAdmin):
    list_display = ('eleve','montant','date_paiement','periode','moyen')
    list_filter = ('periode',)


@admin.register(Proffeseur)
class ProfesseurAdmin(admin.ModelAdmin):
    list_display = ('nom_conplet','sexe','telephone','email','adresse','matieres','diplome','date_empauche','status','actif')
    list_filter = ('status','actif',)
    filter_horizontal = ('classes',)
    list_per_page = 20




@admin.register(TypePaiement)
class TypePaimentAdmin(admin.ModelAdmin):
    list_display = ('nom','description','ecole','actif')
    list_filter = ('ecole','actif',)



@admin.register(TarifPaiement)
class TarifPaiementAdmin(admin.ModelAdmin):
    list_display = ('niveau','type_paiement','montant','devise','actif','date_creation')
    list_filter = ('niveau','actif',)
    



@admin.register(FraisEleve)
class FraisEleveAdmin(admin.ModelAdmin):
    list_display = ('ecole','annee_scolaire','eleve','niveau','type_paiement','montant','devise','paye','date_creation')
    list_filter = ('niveau','type_paiement',)
    




@admin.register(PaiementFraisEleve)
class PaimentFraisEleveAdmin(admin.ModelAdmin):
    list_display = ('ecole','annee_scolaire','frais_eleve','montant','devise','mode','reference','date_paiement')
    list_filter = ('date_paiement',)
    



@admin.register(Violence)
class ViolenceAdmin(admin.ModelAdmin):
    list_display = ('agresseur','victime','forme_agression','date','cree_par','created_at')
    list_filter = ('created_at',)
    

