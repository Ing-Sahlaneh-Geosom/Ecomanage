from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Choices
from django.utils import timezone
from django.urls import reverse
from django.conf import settings
from django.db import  transaction
from datetime import timedelta
from django.utils.translation import gettext_lazy as _



class Ecole(models.Model):
    LANG_CHOICES = (
        ("fr", ("Français")),
        ("en", ("English")),
        ("ar", ("العربية")),
    )

    nom = models.CharField(max_length=200,unique=True)
    adresse = models.TextField(blank=True, null=True)
    telephone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    logo = models.ImageField(upload_to='logo/', null=True , blank=True )
    signature = models.ImageField(upload_to='signatures/', null=True , blank=True )
    langue = models.CharField(max_length=2, choices=LANG_CHOICES, default="fr")  # ✅ NEW

    def __str__(self):
        return self.nom



class EmploiDuTempsSoir(models.Model):
    SOIR_CHOICES = [
        ('Samedi', 'Samedi'),
        ('Dimanche', 'Dimanche'),
        ('Lundi', 'Lundi'),
        ('Mardi', 'Mardi'),
        ('Mercredi', 'Mercredi'),
        ('Jeudi', 'Jeudi'),
        
    ]

    classe = models.ForeignKey('Classe', on_delete=models.CASCADE, related_name='emploisoir')
    matiere = models.ForeignKey('Matier', on_delete=models.CASCADE)
    professeur = models.ForeignKey('Proffeseur', on_delete=models.CASCADE)
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()
    soir = models.CharField(max_length=15, choices=SOIR_CHOICES)
    salle = models.CharField(max_length=50, blank=True, null=True)

    ecole = models.ForeignKey('Ecole', on_delete=models.CASCADE)
    annee_scolaire = models.ForeignKey('AnneeScolaire', on_delete=models.CASCADE)
    date_creation = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['soir', 'heure_debut']
        verbose_name_plural = "Emplois du temps de soir"

    def __str__(self):
        return f"{self.classe} - {self.soir} ({self.matiere})"
    

from django.db import models
from django.utils import timezone

class EmploiDuTemps(models.Model):
    JOUR_CHOICES = [
        ('Samedi', 'Samedi'),
        ('Dimanche', 'Dimanche'),
        ('Lundi', 'Lundi'),
        ('Mardi', 'Mardi'),
        ('Mercredi', 'Mercredi'),
        ('Jeudi', 'Jeudi'),
    ]

    classe = models.ForeignKey('Classe', on_delete=models.CASCADE, related_name='emplois')
    matiere = models.ForeignKey('Matier', on_delete=models.CASCADE)
    professeur = models.ForeignKey('Proffeseur', on_delete=models.CASCADE)

    heure_debut = models.TimeField()
    heure_fin = models.TimeField()
    jour = models.CharField(max_length=15, choices=JOUR_CHOICES)

    # ✅ NOUVEAU : salle liée (select)
    salle = models.ForeignKey(
        'Salle',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='emplois'
    )

    ecole = models.ForeignKey('Ecole', on_delete=models.CASCADE)
    annee_scolaire = models.ForeignKey('AnneeScolaire', on_delete=models.CASCADE)
    date_creation = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['jour', 'heure_debut']
        verbose_name_plural = "Emplois du temps"

    def __str__(self):
        return f"{self.classe} - {self.jour} ({self.matiere})"



class User(AbstractUser):
    ROLES = (
        ('admin', _('Administrateur')),
        ('secretaire', _('Secrétaire')),
        ('parent', _('Parent')),
        ('proffesseur', _('Professeur')),
    )
    SEXE = (
        ('M',_('musculin')),
        ('F',_('feminin')),
    )

    nom_complet = models.CharField(max_length=120, blank=True, default="")
    sexe = models.CharField(max_length=1, choices=SEXE, default='M')
    date_naissance = models.DateField( default=timezone.now)
    Pays = models.CharField(max_length=50 )
    Ville = models.CharField(max_length=52, default='')
    Adresse = models.CharField(max_length=100 , default='')
    num_tel = models.CharField(max_length=50, blank=True, default="")
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLES, null=True, blank=True)
    ecole = models.ForeignKey("Ecole", on_delete=models.CASCADE, null=True, blank=True)

    

    def __str__(self):
        return self.username


class AnneeScolaire(models.Model):
    nom = models.CharField(max_length=50, unique=True)
    debut = models.DateField()
    fin = models.DateField()
    est_active = models.BooleanField(default=False)

    def __str__(self):
        return self.nom

    @classmethod
    def get_active(cls):
        return cls.objects.get(est_active=True)


class Niveau(models.Model):
    nom = models.CharField(
        max_length=50,
    
    )  # ex: 6ème, 5ème, Terminale

   
    ordre = models.PositiveIntegerField(
        help_text="Ordre d'affichage",
        default=0
    )

    ecole = models.ForeignKey(
        Ecole,
        on_delete=models.CASCADE , null=True , blank=True
    )

    actif = models.BooleanField(default=True)

    date_creation = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        ordering = ['ordre', 'nom']
        constraints = [
            models.UniqueConstraint(fields=['ecole', 'nom'], name='uniq_niveau_ecole_nom')
        ]

    def __str__(self):
        return self.nom

class Specialite(models.Model):
    nom = models.CharField(max_length=50)
    niveau = models.ForeignKey(Niveau, on_delete=models.CASCADE)
    ecole = models.ForeignKey(Ecole, on_delete=models.CASCADE, blank=True)

    def __str__(self):
        return self.nom


class Classe(models.Model):
    nom = models.CharField(max_length=50)  # ex: 6EME1, TSE, 1ERE S

    niveau = models.ForeignKey(
        Niveau,
        on_delete=models.PROTECT,
        related_name='classes'
    )

    # ✅ NOUVEAU : ordre de la classe dans son niveau
    ordre = models.PositiveIntegerField(
        default=1,
        help_text=_("Ordre de la classe dans le niveau (ex: 1, 2, 3...)")
    )

    a_specialite = models.BooleanField(default=False)

    specialite = models.ForeignKey(
        Specialite,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    ecole = models.ForeignKey(
        Ecole,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    actif = models.BooleanField(default=True)

    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('nom', 'ecole')
        ordering = ['niveau__ordre', 'ordre', 'nom']

    def __str__(self):
        return f"{self.nom} - {self.niveau}"

    def get_absolute_url(self):
        return reverse('Detaille_d_une_classe', kwargs={"pk": self.id})




from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

class Eleve(models.Model):
    
    SEXE = (('M', _('musculin')), ('F', _('feminin')))
    STATUS = (
        ("EN_COURS", _("En cours")),
        ("ADMIS", _("Admis")),
        ("REDOUBLE", _("Redouble")),
        ("AUTORISE", _("Autorisé(e)")),
        ("ORIENTE", _("Orienté(e)")),
        ("DIPLOME", _("Diplômé(e)")),
        ("EXCLU", _("Exclu(e)")),
    )
    identifiant = models.CharField(max_length=20, blank=True, null=True)
    date_inscription = models.DateField(default=timezone.localdate)

    user = models.OneToOneField("User", on_delete=models.CASCADE, null=True, blank=True)
    nom = models.CharField(max_length=100)
    date_naissancce = models.DateField()
    lieu_naissance = models.CharField(max_length=250 , default="Djibouti")
    Sexe = models.CharField(max_length=1, choices=SEXE)
    adrress = models.CharField(max_length=120)
    telephone = models.CharField(max_length=50)
    email = models.EmailField()
    photo = models.ImageField(default='default.png', upload_to='eleve')

    classe = models.ForeignKey('Classe', on_delete=models.SET_NULL, null=True, related_name="eleves")
    parent_user = models.ForeignKey("User", null=True, blank=True, on_delete=models.SET_NULL, related_name="enfants")

    parent = models.CharField(max_length=200)
    telephone_parent = models.CharField(max_length=70, blank=True)
    email_parent = models.EmailField(null=True, blank=True)
    status = models.CharField(max_length=120, choices=STATUS, default="EN_COURS")

    
    parent_user = models.ForeignKey("User", null=True, blank=True, on_delete=models.CASCADE, related_name="enfants")
    annee_scolaire = models.ForeignKey('AnneeScolaire', on_delete=models.CASCADE)
    ecole = models.ForeignKey('Ecole', on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["ecole", "annee_scolaire", "identifiant"],
                name="uniq_eleve_identifiant_par_ecole_annee"
            )
        ]

    def __str__(self):
        return self.nom

    def _generate_identifiant(self):
        # Format: YYYYMMDD + 4 digits (compteur par ECOLE + ANNEE + JOUR)
        date_part = self.date_inscription.strftime("%Y%m%d")
        prefix = date_part

        qs = Eleve.objects.filter(
            ecole_id=self.ecole_id,
            annee_scolaire_id=self.annee_scolaire_id,
            identifiant__startswith=prefix
        )

        last = qs.order_by("-identifiant").values_list("identifiant", flat=True).first()
        next_num = int(last[-4:]) + 1 if last else 1

        return f"{prefix}{next_num:04d}"  # ex: 202601070001

    def save(self, *args, **kwargs):
        if not self.identifiant:
            with transaction.atomic():
                # ecole + annee_scolaire doivent déjà être remplis avant
                if not self.ecole_id or not self.annee_scolaire_id:
                    raise ValueError("ecole et annee_scolaire doivent être définis avant de générer l'identifiant.")
                self.identifiant = self._generate_identifiant()
                super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs)



class Matier(models.Model):
    nom = models.CharField(max_length=100)
    classe = models.ForeignKey(Classe , on_delete=models.CASCADE)
    ecole = models.ForeignKey(Ecole, on_delete=models.CASCADE, null=True, blank=True)
  

    def __str__(self):
        return f"{self.nom} - {self.classe}"



class Proffeseur(models.Model):
    SEXE = (
        ('M', _('musculin')),
        ('F', _('feminin')),
    )
    STATUS_CHOICES = [
    ('Permanent',  _('Permanent')),
    ('Vacataire',  _('Vacataire')),
    ('Stagiaire',  _('Stagiaire')),
]
    user = models.OneToOneField("User", on_delete=models.SET_NULL, null=True, blank=True, related_name="profil_prof")
    nom_conplet = models.CharField(max_length=150)
    sexe = models.CharField(choices=SEXE)
    telephone = models.CharField(max_length=120)
    email = models.EmailField(blank=True)
    adresse = models.CharField(max_length=120, blank=True)
    matieres = models.ForeignKey('Matier', on_delete=models.SET_NULL,null=True,blank=True,related_name='professeurs')
    classes = models.ManyToManyField('Classe', related_name='professeurs')
    diplome = models.FileField(upload_to='diplomes/', null=True, blank=True)
    date_empauche = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Permanent'
    )
    actif = models.BooleanField(default=True)
    ecole = models.ForeignKey(Ecole, on_delete=models.CASCADE, null=True, blank=True)
  

    def __str__(self):
        return f"{self.nom_conplet}"




class Ressource(models.Model):
    professeur = models.ForeignKey(Proffeseur, on_delete=models.CASCADE, related_name="ressources")
    matier = models.ForeignKey(Matier, on_delete=models.CASCADE, related_name="ressources")

    fichier = models.FileField(upload_to="ressources/")
    description = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    ecole = models.ForeignKey(Ecole, on_delete=models.CASCADE, null=True, blank=True)
    annee_scolaire = models.ForeignKey('AnneeScolaire', on_delete=models.CASCADE)

    def __str__(self):
        return f"Ressource - {self.professeur} - {self.matier}"



class Note(models.Model):
    TRIMESTRE_CHOISE = (
        (1,'1er trimestre'),
        (2,'2e trimestre'),
        (3, '3e trimestre'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    eleve = models.ForeignKey(Eleve, on_delete=models.CASCADE)
    matiere = models.ForeignKey(Matier, on_delete=models.CASCADE)
    devoir = models.ForeignKey("Devoir", on_delete=models.SET_NULL, null=True, blank=True)
    trimestre = models.PositiveSmallIntegerField(choices=TRIMESTRE_CHOISE , default=1)
    note = models.DecimalField(max_digits=5, decimal_places=2)
    coefficient = models.PositiveIntegerField(default=1)
    annee_scolaire = models.ForeignKey('AnneeScolaire', on_delete=models.CASCADE)
    ecole = models.ForeignKey(Ecole, on_delete=models.CASCADE, null=True, blank=True)
    
  


    def __str__(self):
        return f"{self.eleve.nom} - {self.matiere.nom} : {self.trimestre} : {self.note} "


# 

class Absence(models.Model):
    
    STATUT_CHOICES = (
        ('present', 'Présent'),
        ('absence', 'Absence'),
        ('retard', 'Retard'),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="absences_saisies"
    )

    eleve = models.ForeignKey(
        Eleve,
        on_delete=models.CASCADE,
        related_name="absences"
    )

    statut = models.CharField(
        max_length=10,
        choices=STATUT_CHOICES,
        default='present'
    )

    date = models.DateField()

    h_debut = models.TimeField(
        null=True,
        blank=True
    )

    h_fin = models.TimeField(
        null=True,
        blank=True
    )

    motif = models.CharField(
        max_length=255,
        blank=True
    )

    justifiee = models.BooleanField(
        default=False
    )

    annee_scolaire = models.ForeignKey(
        'AnneeScolaire',
        on_delete=models.CASCADE
    )

    ecole = models.ForeignKey(
        Ecole,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    date_creation = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        unique_together = (
            'eleve',
            'date',
            'h_debut',
            'h_fin'
        )
        ordering = ['-date', 'h_debut']

    def __str__(self):
        return f"{self.eleve.nom} | {self.date} | {self.get_statut_display()}"



class ProfesseurAbsence(models.Model):
    STATUT_CHOICES = (
        ("present", "Présent"),
        ("absence", "Absence"),
        ("retard", "Retard"),
    )

    # qui a saisi (admin/secretaire)
    user = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="absences_prof_saisies"
    )

    professeur = models.ForeignKey(
        "Proffeseur",
        on_delete=models.CASCADE,
        related_name="absences"
    )

    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default="absence")
    date = models.DateField(default=timezone.localdate)

    h_debut = models.TimeField(null=True, blank=True)
    h_fin = models.TimeField(null=True, blank=True)

    motif = models.CharField(max_length=255, blank=True)
    justifiee = models.BooleanField(default=False)

    # optionnel : justificatif
    piece = models.FileField(upload_to="absences_prof/", null=True, blank=True)

    annee_scolaire = models.ForeignKey("AnneeScolaire", on_delete=models.CASCADE)
    ecole = models.ForeignKey("Ecole", on_delete=models.CASCADE, null=True, blank=True)

    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "professeur__nom_conplet"]
        constraints = [
            models.UniqueConstraint(
                fields=["professeur", "date", "h_debut", "h_fin", "annee_scolaire", "ecole"],
                name="uniq_absence_prof_par_date_heure_ecole_annee"
            )
        ]

    def __str__(self):
        return f"{self.professeur.nom_conplet} | {self.date} | {self.get_statut_display()}"




class Devise(models.TextChoices):
    DJF = "DJF", "DJF"
    USD = "USD", "USD"
    EUR = "EUR", "EUR"

class TarifPaiement(models.Model):
    ecole = models.ForeignKey("Ecole", on_delete=models.CASCADE, related_name="tarifs_paiement")

    # si tu veux par année scolaire (très conseillé)
    annee_scolaire = models.ForeignKey("AnneeScolaire", on_delete=models.CASCADE)

    niveau = models.ForeignKey("Niveau", on_delete=models.CASCADE, related_name="tarifs")
    type_paiement = models.ForeignKey("TypePaiement", on_delete=models.CASCADE, related_name="tarifs")

    montant = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    devise = models.CharField(max_length=10, choices=Devise.choices, default=Devise.DJF)

    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["ecole", "annee_scolaire", "niveau", "type_paiement"],
                name="uniq_tarif_par_ecole_annee_niveau_type"
            )
        ]
        ordering = ["niveau", "type_paiement"]

    def __str__(self):
        return f"{self.ecole} | {self.annee_scolaire} | {self.niveau} | {self.type_paiement} = {self.montant} {self.devise}"


class TypePaiement(models.Model):
    nom = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    ecole = models.ForeignKey(Ecole, on_delete=models.CASCADE, related_name='types_paiement')

    actif = models.BooleanField(default=True)

    def __str__(self):
        return self.nom






class Paiment(models.Model):
    eleve = models.ForeignKey(Eleve, on_delete=models.CASCADE)
    type_paiement = models.ForeignKey(TypePaiement, on_delete=models.PROTECT)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    date_paiement = models.DateField()
    periode = models.CharField(max_length=50)
    moyen = models.CharField(max_length=50, blank=True)
    annee_scolaire = models.ForeignKey('AnneeScolaire', on_delete=models.CASCADE)
    ecole = models.ForeignKey(Ecole, on_delete=models.CASCADE, null=True, blank=True)
  


    def __str__(self):
        return f"{self.eleve.nom} - {self.periode} - {self.montant} fr"




# class Message(models.Model):
#     sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='messages_envoyes')
#     receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='messages_recus')

#     sujet = models.CharField(max_length=255)
#     contenu = models.TextField()

#     # ✅ thread conversation
#     thread_id = models.CharField(max_length=80, db_index=True)
#     parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="reponses")

#     date_envoi = models.DateTimeField(auto_now_add=True)
#     lu = models.BooleanField(default=False)

#     annee_scolaire = models.ForeignKey('AnneeScolaire', on_delete=models.CASCADE)
#     ecole = models.ForeignKey("Ecole", on_delete=models.CASCADE, null=True, blank=True)

#     def __str__(self):
#         return f"{self.sujet} -> {self.receiver}"



class FraisEleve(models.Model):
    ecole = models.ForeignKey("Ecole", on_delete=models.CASCADE)
    annee_scolaire = models.ForeignKey("AnneeScolaire", on_delete=models.CASCADE)

    eleve = models.ForeignKey("Eleve", on_delete=models.CASCADE, related_name="frais")
    niveau = models.ForeignKey("Niveau", on_delete=models.CASCADE)
    type_paiement = models.ForeignKey("TypePaiement", on_delete=models.CASCADE)

    montant = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    devise = models.CharField(max_length=10, default="DJF")

    paye = models.BooleanField(default=False)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["ecole","annee_scolaire","eleve","type_paiement"],
                name="uniq_frais_eleve_par_annee_type"
            )
        ]


from django.db import models

class ModePaiement(models.TextChoices):
    ESPECES  = "especes", _("Espèces")
    CHEQUE   = "cheque", _("Chèque")
    VIREMENT = "virement", _("Virement")
    MOBILE   = "mobile", _("Mobile money")
    
class PaiementFraisEleve(models.Model):
    ecole = models.ForeignKey("Ecole", on_delete=models.CASCADE)
    annee_scolaire = models.ForeignKey("AnneeScolaire", on_delete=models.CASCADE)

    frais_eleve = models.ForeignKey("FraisEleve", on_delete=models.CASCADE, related_name="paiements")

    montant = models.DecimalField(max_digits=12, decimal_places=2)
    devise = models.CharField(max_length=10, default="DJF")
    mode = models.CharField(max_length=20, choices=ModePaiement.choices, default=ModePaiement.ESPECES)

    reference = models.CharField(max_length=100, blank=True)  # reçu, ref transaction etc.
    date_paiement = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ["-date_paiement"]

    def __str__(self):
        return f"{self.frais_eleve.eleve} - {self.montant} {self.devise}"


from django.db import models
from django.utils import timezone
import uuid

class RecuCaisse(models.Model):
    STATUT_CHOICES = (
        ("valide", _("Validé")),
        ("annule", _("Annulé")),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    ecole = models.ForeignKey("Ecole", on_delete=models.CASCADE)
    annee_scolaire = models.ForeignKey("AnneeScolaire", on_delete=models.CASCADE)
    eleve = models.ForeignKey("Eleve", on_delete=models.CASCADE, related_name="recus")
    caissier = models.ForeignKey("User", on_delete=models.SET_NULL, null=True, related_name="recus_caisses")

    numero = models.CharField(max_length=30, unique=True)  # RC-2026-00001
    date_operation = models.DateTimeField(default=timezone.now)

    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    devise = models.CharField(max_length=10, default="DJF")

    mode = models.CharField(max_length=20, default=_("especes"))
    reference = models.CharField(max_length=100, blank=True)
    note = models.CharField(max_length=255, blank=True)

    # ✅ annulation
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default="valide")
    annule_par = models.ForeignKey("User", on_delete=models.SET_NULL, null=True, blank=True, related_name="recus_annules")
    date_annulation = models.DateTimeField(null=True, blank=True)
    motif_annulation = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.numero} - {self.eleve.nom} ({self.statut})"


class LigneRecuCaisse(models.Model):
    recu = models.ForeignKey(RecuCaisse, on_delete=models.CASCADE, related_name="lignes")
    frais_eleve = models.ForeignKey("FraisEleve", on_delete=models.CASCADE, related_name="lignes_recu")

    montant = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    devise = models.CharField(max_length=10, default="DJF")

    def __str__(self):
        return f"{self.recu.numero} | {self.frais_eleve.type_paiement} | {self.montant}"

# models.py
class Message(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='message_envoyes')
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='message_recus',blank=True,null=True)
    sujet = models.CharField(max_length=255)
    contenu = models.TextField()
    date_envoi = models.DateTimeField(auto_now_add=True)
    lu = models.BooleanField(default=False)
    annee_scolaire = models.ForeignKey('AnneeScolaire', on_delete=models.CASCADE)
    ecole = models.ForeignKey(Ecole, on_delete=models.CASCADE, null=True, blank=True)

    # ✅ NEW: suppression logique
    deleted_by_sender = models.BooleanField(default=False)
    deleted_by_receiver = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sujet} - a {self.receiver}"




class MessageDestinataire(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="destinataires")
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="inbox")

    lu = models.BooleanField(default=False)
    date_lu = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("message", "receiver")
        ordering = ["-message__date_envoi"]

    def __str__(self):
        return f"{self.receiver} <- {self.message.sujet}"




# ======= AJOUTS POUR GESTION DES NOTES (Périodes / Devoirs / Dispenses) =======

class PeriodeScolaire(models.Model):
    """Trimestre 1/2/3 avec dates (comme ton écran Période scolaire)."""
    nom = models.CharField(max_length=50)  # ex: Trimestre 1
    debut = models.DateField()
    fin = models.DateField()
    est_active = models.BooleanField(default=False)

    annee_scolaire = models.ForeignKey("AnneeScolaire", on_delete=models.CASCADE)
    ecole = models.ForeignKey("Ecole", on_delete=models.CASCADE)
    prolongation_jours = models.PositiveIntegerField(default=0)

    @property
    def fin_effective(self):
        return self.fin + timedelta(days=int(self.prolongation_jours or 0))

    class Meta:
        unique_together = ("ecole", "annee_scolaire", "nom")
        ordering = ("debut",)

    def __str__(self):
        return f"{self.nom} ({self.annee_scolaire})"


class Devoir(models.Model):
    """Devoir/Test (comme ton écran Créer un devoir)."""
    nom = models.CharField(max_length=120)  # ex: Devoir 1
    niveau = models.ForeignKey("Niveau", on_delete=models.PROTECT)
    classes = models.ManyToManyField("Classe", related_name="devoirs")

    professeur = models.ForeignKey("Proffeseur", on_delete=models.PROTECT)
    matiere = models.ForeignKey("Matier", on_delete=models.PROTECT)

    periode = models.ForeignKey("PeriodeScolaire", on_delete=models.PROTECT)
    annee_scolaire = models.ForeignKey("AnneeScolaire", on_delete=models.CASCADE)
    ecole = models.ForeignKey("Ecole", on_delete=models.CASCADE)

    points = models.PositiveIntegerField(default=20)
    coefficient = models.PositiveIntegerField(default=1)

    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-date_creation",)

    def __str__(self):
        return f"{self.nom} - {self.matiere} - {self.periode}"


class DispenseMatiere(models.Model):
    """Dispense par élève / matière / période (colonne Dispense)."""
    eleve = models.ForeignKey("Eleve", on_delete=models.CASCADE)
    matiere = models.ForeignKey("Matier", on_delete=models.CASCADE)
    periode = models.ForeignKey("PeriodeScolaire", on_delete=models.CASCADE)

    valeur = models.CharField(max_length=50, default="Disp")  # ex: Disp
    motif = models.CharField(max_length=255, blank=True)

    annee_scolaire = models.ForeignKey("AnneeScolaire", on_delete=models.CASCADE)
    ecole = models.ForeignKey("Ecole", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("eleve", "matiere", "periode", "annee_scolaire", "ecole")
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.eleve} - {self.matiere} - {self.periode} ({self.valeur})"






# =========================
# CONFIGURATION DES APPRECIATIONS
# =========================
from django.core.validators import MinValueValidator, MaxValueValidator

class AppreciationPeriode(models.Model):
    nom = models.CharField(max_length=255)
    note_min = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0)])
    note_max = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0)])

    annee_scolaire = models.ForeignKey("AnneeScolaire", on_delete=models.CASCADE)
    ecole = models.ForeignKey("Ecole", on_delete=models.CASCADE)

    actif = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("note_min",)
       
    def __str__(self):
        return f"{self.nom} ({self.note_min} - {self.note_max})"


class AppreciationAnnuelle(models.Model):
    nom = models.CharField(max_length=255)
    note_min = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0)])
    note_max = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0)])

    annee_scolaire = models.ForeignKey("AnneeScolaire", on_delete=models.CASCADE)
    ecole = models.ForeignKey("Ecole", on_delete=models.CASCADE)

    actif = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("note_min",)
        unique_together = ("ecole", "annee_scolaire", "nom")

    def __str__(self):
        return f"{self.nom} ({self.note_min} - {self.note_max})"


class AppreciationAbsence(models.Model):
    nom = models.CharField(max_length=255)
    abs_min = models.PositiveIntegerField(default=0)
    abs_max = models.PositiveIntegerField(default=0)

    annee_scolaire = models.ForeignKey("AnneeScolaire", on_delete=models.CASCADE)
    ecole = models.ForeignKey("Ecole", on_delete=models.CASCADE)

    actif = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("abs_min",)
        unique_together = ("ecole", "annee_scolaire", "nom")

    def __str__(self):
        return f"{self.nom} ({self.abs_min} - {self.abs_max})"


# =========================
# CONFIGURATION DE MOYEN (SANS AGE)
# =========================
class ConfigMoyenne(models.Model):
    """
    ✅ Comme ta capture "Configuration de moyen", MAIS SANS les champs âge.
    Seulement: niveau + moyenne_de + moyenne_a + status (choix).
    """
    STATUS_CHOICES = (
        ("admis", _("Admis")),
        ("redouble", _("Redouble")),
        ("autorise", _("Autorisé(e)")),
        ("exclu", _("Exclu")),
    )
    

    niveau = models.ForeignKey("Niveau", on_delete=models.PROTECT)
    moyenne_de = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0)])
    moyenne_a = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0)])

    status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    annee_scolaire = models.ForeignKey("AnneeScolaire", on_delete=models.CASCADE)
    ecole = models.ForeignKey("Ecole", on_delete=models.CASCADE)

    actif = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("niveau", "moyenne_de")
        constraints = [
            models.UniqueConstraint(
                fields=["ecole", "annee_scolaire", "niveau", "moyenne_de", "moyenne_a", "status"],
                name="uniq_cfg_moyenne_par_ecole_annee"
            )
        ]

    def __str__(self):
        return f"{self.niveau} | {self.moyenne_de}-{self.moyenne_a} => {self.get_status_display()}"


# =========================
# PROLONGER LA SAISIE DES NOTES
# =========================
class ProlongationSaisieNotes(models.Model):
    """
    Garde une règle par (prof, niveau, période).
    Permet d'activer/désactiver et d'ajouter des jours.
    """
    professeur = models.ForeignKey("Proffeseur", on_delete=models.CASCADE)
    niveau = models.ForeignKey("Niveau", on_delete=models.PROTECT)
    periode = models.ForeignKey("PeriodeScolaire", on_delete=models.PROTECT)

    debut = models.DateField()
    fin = models.DateField()

    actif = models.BooleanField(default=False)
    prolonger_jours = models.PositiveIntegerField(default=0)

    annee_scolaire = models.ForeignKey("AnneeScolaire", on_delete=models.CASCADE)
    ecole = models.ForeignKey("Ecole", on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        unique_together = ("ecole", "annee_scolaire", "professeur", "niveau", "periode")

    def __str__(self):
        return f"{self.professeur} | {self.niveau} | {self.periode} ({'ON' if self.actif else 'OFF'})"




from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone

# =========================
# DECISIONS DE PROMOTION
# =========================
class DecisionPromotion(models.Model):
    decision = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True)

    annee_scolaire = models.ForeignKey("AnneeScolaire", on_delete=models.CASCADE)
    ecole = models.ForeignKey("Ecole", on_delete=models.CASCADE)

    actif = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("decision",)
        unique_together = ("ecole", "annee_scolaire", "decision")

    def __str__(self):
        return self.decision


# =========================
# DECISION D'ABSENCE
# =========================
class DecisionAbsence(models.Model):
    """
    Capture: Max Abs + Statut
    Statut: on utilise tes choix élèves (tu avais R/F).
    Tu peux ajouter A/E si tu veux.
    """
    STATUT_CHOICES = (
        ("R", _("Redouble")),
        ("F", _("Admis")),
        ("A", _("Autorisé(e)")),
        ("E", _("Exclu(e)")),
    )

    max_abs = models.PositiveIntegerField(validators=[MinValueValidator(0)])
    statut = models.CharField(max_length=2, choices=STATUT_CHOICES)

    annee_scolaire = models.ForeignKey("AnneeScolaire", on_delete=models.CASCADE)
    ecole = models.ForeignKey("Ecole", on_delete=models.CASCADE)

    actif = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("max_abs",)
        unique_together = ("ecole", "annee_scolaire", "max_abs", "statut")

    def __str__(self):
        return f"{self.max_abs} => {self.get_statut_display()}"
    


from decimal import Decimal, ROUND_HALF_UP


class PromotionEtat(models.TextChoices):
    EN_ATTENTE = "en_attente", _("En attente")
    EVALUE = "evalue", _("Évalué")
    VALIDE = "valide", _("Validé")
    EXECUTE = "execute", _("Exécuté")


class PromotionDecisionCode(models.TextChoices):
    ATTENTE = "attente", _("En attente")
    ADMIS = "admis", _("Admis")
    REDOUBLE = "redouble", _("Redouble")
    AUTORISE = "autorise", _("Autorisé(e)")
    ORIENTE = "oriente", _("Orienté(e)")
    DIPLOME = "diplome", _("Diplômé(e)")
    EXCLU = "exclu", _("Exclu(e)")


class PromotionEleve(models.Model):
    ecole = models.ForeignKey("Ecole", on_delete=models.CASCADE, related_name="promotions_eleves")
    annee_scolaire = models.ForeignKey("AnneeScolaire", on_delete=models.CASCADE, related_name="promotions_eleves")

    eleve = models.ForeignKey("Eleve", on_delete=models.CASCADE, related_name="promotions")

    niveau_actuel = models.ForeignKey(
        "Niveau",
        on_delete=models.PROTECT,
        related_name="promotions_niveau_actuel",
        null=True,
        blank=True
    )
    classe_actuelle = models.ForeignKey(
        "Classe",
        on_delete=models.PROTECT,
        related_name="promotions_classe_actuelle",
        null=True,
        blank=True
    )

    moyenne_annuelle = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    total_absences = models.PositiveIntegerField(default=0)
    total_retards = models.PositiveIntegerField(default=0)

    decision_proposee = models.CharField(
        max_length=20,
        choices=PromotionDecisionCode.choices,
        default=PromotionDecisionCode.ATTENTE
    )
    decision_finale = models.CharField(
        max_length=20,
        choices=PromotionDecisionCode.choices,
        default=PromotionDecisionCode.ATTENTE
    )

    # optionnel : si admin choisit une décision personnalisée depuis DecisionPromotion
    decision_personnalisee = models.ForeignKey(
        "DecisionPromotion",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="promotions_personnalisees"
    )

    etat = models.CharField(
        max_length=20,
        choices=PromotionEtat.choices,
        default=PromotionEtat.EN_ATTENTE
    )

    prochaine_niveau = models.ForeignKey(
        "Niveau",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="promotions_niveau_cible"
    )
    prochaine_classe = models.ForeignKey(
        "Classe",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="promotions_classe_cible"
    )
    prochaine_specialite = models.ForeignKey(
        "Specialite",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="promotions_specialite_cible"
    )

    commentaire = models.TextField(blank=True)

    evalue_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="promotions_evaluees"
    )
    valide_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="promotions_validees"
    )
    execute_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="promotions_executees"
    )

    date_evaluation = models.DateTimeField(null=True, blank=True)
    date_validation = models.DateTimeField(null=True, blank=True)
    date_execution = models.DateTimeField(null=True, blank=True)

    est_diplome = models.BooleanField(default=False)
    est_traite = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["classe_actuelle__nom", "eleve__nom"]
        constraints = [
            models.UniqueConstraint(
                fields=["ecole", "annee_scolaire", "eleve"],
                name="uniq_promotion_eleve_par_ecole_annee"
            )
        ]

    def __str__(self):
        return f"{self.eleve} - {self.annee_scolaire} - {self.get_decision_finale_display()}"

    def save(self, *args, **kwargs):
        default_classe = None

        if not self.classe_actuelle_id and self.eleve_id and self.eleve.classe_id:
            self.classe_actuelle = self.eleve.classe

        if not self.niveau_actuel_id and self.classe_actuelle_id:
            self.niveau_actuel = self.classe_actuelle.niveau

        if self.classe_actuelle_id and not self.prochaine_classe_id:
            from .promotion_utils import get_prochaine_classe_par_defaut

            decision = self.decision_finale or self.decision_proposee
            default_classe = get_prochaine_classe_par_defaut(
                classe_actuelle=self.classe_actuelle,
                decision=decision,
            )

        if default_classe:
            self.prochaine_classe = default_classe

            if getattr(default_classe, "specialite_id", None):
                self.prochaine_specialite = default_classe.specialite
            else:
                self.prochaine_specialite = None

        if self.prochaine_classe_id and self.prochaine_classe:
            self.prochaine_niveau = self.prochaine_classe.niveau

        if getattr(self.prochaine_classe, "specialite_id", None):
            self.prochaine_specialite = self.prochaine_classe.specialite
        elif not self.prochaine_classe.a_specialite:
            self.prochaine_specialite = None
        else:
            self.prochaine_niveau = None
            self.prochaine_specialite = None

        super().save(*args, **kwargs)

    def calculer_total_absences(self):
        return Absence.objects.filter(
            eleve=self.eleve,
            annee_scolaire=self.annee_scolaire,
            ecole=self.ecole,
            statut="absence"
        ).count()

    def calculer_total_retards(self):
        return Absence.objects.filter(
            eleve=self.eleve,
            annee_scolaire=self.annee_scolaire,
            ecole=self.ecole,
            statut="retard"
        ).count()

    def calculer_moyenne_annuelle(self):
        notes = Note.objects.filter(
            eleve=self.eleve,
            annee_scolaire=self.annee_scolaire,
            ecole=self.ecole
        ).select_related("devoir")

        total_points = Decimal("0.00")
        total_coef = 0

        for n in notes:
            coef = int(n.coefficient or 1)
            note_brute = Decimal(str(n.note))

            # normalisation sur 20 si devoir.points != 20
            points_devoir = Decimal("20")
            if n.devoir_id and getattr(n.devoir, "points", None):
                points_devoir = Decimal(str(n.devoir.points))

            if points_devoir > 0 and points_devoir != Decimal("20"):
                note_sur_20 = (note_brute * Decimal("20")) / points_devoir
            else:
                note_sur_20 = note_brute

            if note_sur_20 > Decimal("20"):
                note_sur_20 = Decimal("20")

            total_points += note_sur_20 * coef
            total_coef += coef

        if total_coef == 0:
            return Decimal("0.00")

        moyenne = (total_points / Decimal(str(total_coef))).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )
        return moyenne

    def proposer_decision(self, user=None):
        self.total_absences = self.calculer_total_absences()
        self.total_retards = self.calculer_total_retards()
        self.moyenne_annuelle = self.calculer_moyenne_annuelle()

        # 1) priorité à la règle d'absence si elle existe
        regle_abs = DecisionAbsence.objects.filter(
            ecole=self.ecole,
            annee_scolaire=self.annee_scolaire,
            actif=True,
            max_abs__lte=self.total_absences
        ).order_by("-max_abs").first()

        map_absence = {
            "R": PromotionDecisionCode.REDOUBLE,
            "F": PromotionDecisionCode.ADMIS,
            "A": PromotionDecisionCode.AUTORISE,
            "E": PromotionDecisionCode.EXCLU,
        }

        if regle_abs:
            self.decision_proposee = map_absence.get(
                regle_abs.statut,
                PromotionDecisionCode.ATTENTE
            )
        else:
            # 2) sinon, décision selon config moyenne
            cfg = ConfigMoyenne.objects.filter(
                ecole=self.ecole,
                annee_scolaire=self.annee_scolaire,
                niveau=self.niveau_actuel,
                actif=True,
                moyenne_de__lte=self.moyenne_annuelle,
                moyenne_a__gte=self.moyenne_annuelle
            ).order_by("moyenne_de").first()

            if cfg:
                self.decision_proposee = cfg.status
            else:
                self.decision_proposee = PromotionDecisionCode.ATTENTE

        self.etat = PromotionEtat.EVALUE
        self.date_evaluation = timezone.now()
        self.evalue_par = user
        self.save()

        return self.decision_proposee

    def valider_decision(self, user=None, decision=None, commentaire=""):
        self.decision_finale = decision or self.decision_proposee or PromotionDecisionCode.ATTENTE
        self.commentaire = commentaire or self.commentaire
        self.valide_par = user
        self.date_validation = timezone.now()
        self.etat = PromotionEtat.VALIDE
        self.est_diplome = self.decision_finale == PromotionDecisionCode.DIPLOME
        self.save()

    def executer_promotion(self, user=None):
        if self.decision_finale == PromotionDecisionCode.ATTENTE:
            raise ValueError("Impossible d'exécuter une promotion sans décision finale.")

        ancienne_classe = self.eleve.classe
        ancien_niveau = ancienne_classe.niveau if ancienne_classe else None

        # mise à jour du statut élève
        map_status_eleve = {
            PromotionDecisionCode.ADMIS: "ADMIS",
            PromotionDecisionCode.REDOUBLE: "REDOUBLE",
            PromotionDecisionCode.AUTORISE: "AUTORISE",
            PromotionDecisionCode.ORIENTE: "ORIENTE",
            PromotionDecisionCode.DIPLOME: "DIPLOME",
            PromotionDecisionCode.EXCLU: "EXCLU",
        }

        # changement de classe seulement si logique de passage
        if self.decision_finale in [
            PromotionDecisionCode.ADMIS,
            PromotionDecisionCode.AUTORISE,
            PromotionDecisionCode.ORIENTE,
        ] and self.prochaine_classe_id:
            self.eleve.classe = self.prochaine_classe

        if self.decision_finale in map_status_eleve:
            self.eleve.status = map_status_eleve[self.decision_finale]

        self.eleve.save()

        HistoriqueChangementClasse.objects.create(
            ecole=self.ecole,
            annee_scolaire=self.annee_scolaire,
            eleve=self.eleve,
            ancienne_niveau=ancien_niveau,
            ancienne_classe=ancienne_classe,
            nouvelle_niveau=self.eleve.classe.niveau if self.eleve.classe else None,
            nouvelle_classe=self.eleve.classe,
            decision=self.decision_finale,
            source="promotion",
            motif=self.commentaire or f"Promotion exécutée : {self.get_decision_finale_display()}",
            cree_par=user,
            promotion=self
        )

        self.execute_par = user
        self.date_execution = timezone.now()
        self.etat = PromotionEtat.EXECUTE
        self.est_traite = True
        self.save()


class HistoriqueChangementClasse(models.Model):
    SOURCE_CHOICES = (
        ("promotion", _("Promotion")),
        ("orientation", _("Orientation")),
        ("manuel", _("Manuel")),
    )

    ecole = models.ForeignKey("Ecole", on_delete=models.CASCADE, related_name="historiques_changement_classe")
    annee_scolaire = models.ForeignKey("AnneeScolaire", on_delete=models.CASCADE, related_name="historiques_changement_classe")

    eleve = models.ForeignKey("Eleve", on_delete=models.CASCADE, related_name="historiques_changement_classe")

    ancienne_niveau = models.ForeignKey(
        "Niveau",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="anciens_niveaux_changement"
    )
    ancienne_classe = models.ForeignKey(
        "Classe",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="anciennes_classes_changement"
    )

    nouvelle_niveau = models.ForeignKey(
        "Niveau",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="nouveaux_niveaux_changement"
    )
    nouvelle_classe = models.ForeignKey(
        "Classe",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="nouvelles_classes_changement"
    )

    decision = models.CharField(max_length=20, choices=PromotionDecisionCode.choices, default=PromotionDecisionCode.ATTENTE)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default="manuel")

    motif = models.TextField(blank=True)

    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="changements_classe_crees"
    )

    promotion = models.ForeignKey(
        "PromotionEleve",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="historiques"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.eleve} : {self.ancienne_classe} -> {self.nouvelle_classe}"


# =========================
# CLOTURE DES PERIODES
# =========================
class CloturePeriode(models.Model):
    periode_scolaire = models.ForeignKey("PeriodeScolaire", on_delete=models.PROTECT)
    annee_scolaire = models.ForeignKey("AnneeScolaire", on_delete=models.CASCADE)
    description = models.CharField(max_length=255, blank=True)

    ecole = models.ForeignKey("Ecole", on_delete=models.CASCADE)

    cloturee = models.BooleanField(default=False)
    cloturee_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        unique_together = ("ecole", "annee_scolaire", "periode_scolaire")

    def __str__(self):
        return f"{self.annee_scolaire} - {self.periode_scolaire}"

    def set_cloture(self, value: bool):
        self.cloturee = value
        self.cloturee_at = timezone.now() if value else None
        self.save(update_fields=["cloturee", "cloturee_at"])


# =========================
# (OPTION) SIGNATURE
# =========================
class SignatureConfig(models.Model):
    nom = models.CharField(max_length=255)
    fonction = models.CharField(max_length=255, blank=True)
    image = models.ImageField(upload_to="signatures/", blank=True, null=True)

    annee_scolaire = models.ForeignKey("AnneeScolaire", on_delete=models.CASCADE)
    ecole = models.ForeignKey("Ecole", on_delete=models.CASCADE)

    actif = models.BooleanField(default=True)

    class Meta:
        ordering = ("nom",)

    def __str__(self):
        return self.nom



class RaisonConvocation(models.Model):
    libelle = models.CharField(max_length=255)
    actif = models.BooleanField(default=True)
    ecole = models.ForeignKey("Ecole", on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        ordering = ["libelle"]
        unique_together = ("ecole", "libelle")

    def __str__(self):
        return self.libelle


class ConvocationParent(models.Model):
    ecole = models.ForeignKey("Ecole", on_delete=models.CASCADE, null=True, blank=True)
    annee_scolaire = models.ForeignKey("AnneeScolaire", on_delete=models.CASCADE)

    niveau = models.ForeignKey("Niveau", on_delete=models.PROTECT)
    classe = models.ForeignKey("Classe", on_delete=models.PROTECT)
    eleve = models.ForeignKey("Eleve", on_delete=models.CASCADE)

    # parent (si ton élève a parent_user)
    parent_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="convocations_recues"
    )

    # expéditeur
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="convocations_creees"
    )

    raison = models.ForeignKey("RaisonConvocation", on_delete=models.PROTECT)
    message = models.TextField(blank=True)

    date_convocation = models.DateField(default=timezone.localdate)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_creation"]

    def __str__(self):
        return f"Convocation: {self.eleve} - {self.raison}"



class Violence(models.Model):
    agresseur = models.ForeignKey("Eleve", on_delete=models.CASCADE, related_name="violences_agresseur")
    victime = models.ForeignKey("Eleve", on_delete=models.CASCADE, related_name="violences_victime")

    forme_agression = models.TextField()
    cause_violence = models.TextField()
    dommage_corporel = models.TextField()
    moyens_resolution = models.TextField()

    date = models.DateField(default=timezone.localdate)

    cree_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.agresseur} -> {self.victime} ({self.date})"




class Degradation(models.Model):
    DECISIONS = (
        ("avertissement", "Avertissement"),
        ("convocation_parent", "Convocation des parents"),
        ("reparation", "Réparation / Remboursement"),
        ("travail_interet", "Travail d’intérêt général"),
        ("exclusion_temp", "Exclusion temporaire"),
        ("autre", "Autre (personnalisée)"),
    )

    eleve = models.ForeignKey("Eleve", on_delete=models.PROTECT, related_name="degradations")
    degradation_commise = models.TextField()
    decision_prise = models.CharField(max_length=40, choices=DECISIONS)
    decision_autre = models.CharField(max_length=255, blank=True)  # rempli si decision_prise == "autre"
    date = models.DateField(default=timezone.localdate)

    cree_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def decision_affichee(self) -> str:
        if self.decision_prise == "autre" and self.decision_autre:
            return self.decision_autre
        return self.get_decision_prise_display()

    def __str__(self):
        return f"{self.eleve} - {self.date}"



from django.db import models, transaction
from django.utils import timezone
from django.db.models import Max
from django.utils.translation import gettext_lazy as _


class Employe(models.Model):
    SEXE = (
        ("M", _("Masculin")),
        ("F", _("Féminin")),
    )

    FONCTIONS = (
        ("gardien", _("Gardien")),
        ("surveillant", _("Surveillant")),
        ("entretien", _("Agent d’entretien")),
        ("concierge", _("Concierge")),
        ("chauffeur", _("Chauffeur")),
        ("cuisinier", _("Cuisinier")),
        ("cantine", _("Cantinier / Cantine")),
        ("administratif", _("Agent administratif")),
        ("comptable", _("Comptable")),
        ("bibliothecaire", _("Bibliothécaire")),
        ("it", _("Technicien informatique")),
        ("electricien", _("Électricien")),
        ("plombier", _("Plombier")),
        ("autre", _("Autre")),
    )

    STATUT = (
        ("active", _("Active")),
        ("inactive", _("Inactive")),
    )

    ecole = models.ForeignKey(
        "Ecole",
        on_delete=models.CASCADE,
        related_name="employes",
        verbose_name=_("École"),
    )

    nom_complet = models.CharField(
        max_length=150,
        verbose_name=_("Nom complet"),
    )

    matricule = models.CharField(
        max_length=30,
        blank=True,
        editable=False,
        verbose_name=_("Matricule"),
    )

    sexe = models.CharField(
        max_length=1,
        choices=SEXE,
        default="M",
        verbose_name=_("Sexe"),
    )

    telephone = models.CharField(
        max_length=50,
        blank=True,
        default="",
        verbose_name=_("Téléphone"),
    )

    email = models.EmailField(
        blank=True,
        default="",
        verbose_name=_("Email"),
    )

    fonction = models.CharField(
        max_length=30,
        choices=FONCTIONS,
        verbose_name=_("Fonction"),
    )

    autre_fonction = models.CharField(
        max_length=120,
        blank=True,
        default="",
        verbose_name=_("Autre fonction"),
    )

    statut = models.CharField(
        max_length=10,
        choices=STATUT,
        default="active",
        verbose_name=_("Statut"),
    )

    bureau = models.CharField(
        max_length=120,
        blank=True,
        default="",
        verbose_name=_("Bureau"),
    )

    date_embauche = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Date d'embauche"),
    )

    working_hours = models.PositiveIntegerField(
        default=8,
        verbose_name=_("Heures de travail"),
    )

    date_creation = models.DateTimeField(
        default=timezone.now,
        verbose_name=_("Date de création"),
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["ecole", "matricule"],
                name="unique_matricule_par_ecole"
            )
        ]
        ordering = ["-date_creation"]
        verbose_name = _("Employé")
        verbose_name_plural = _("Employés")

    def __str__(self):
        return f"{self.nom_complet} ({self.matricule})"

    # ✅ AJOUT: génération matricule auto (EMP001-<ecole_id>)
    def _next_matricule(self) -> str:
        suffix = f"-{self.ecole_id}"

        last = (
            Employe.objects
            .filter(ecole_id=self.ecole_id, matricule__endswith=suffix)
            .aggregate(m=Max("matricule"))["m"]
        )

        if not last:
            return f"EMP001{suffix}"

        # last = "EMP012-2" => num = 12
        num_str = last.replace("EMP", "").replace(suffix, "")
        num = int(num_str)
        return f"EMP{num + 1:03d}{suffix}"

    # ✅ AJOUT: matricule créé une seule fois (à la création)
    def save(self, *args, **kwargs):
        # Si création (pas de pk encore) ET matricule vide ET ecole connue
        if not self.pk and not self.matricule and self.ecole_id:
            with transaction.atomic():
                # génère le matricule
                self.matricule = self._next_matricule()
                # sécurité: si jamais matricule vide (ne doit jamais arriver)
                if not self.matricule:
                    self.matricule = f"EMP001-{self.ecole_id}"

        super().save(*args, **kwargs)

# models.py
class EmployeAbsence(models.Model):
    STATUT_CHOICES = (
        ("present", "Présent"),
        ("absence", "Absence"),
        ("retard", "Retard"),
    )

    user = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="absences_employe_saisies"
    )

    employe = models.ForeignKey(
        "Employe",
        on_delete=models.CASCADE,
        related_name="absences"
    )

    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default="absence")
    date = models.DateField(default=timezone.localdate)

    h_debut = models.TimeField(null=True, blank=True)
    h_fin = models.TimeField(null=True, blank=True)

    motif = models.CharField(max_length=255, blank=True)
    justifiee = models.BooleanField(default=False)

    piece = models.FileField(upload_to="absences_employes/", null=True, blank=True)

    annee_scolaire = models.ForeignKey("AnneeScolaire", on_delete=models.CASCADE)
    ecole = models.ForeignKey("Ecole", on_delete=models.CASCADE, null=True, blank=True)

    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "employe__nom_complet"]
        constraints = [
            models.UniqueConstraint(
                fields=["employe", "date", "h_debut", "h_fin", "annee_scolaire", "ecole"],
                name="uniq_absence_employe_par_date_heure_ecole_annee"
            )
        ]

    def __str__(self):
        return f"{self.employe.nom_complet} | {self.date} | {self.get_statut_display()}"






class Batiment(models.Model):
    ecole = models.ForeignKey("Ecole", on_delete=models.CASCADE, related_name="batiments")

    nom = models.CharField(max_length=120)           # ex: Bâtiment A
    code = models.CharField(max_length=30, blank=True, default="")   # ex: A, B1...
    adresse = models.CharField(max_length=255, blank=True, default="")
    description = models.TextField(blank=True, default="")

    nb_etages = models.PositiveSmallIntegerField(default=0)
    actif = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nom", "id"]
        unique_together = [("ecole", "nom")]

    def __str__(self):
        return self.nom


class Salle(models.Model):
    ecole = models.ForeignKey("Ecole", on_delete=models.CASCADE, related_name="salles")
    batiment = models.ForeignKey("Batiment", on_delete=models.PROTECT, related_name="salles")

    nom = models.CharField(max_length=120)
    etage = models.PositiveSmallIntegerField(default=0)  # 0..(batiment.nb_etages-1)
    description = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["batiment__nom", "nom", "id"]
        unique_together = [("ecole", "batiment", "nom", "etage")]

    def __str__(self):
        return f"{self.nom} - {self.batiment} (étage {self.etage})"




























from django.db import models
from django.utils.translation import gettext_lazy as _


class ProgrammeOrientation(models.Model):
    code = models.CharField(
        max_length=30,
        verbose_name=_("Code"),
        help_text=_("Exemple : ES, S, L, GFM, OGRH, IAG")
    )
    libelle = models.CharField(
        max_length=120,
        blank=True,
        default="",
        verbose_name=_("Libellé")
    )
    ordre = models.PositiveIntegerField(
        default=1,
        verbose_name=_("Ordre")
    )
    actif = models.BooleanField(
        default=True,
        verbose_name=_("Actif")
    )

    ecole = models.ForeignKey(
        "Ecole",
        on_delete=models.CASCADE,
        related_name="programmes_orientation",
        verbose_name=_("École")
    )

    class Meta:
        ordering = ["ordre", "code"]
        verbose_name = _("Programme d'orientation")
        verbose_name_plural = _("Programmes d'orientation")
        constraints = [
            models.UniqueConstraint(
                fields=["ecole", "code"],
                name="uniq_programme_orientation_ecole_code"
            )
        ]

    def __str__(self):
        if self.libelle:
            return f"{self.code} - {self.libelle}"
        return self.code

    @property
    def nom_affichage(self):
        return self.code.strip().upper()
    




from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class OrientationScolaire(models.Model):
    niveau = models.ForeignKey(
        "Niveau",
        on_delete=models.PROTECT,
        related_name="orientations_scolaires",
        verbose_name=_("Niveau")
    )
    programmes = models.ManyToManyField(
        "ProgrammeOrientation",
        related_name="orientations_scolaires",
        blank=True,
        verbose_name=_("Programmes")
    )

    date_debut = models.DateField(verbose_name=_("Date de début"))
    date_fin = models.DateField(verbose_name=_("Date de fin"))

    annee_scolaire = models.ForeignKey(
        "AnneeScolaire",
        on_delete=models.CASCADE,
        verbose_name=_("Année scolaire")
    )
    ecole = models.ForeignKey(
        "Ecole",
        on_delete=models.CASCADE,
        verbose_name=_("École")
    )

    actif = models.BooleanField(default=True, verbose_name=_("Actif"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["niveau__ordre", "niveau__nom"]
        verbose_name = _("Orientation scolaire")
        verbose_name_plural = _("Orientations scolaires")
        constraints = [
            models.UniqueConstraint(
                fields=["ecole", "annee_scolaire", "niveau"],
                name="uniq_orientation_scolaire_ecole_annee_niveau"
            )
        ]

    def __str__(self):
        return f"{self.niveau} | {self.annee_scolaire}"

    def clean(self):
        if self.date_fin and self.date_debut and self.date_fin < self.date_debut:
            raise ValidationError(_("La date de fin doit être supérieure ou égale à la date de début."))

    @property
    def periode_validite(self):
        if self.date_debut and self.date_fin:
            return f"{self.date_debut:%Y-%m-%d} à {self.date_fin:%Y-%m-%d}"
        return ""

    def programmes_affichage(self):
        items = self.programmes.order_by("ordre", "code")
        return [f"{idx}. {p.nom_affichage}" for idx, p in enumerate(items, start=1)]
    



from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class VoeuOrientationEleve(models.Model):
    eleve = models.ForeignKey(
        "Eleve",
        on_delete=models.CASCADE,
        related_name="voeux_orientation",
        verbose_name=_("Élève")
    )
    orientation = models.ForeignKey(
        "OrientationScolaire",
        on_delete=models.CASCADE,
        related_name="voeux_eleves",
        verbose_name=_("Orientation scolaire")
    )

    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="voeux_orientation_crees",
        verbose_name=_("Créé par")
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Vœu d'orientation élève")
        verbose_name_plural = _("Vœux d'orientation élèves")
        ordering = ["eleve__nom"]
        constraints = [
            models.UniqueConstraint(
                fields=["eleve", "orientation"],
                name="uniq_voeu_orientation_par_eleve_orientation"
            )
        ]

    def __str__(self):
        return f"{self.eleve} | {self.orientation}"


class VoeuOrientationChoix(models.Model):
    voeu = models.ForeignKey(
        "VoeuOrientationEleve",
        on_delete=models.CASCADE,
        related_name="choix",
        verbose_name=_("Vœu")
    )
    programme = models.ForeignKey(
        "ProgrammeOrientation",
        on_delete=models.CASCADE,
        related_name="choix_voeux",
        verbose_name=_("Programme")
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Choix de vœu")
        verbose_name_plural = _("Choix de vœux")
        ordering = ["programme__ordre", "programme__code"]
        constraints = [
            models.UniqueConstraint(
                fields=["voeu", "programme"],
                name="uniq_choix_par_voeu_programme"
            )
        ]

    def __str__(self):
        return f"{self.voeu.eleve} | {self.programme.code}"


from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class OrientationFinaleEleve(models.Model):
    eleve = models.ForeignKey(
        "Eleve",
        on_delete=models.CASCADE,
        related_name="orientations_finales",
        verbose_name=_("Élève")
    )
    orientation = models.ForeignKey(
        "OrientationScolaire",
        on_delete=models.CASCADE,
        related_name="orientations_finales_eleves",
        verbose_name=_("Orientation scolaire")
    )
    programme_final = models.ForeignKey(
        "ProgrammeOrientation",
        on_delete=models.PROTECT,
        related_name="orientations_finales",
        verbose_name=_("Programme final")
    )

    remarque = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name=_("Remarque")
    )

    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orientations_finales_creees",
        verbose_name=_("Créé par")
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Orientation finale élève")
        verbose_name_plural = _("Orientations finales élèves")
        ordering = ["eleve__nom"]
        constraints = [
            models.UniqueConstraint(
                fields=["eleve", "orientation"],
                name="uniq_orientation_finale_par_eleve_orientation"
            )
        ]

    def __str__(self):
        return f"{self.eleve} -> {self.programme_final}"
    




from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class DecisionFinaleEleve(models.Model):
    eleve = models.ForeignKey(
        "Eleve",
        on_delete=models.CASCADE,
        related_name="decisions_finales",
        verbose_name=_("Élève")
    )
    orientation = models.ForeignKey(
        "OrientationScolaire",
        on_delete=models.CASCADE,
        related_name="decisions_finales_eleves",
        verbose_name=_("Orientation scolaire")
    )
    orientation_finale = models.ForeignKey(
        "OrientationFinaleEleve",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="decisions_administratives",
        verbose_name=_("Orientation finale")
    )
    decision = models.ForeignKey(
        "DecisionPromotion",
        on_delete=models.PROTECT,
        related_name="decisions_eleves",
        verbose_name=_("Décision")
    )

    moyenne_annuelle = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Moyenne annuelle")
    )

    remarque = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name=_("Remarque")
    )

    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="decisions_finales_creees",
        verbose_name=_("Créé par")
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Décision finale élève")
        verbose_name_plural = _("Décisions finales élèves")
        ordering = ["eleve__nom"]
        constraints = [
            models.UniqueConstraint(
                fields=["eleve", "orientation"],
                name="uniq_decision_finale_par_eleve_orientation"
            )
        ]

    def __str__(self):
        return f"{self.eleve} -> {self.decision}"