from .utils import get_annee_active
from ..models import AnneeScolaire , Message


def annee_context(request):
    return {
        'annees': AnneeScolaire.objects.all(),
        'annee_active': get_annee_active(request)
    }


# Ecole_admin/utils/context_processors.py
from django.utils.timezone import localtime
from django.urls import reverse



def notifications_context(request):
    """
    Variables globales pour base.html:
    - notif_count: nombre messages NON LUS
    - notifications: liste (max 4) non lus
    """
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {"notif_count": 0, "notifications": []}

    ecole = getattr(user, "ecole", None)
    if not ecole:
        return {"notif_count": 0, "notifications": []}

    try:
        annee = get_annee_active(request)
    except Exception:
        return {"notif_count": 0, "notifications": []}

    qs = Message.objects.filter(
        receiver=user,
        ecole=ecole,
        annee_scolaire=annee,
        lu=False,
        deleted_by_receiver=False
    ).order_by("-date_envoi")

    notif_count = qs.count()

    notifications = []
    for m in qs[:4]:
        notifications.append({
            "id": m.id,
            "titre": m.sujet,
            "message": (m.contenu[:55] + "…") if len(m.contenu) > 55 else m.contenu,
            "date": localtime(m.date_envoi).strftime("%d/%m/%Y %H:%M"),
            "url": reverse("messagerie_home") + f"?open={m.id}",
        })

    return {"notif_count": notif_count, "notifications": notifications}
