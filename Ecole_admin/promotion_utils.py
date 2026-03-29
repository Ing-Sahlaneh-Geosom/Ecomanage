from django.db.models import QuerySet

from .models import Classe, Niveau, PromotionDecisionCode, Specialite


def get_niveau_suivant(niveau):
    """
    Retourne le niveau suivant selon l'ordre du niveau.
    """
    if not niveau:
        return None

    return Niveau.objects.filter(
        ecole=niveau.ecole,
        actif=True,
        ordre__gt=niveau.ordre
    ).order_by("ordre", "nom").first()


def get_queryset_prochaine_classe(classe_actuelle, decision=None) -> QuerySet:
    """
    Retourne les classes possibles pour la promotion :
    - admis / autorise / oriente => classes du niveau suivant
    - redouble => classes du même niveau
    - diplome / exclu / attente => aucune classe
    """
    if not classe_actuelle or not classe_actuelle.niveau_id:
        return Classe.objects.none()

    if decision == PromotionDecisionCode.REDOUBLE:
        return Classe.objects.filter(
            ecole=classe_actuelle.ecole,
            niveau=classe_actuelle.niveau,
            actif=True
        ).order_by("ordre", "nom")

    if decision in [
        PromotionDecisionCode.ADMIS,
        PromotionDecisionCode.AUTORISE,
        PromotionDecisionCode.ORIENTE,
    ]:
        niveau_suivant = get_niveau_suivant(classe_actuelle.niveau)
        if not niveau_suivant:
            return Classe.objects.none()

        return Classe.objects.filter(
            ecole=classe_actuelle.ecole,
            niveau=niveau_suivant,
            actif=True
        ).order_by("ordre", "nom")

    return Classe.objects.none()


def get_prochaine_classe_par_defaut(classe_actuelle, decision=None):
    """
    Logique par défaut :
    - REDOUBLE => même classe
    - ADMIS / AUTORISE / ORIENTE =>
        1) même ordre dans le niveau suivant
        2) sinon première classe du niveau suivant
    """
    if not classe_actuelle or not classe_actuelle.niveau_id:
        return None

    if decision == PromotionDecisionCode.REDOUBLE:
        return classe_actuelle

    if decision in [
        PromotionDecisionCode.ADMIS,
        PromotionDecisionCode.AUTORISE,
        PromotionDecisionCode.ORIENTE,
    ]:
        niveau_suivant = get_niveau_suivant(classe_actuelle.niveau)
        if not niveau_suivant:
            return None

        # priorité : même ordre de classe
        meme_ordre = Classe.objects.filter(
            ecole=classe_actuelle.ecole,
            niveau=niveau_suivant,
            actif=True,
            ordre=classe_actuelle.ordre
        ).order_by("ordre", "nom").first()

        if meme_ordre:
            return meme_ordre

        # fallback : première classe du niveau suivant
        return Classe.objects.filter(
            ecole=classe_actuelle.ecole,
            niveau=niveau_suivant,
            actif=True
        ).order_by("ordre", "nom").first()

    return None


def classe_a_specialite_fixee(classe) -> bool:
    """
    La classe porte déjà une spécialité précise.
    Dans ce cas, pas besoin d'afficher un champ 'prochaine_specialite'.
    """
    return bool(classe and classe.specialite_id)


def classe_demande_choix_specialite(classe) -> bool:
    """
    On affiche le champ spécialité seulement si :
    - la classe existe
    - a_specialite=True
    - MAIS aucune spécialité n'est encore fixée sur la classe
    - et il existe des spécialités sur le niveau de cette classe
    """
    if not classe:
        return False

    if classe.specialite_id:
        return False

    if not classe.a_specialite:
        return False

    return Specialite.objects.filter(
        ecole=classe.ecole,
        niveau=classe.niveau
    ).exists()


def get_specialites_queryset_for_classe(classe):
    """
    Retourne les spécialités disponibles pour la classe cible,
    seulement si cette classe demande vraiment un choix de spécialité.
    """
    if not classe_demande_choix_specialite(classe):
        return Specialite.objects.none()

    return Specialite.objects.filter(
        ecole=classe.ecole,
        niveau=classe.niveau
    ).order_by("nom")