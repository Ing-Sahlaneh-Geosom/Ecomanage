from decimal import Decimal
from django.db.models import Avg, Sum, F
from Ecole_admin.models import Note, DispenseMatiere, Matier


def _safe_decimal(x, default="0"):
    try:
        return Decimal(str(x))
    except Exception:
        return Decimal(default)


def compute_bulletin(eleve, periode, annee_scolaire, ecole):
    """
    Retourne:
      - lignes: [{matiere, moyenne, coef, total_points, total_coef, est_dispense, note_affichage}]
      - moyenne_generale, total_coef
    """
    # Notes liées à un devoir de la période choisie (recommandé car Devoir a periode)
    notes_qs = (
        Note.objects
        .filter(eleve=eleve, annee_scolaire=annee_scolaire, ecole=ecole)
        .select_related("matiere", "devoir", "devoir__periode")
    )
    notes_qs = notes_qs.filter(devoir__periode=periode)

    dispenses = {
        (d.matiere_id): d
        for d in DispenseMatiere.objects.filter(
            eleve=eleve, periode=periode, annee_scolaire=annee_scolaire, ecole=ecole
        ).select_related("matiere")
    }

    # matières de la classe
    matieres = Matier.objects.filter(classe=eleve.classe)
    lignes = []

    somme_points = Decimal("0")
    somme_coef = Decimal("0")

    for m in matieres:
        disp = dispenses.get(m.id)

        if disp:
            lignes.append({
                "matiere": m.nom,
                "moyenne": None,
                "coef": None,
                "total_points": None,
                "total_coef": None,
                "est_dispense": True,
                "note_affichage": disp.valeur or "Disp",
            })
            continue

        m_notes = notes_qs.filter(matiere=m)

        if not m_notes.exists():
            lignes.append({
                "matiere": m.nom,
                "moyenne": None,
                "coef": None,
                "total_points": None,
                "total_coef": None,
                "est_dispense": False,
                "note_affichage": "-",
            })
            continue

        # moyenne pondérée: sum(note * coef) / sum(coef)
        total_coef = m_notes.aggregate(s=Sum("coefficient"))["s"] or 0
        total_coef = _safe_decimal(total_coef, "0")

        total_points = Decimal("0")
        for n in m_notes:
            total_points += _safe_decimal(n.note) * _safe_decimal(n.coefficient)

        moyenne = (total_points / total_coef) if total_coef > 0 else Decimal("0")

        lignes.append({
            "matiere": m.nom,
            "moyenne": moyenne.quantize(Decimal("0.01")),
            "coef": total_coef,
            "total_points": total_points.quantize(Decimal("0.01")),
            "total_coef": total_coef,
            "est_dispense": False,
            "note_affichage": str(moyenne.quantize(Decimal("0.01"))),
        })

        somme_points += total_points
        somme_coef += total_coef

    moyenne_generale = (somme_points / somme_coef) if somme_coef > 0 else Decimal("0")

    return {
        "lignes": lignes,
        "moyenne_generale": moyenne_generale.quantize(Decimal("0.01")),
        "total_coef": somme_coef,
    }
