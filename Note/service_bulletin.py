from decimal import Decimal
from django.db.models import Avg, Sum, Count, Q
from Ecole_admin.models import Note, DispenseMatiere, Matier, Proffeseur, Absence
from decimal import Decimal, InvalidOperation

def appreciation_from_avg(avg: Decimal) -> str:
    try:
        a = Decimal(avg)
    except Exception:
        return ""
    if a >= 16:
        return "Très bien"
    if a >= 14:
        return "Bien"
    if a >= 12:
        return "Assez bien"
    if a >= 10:
        return "Passable"
    if a >= 8:
        return "Insuffisant"
    return "Très insuffisant"

def compute_student_subject_avg(eleve, matiere, periode, annee, ecole):
    qs = Note.objects.filter(
        eleve=eleve, matiere=matiere, ecole=ecole, annee_scolaire=annee,
        devoir__periode=periode
    )
    total_coef = qs.aggregate(s=Sum("coefficient"))["s"] or 0
    total_coef = Decimal(str(total_coef)) if total_coef else Decimal("0")

    total_points = Decimal("0")
    for n in qs:
        total_points += Decimal(str(n.note)) * Decimal(str(n.coefficient))

    avg = (total_points / total_coef) if total_coef > 0 else None
    nb = qs.aggregate(c=Count("id"))["c"] or 0
    return avg, nb, total_points, total_coef

def compute_class_subject_avg(classe, matiere, periode, annee, ecole):
    qs = Note.objects.filter(
        eleve__classe=classe, matiere=matiere, ecole=ecole, annee_scolaire=annee,
        devoir__periode=periode
    )
    # moyenne pondérée globale classe
    # (somme(note*coef)) / somme(coef)
    total_coef = qs.aggregate(s=Sum("coefficient"))["s"] or 0
    total_coef = Decimal(str(total_coef)) if total_coef else Decimal("0")

    total_points = Decimal("0")
    for n in qs:
        total_points += Decimal(str(n.note)) * Decimal(str(n.coefficient))

    avg = (total_points / total_coef) if total_coef > 0 else None
    return avg

def compute_rank_in_class_for_subject(classe, matiere, periode, annee, ecole, target_eleve):
    """
    Rang de l'élève dans la classe pour une matière (basé sur moyenne pondérée).
    """
    # élèves de la classe
    eleves = classe.eleves.filter(ecole=ecole, annee_scolaire=annee).all()

    scores = []
    for e in eleves:
        avg, nb, _, _ = compute_student_subject_avg(e, matiere, periode, annee, ecole)
        if avg is not None:
            scores.append((e.id, avg))

    scores.sort(key=lambda x: x[1], reverse=True)  # desc
    for idx, (eid, _) in enumerate(scores, start=1):
        if eid == target_eleve.id:
            return idx, len(scores)
    return None, len(scores)

def get_teacher_name_for_subject(classe, matiere, ecole):
    # selon ton modèle: Proffeseur.matieres = FK Matier + Proffeseur.classes = M2M Classe
    prof = Proffeseur.objects.filter(ecole=ecole, actif=True, matieres=matiere, classes=classe).first()
    return prof.nom_conplet if prof else ""

def compute_absence_hours(eleve, periode, annee, ecole):
    qs = Absence.objects.filter(
        eleve=eleve, ecole=ecole, annee_scolaire=annee,
        date__gte=periode.debut, date__lte=periode.fin,
        statut__in=["absence", "retard"]
    )
    total = Decimal("0")
    for a in qs:
        if a.h_debut and a.h_fin:
            delta = (a.h_fin.hour + a.h_fin.minute/60) - (a.h_debut.hour + a.h_debut.minute/60)
            if delta < 0:
                delta = 0
            total += Decimal(str(delta))
        else:
            total += Decimal("1")
    return total

def build_bulletin(eleve, classe, periode, annee, ecole):
    matieres = Matier.objects.filter(classe=classe).order_by("nom")

    dispenses = {
        d.matiere_id: d
        for d in DispenseMatiere.objects.filter(
            eleve=eleve, periode=periode, annee_scolaire=annee, ecole=ecole
        )
    }

    lignes = []
    somme_points = Decimal("0")
    somme_coef = Decimal("0")

    for m in matieres:
        if m.id in dispenses:
            lignes.append({
                "matiere": m.nom,
                "enseignant": get_teacher_name_for_subject(classe, m, ecole),
                "nb_note": 0,
                "rang": "-",
                "moy_eleve": "Disp",
                "moy_classe": "-",
                "appreciation": "",
            })
            continue

        avg_eleve, nb, total_points, total_coef = compute_student_subject_avg(eleve, m, periode, annee, ecole)
        avg_classe = compute_class_subject_avg(classe, m, periode, annee, ecole)
        rang, total_rang = compute_rank_in_class_for_subject(classe, m, periode, annee, ecole, eleve)

        if avg_eleve is None:
            moy_eleve = "-"
            app = ""
        else:
            moy_eleve = f"{avg_eleve.quantize(Decimal('0.01'))}"
            app = appreciation_from_avg(avg_eleve)

            # moyenne générale pondérée
            somme_points += (total_points if total_points else Decimal("0"))
            somme_coef += (total_coef if total_coef else Decimal("0"))

        moy_classe = "-"
        if avg_classe is not None:
            moy_classe = f"{avg_classe.quantize(Decimal('0.01'))}"

        lignes.append({
            "matiere": m.nom,
            "enseignant": get_teacher_name_for_subject(classe, m, ecole),
            "nb_note": nb,
            "rang": f"{rang} ème" if rang else "-",
            "moy_eleve": moy_eleve,
            "moy_classe": moy_classe,
            "appreciation": app,
        })

    moy_gen = (somme_points / somme_coef) if somme_coef > 0 else Decimal("0")
    appr_global = appreciation_from_avg(moy_gen)

    abs_h = compute_absence_hours(eleve, periode, annee, ecole)

    try:
        abs_h_display = abs_h.quantize(Decimal("0.01"))  # ✅ OK
    except InvalidOperation:
        abs_h_display = abs_h

    return {
        "lignes": lignes,
        "moyenne_generale": moy_gen.quantize(Decimal("0.01")),
        "appreciation_globale": appr_global,
        "absences_heures": abs_h_display,
    }
