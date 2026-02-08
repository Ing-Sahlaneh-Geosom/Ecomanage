from decimal import Decimal, InvalidOperation
from django.db.models import Sum

from Ecole_admin.models import Note, Matier, Eleve

# ✅ Essayer d'importer Absence depuis plusieurs endroits (selon ton projet)
Absence = None
for path in [
    ".models",                # si Absence est dans Note/models.py
    "Ecole_admin.models",     # si Absence est dans Ecole_admin
    "Absence_admin.models",   # si tu as une app Absence_admin
    "Presence_admin.models",  # parfois nommé presence
]:
    try:
        mod = __import__(path, fromlist=["Absence"])
        Absence = getattr(mod, "Absence", None)
        if Absence:
            break
    except Exception:
        pass


def D(x, default="0"):
    try:
        return Decimal(str(x))
    except Exception:
        return Decimal(default)


def moyenne_matiere_eleve(eleve, matiere, periode, annee, ecole):
    qs = Note.objects.filter(
        ecole=ecole,
        annee_scolaire=annee,
        eleve=eleve,
        matiere=matiere,
        devoir__periode=periode
    )

    total_coef = qs.aggregate(s=Sum("coefficient"))["s"] or 0
    total_coef = D(total_coef, "0")

    total_points = Decimal("0")
    for n in qs:
        total_points += D(n.note) * D(n.coefficient)

    if total_coef <= 0:
        return None

    try:
        return (total_points / total_coef).quantize(Decimal("0.01"))
    except InvalidOperation:
        return (total_points / total_coef)


def _get_time(obj, names):
    """Retourne le 1er champ existant parmi names."""
    for n in names:
        if hasattr(obj, n) and getattr(obj, n) is not None:
            return getattr(obj, n)
    return None


def compute_absence_hours(eleve, periode, annee, ecole):
    """
    Calcule heures d'absence :
    - supporte plusieurs noms de champs (h_debut/h_fin, heure_debut/heure_fin, etc.)
    - si pas d'heure, compte 1h par ligne (fallback)
    """
    if Absence is None:
        return Decimal("0.00")

    # ✅ filtres possibles selon ton modèle Absence
    qs = Absence.objects.all()

    # champs habituels : ecole / annee_scolaire / eleve
    if hasattr(Absence, "ecole_id"):
        qs = qs.filter(ecole=ecole)
    if hasattr(Absence, "annee_scolaire_id"):
        qs = qs.filter(annee_scolaire=annee)
    if hasattr(Absence, "eleve_id"):
        qs = qs.filter(eleve=eleve)

    # champs date
    if hasattr(Absence, "date"):
        qs = qs.filter(date__gte=periode.debut, date__lte=periode.fin)
    elif hasattr(Absence, "jour"):
        qs = qs.filter(jour__gte=periode.debut, jour__lte=periode.fin)

    total = Decimal("0")

    for a in qs:
        hd = _get_time(a, ["h_debut", "heure_debut", "debut", "time_start"])
        hf = _get_time(a, ["h_fin", "heure_fin", "fin", "time_end"])

        if hd and hf and hasattr(hd, "hour") and hasattr(hf, "hour"):
            delta = (hf.hour + hf.minute / 60) - (hd.hour + hd.minute / 60)
            if delta < 0:
                delta = 0
            total += D(delta)
        else:
            # fallback : 1 heure par absence si pas d'heure
            total += Decimal("1")

    try:
        return total.quantize(Decimal("0.01"))
    except InvalidOperation:
        return total


def appreciation_from_moyenne(m):
    m = D(m, "0")
    if m >= 16:
        return "Très bien"
    if m >= 14:
        return "Bien"
    if m >= 12:
        return "Assez bien"
    if m >= 10:
        return "Passable"
    return "Insuffisant"


def build_rapport_classe(classe, periode, annee, ecole):
    subjects = list(Matier.objects.filter(classe=classe).order_by("nom"))
    eleves = list(Eleve.objects.filter(ecole=ecole, annee_scolaire=annee, classe=classe).order_by("nom"))

    rows = []
    for e in eleves:
        notes_list = []
        total = Decimal("0")
        nb = 0

        for m in subjects:
            val = moyenne_matiere_eleve(e, m, periode, annee, ecole)
            notes_list.append(val)
            if val is not None:
                total += D(val)
                nb += 1

        moyenne = (total / nb).quantize(Decimal("0.01")) if nb > 0 else Decimal("0.00")

        # ✅ SEXE (supporte sex / sexe)
        sexe_val = getattr(e, "Sexe", None)
        if sexe_val is None:
            sexe_val = getattr(e, "Sexe", None)
        sexe_display = sexe_val if sexe_val else "-"

        # ✅ STATUS (ton champ: status avec choices)
        status_display = "-"
        if hasattr(e, "get_status_display"):
            status_display = e.get_status_display()
        elif getattr(e, "status", None):
            status_display = str(e.status)

        abs_h = compute_absence_hours(e, periode, annee, ecole)
        app = appreciation_from_moyenne(moyenne)

        rows.append({
            "eleve": e,
            "sexe": sexe_display,
            "status": status_display,
            "notes_list": notes_list,
            "total": total.quantize(Decimal("0.01")),
            "nb": nb,
            "moyenne": moyenne,
            "absences": abs_h,
            "appreciation": app,
        })

    # Tri moyenne desc + rang
    rows.sort(key=lambda r: r["moyenne"], reverse=True)
    for i, r in enumerate(rows, start=1):
        r["rang"] = i

    return {"subjects": subjects, "rows": rows}
