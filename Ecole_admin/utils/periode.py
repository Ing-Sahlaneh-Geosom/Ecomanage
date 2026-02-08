from django.utils import timezone
from Ecole_admin.models import PeriodeScolaire, CloturePeriode

def is_periode_closed(ecole, annee, periode: PeriodeScolaire) -> bool:
    return CloturePeriode.objects.filter(
        ecole=ecole, annee_scolaire=annee,
        periode_scolaire=periode, cloturee=True
    ).exists()

def is_periode_expired(periode: PeriodeScolaire) -> bool:
    today = timezone.localdate()
    return today > periode.fin_effective

def is_periode_usable(ecole, annee, periode: PeriodeScolaire) -> bool:
    """
    Utilisable = pas clôturée ET pas expirée (fin_effective)
    """
    if is_periode_closed(ecole, annee, periode):
        return False
    if is_periode_expired(periode):
        return False
    return True

def is_periode_allowed_for_actions(ecole, annee, periode: PeriodeScolaire) -> bool:
    """
    Pour actions (devoir/saisie/dispense):
    - doit être UTILISABLE
    - ET doit être ACTIVE (ton besoin)
    """
    if not periode.est_active:
        return False
    return is_periode_usable(ecole, annee, periode)

def sync_periodes_auto(ecole, annee):
    """
    Auto:
    - si clôturée OU expirée => est_active=False (désactivation automatique)
    """
    periodes = PeriodeScolaire.objects.filter(ecole=ecole, annee_scolaire=annee)
    for p in periodes:
        if not is_periode_usable(ecole, annee, p):
            if p.est_active:
                p.est_active = False
                p.save(update_fields=["est_active"])
