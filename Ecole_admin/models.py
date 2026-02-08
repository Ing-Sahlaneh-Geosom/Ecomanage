from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Choices
from django.utils import timezone
from django.urls import reverse
from django.conf import settings
from django.db import  transaction
from datetime import timedelta



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
        ('admin', 'Administrateur'),
        ('secretaire', 'Secrétaire'),
        ('parent', 'Parent'),
        ('proffesseur', 'Professeur'),
    )
    SEXE = (
        ('M','musculin'),
        ('F','feminin'),
    )

    nom_complet = models.CharField(max_length=120, blank=True, default="")
    sexe = models.CharField(max_length=1, choices=SEXE, default='M')
    date_naissance = models.DateField( default=timezone.now)
    Pays = models.CharField(max_length=50 , default='Djibouti')
    Ville = models.CharField(max_length=12, default='Djibouti')
    Adresse = models.CharField(max_length=100 , default='Adresse inconue')
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
        unique=True
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
        null=True, blank=True
    )

    actif = models.BooleanField(default=True)

    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('nom', 'ecole')
        ordering = ['niveau', 'nom']

    def __str__(self):
        return f"{self.nom} - {self.niveau}"


    def get_absolute_url(self):
        return reverse('Detaille_d_une_classe' , kwargs={"pk": self.id})






from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

class Eleve(models.Model):
    
    SEXE = (('M', _('musculin')), ('F', _('feminin')))
    STATUS = (
        ("ADMIS", _("Admis")),
        ("REDOUBLE", _("Redouble")),
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
    status = models.CharField(max_length=120,choices=STATUS)


    
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
        ('M', 'musculin'),
        ('F', 'feminin'),
    )
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
    status = models.CharField(max_length=20, choices=[
        ('Permanent','Permanent'),
        ('Vacataire','Vacataire'),
        ('Stagiaire','Stagiaire')
    ], default='Permanent')
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
    ESPECES = "especes", "Espèces"
    CHEQUE = "cheque", "Chèque"
    VIREMENT = "virement", "Virement"
    MOBILE = "mobile", "Mobile money"

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
        ("valide", "Validé"),
        ("annule", "Annulé"),
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

    mode = models.CharField(max_length=20, default="especes")
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
        ("admis", "Admis"),
        ("redouble", "Redouble"),
        ("autorise", "Autorisé(e)"),
        ("exclu", "Exclu"),
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
        ("R", "Redouble"),
        ("F", "Admis"),
        ("A", "Autorisé(e)"),
        ("E", "Exclu(e)"),
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




from django.db import models , transaction
from django.utils import timezone
from django.db.models import Max

class Employe(models.Model):
    SEXE = (
        ("M", "Masculin"),
        ("F", "Féminin"),
    )

    FONCTIONS = (
        ("gardien", "Gardien"),
        ("surveillant", "Surveillant"),
        ("entretien", "Agent d’entretien"),
        ("concierge", "Concierge"),
        ("chauffeur", "Chauffeur"),
        ("cuisinier", "Cuisinier"),
        ("cantine", "Cantinier / Cantine"),
        ("administratif", "Agent administratif"),
        ("comptable", "Comptable"),
        ("bibliothecaire", "Bibliothécaire"),
        ("it", "Technicien informatique"),
        ("electricien", "Électricien"),
        ("plombier", "Plombier"),
        ("autre", "Autre"),
    )

    STATUT = (
        ("active", "Active"),
        ("inactive", "Inactive"),
    )

    ecole = models.ForeignKey("Ecole", on_delete=models.CASCADE, related_name="employes")

    # champs nécessaires
    nom_complet = models.CharField(max_length=150)
    matricule = models.CharField(
        max_length=30,
        blank=True,
        editable=False
    )
    sexe = models.CharField(max_length=1, choices=SEXE, default="M")

    telephone = models.CharField(max_length=50, blank=True, default="")
    email = models.EmailField(blank=True, default="")

    fonction = models.CharField(max_length=30, choices=FONCTIONS)
    autre_fonction = models.CharField(max_length=120, blank=True, default="")

    statut = models.CharField(max_length=10, choices=STATUT, default="active")

    # optionnels (si tu veux)
    bureau = models.CharField(max_length=120, blank=True, default="")
    date_embauche = models.DateField(null=True, blank=True)
    working_hours = models.PositiveIntegerField(default=8)

    date_creation = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["ecole", "matricule"],
                name="unique_matricule_par_ecole"
            )
        ]
        ordering = ["-date_creation"]

    def __str__(self):
        return f"{self.nom_complet} ({self.get_fonction_display()})"

    def _next_matricule(self) -> str:
        """
        Génère EMP001-<ecole_id>
        """
        suffix = f"-{self.ecole_id}"

        last = (
            Employe.objects
            .filter(ecole=self.ecole, matricule__endswith=suffix)
            .aggregate(m=Max("matricule"))["m"]
        )

        if not last:
            return f"EMP001{suffix}"
            num = int(last.replace("EMP", "").replace(suffix, ""))
            return f"EMP{num + 1:03d}{suffix}"

    def save(self, *args, **kwargs):
        if not self.matricule and self.ecole_id:
            with transaction.atomic():
                self.matricule = self._next_matricule()
                super().save(*args, **kwargs)
                return
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nom_complet} ({self.matricule})"
    




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

