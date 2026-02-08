from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.hashers import make_password

from .models import Proffeseur, User  # adapte import
from .utils import build_username, unique_username

@receiver(post_save, sender=Proffeseur)
def create_user_for_prof(sender, instance: Proffeseur, created, **kwargs):
    if instance.user_id:
        return

    # si pas de téléphone, impossible de faire login
    tel = (instance.telephone or "").strip()
    if not tel:
        return

    base = build_username(instance.nom_conplet, "@Prof")  # ex: ahmed@prof
    username = unique_username(User, base)

    # email fallback si vide
    email = (instance.email or "").strip() or f"{username}@local.prof"

    u = User.objects.create(
        username=username,
        email=email,
        nom_complet=instance.nom_conplet,
        num_tel=tel,
        role="proffesseur",
        ecole=instance.ecole,
        password=make_password(tel),  # ✅ mdp = téléphone
    )

    instance.user = u
    instance.save(update_fields=["user"])




from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.hashers import make_password
from django.db import transaction

from .models import Eleve, User
from .utils import build_username, unique_username

@receiver(post_save, sender=Eleve)
def create_user_for_parent(sender, instance: Eleve, created, **kwargs):
    # si déjà lié -> rien
    if instance.parent_user_id:
        return

    tel = (instance.telephone_parent or "").strip()
    nom_parent = (instance.parent or "").strip()
    if not tel or not nom_parent:
        return

    # username basé sur nom parent
    base = build_username(nom_parent, "@Parent")  # ex: ali@parent
    username = unique_username(User, base)

    email = (instance.email_parent or "").strip() or f"{username}@local.parent"

    # si un parent user existe déjà avec le même téléphone dans la même école, on le réutilise
    existing = User.objects.filter(ecole=instance.ecole, role="parent", num_tel=tel).first()
    if existing:
        instance.parent_user = existing
        instance.save(update_fields=["parent_user"])
        return

    with transaction.atomic():
        u = User.objects.create(
            username=username,
            email=email,
            nom_complet=nom_parent,
            num_tel=tel,
            role="parent",
            ecole=instance.ecole,
            password=make_password(tel),  # ✅ mdp = téléphone
        )
        instance.parent_user = u
        instance.save(update_fields=["parent_user"])
