import json
from datetime import datetime, date

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q
from django.db.models.functions import ExtractMonth
from django.shortcuts import render

from Ecole_admin.models import (
    Absence,
    Batiment,
    Classe,
    ConvocationParent,
    Degradation,
    Eleve,
    Employe,
    EmployeAbsence,
    EmploiDuTemps,
    Message,
    Niveau,
    Note,
    Paiment,
    Proffeseur,
    ProfesseurAbsence,
    RecuCaisse,
    Salle,
    User,
    Violence,
)
from Ecole_admin.utils.utils import get_annee_active


@login_required(login_url="Connection")
def page_acceuil(request):
    user = request.user
    ecole = user.ecole
    annee_scolaire = get_annee_active(request)
    role = (user.role or "").lower().strip()

    # =========================
    # ✅ PARENT DASHBOARD
    # =========================
    if role == "parent":
        enfants = (
            Eleve.objects.filter(
                parent_user=user,
                ecole=ecole,
                annee_scolaire=annee_scolaire,
            )
            .select_related("classe")
            .order_by("nom")
        )

        absences = (
            Absence.objects.filter(
                eleve__in=enfants,
                ecole=ecole,
                annee_scolaire=annee_scolaire,
                statut="absence",
            )
            .select_related("eleve")
            .order_by("-date")[:8]
        )

        paiements = (
            Paiment.objects.filter(
                eleve__in=enfants,
                ecole=ecole,
                annee_scolaire=annee_scolaire,
            )
            .select_related("eleve", "type_paiement")
            .order_by("-date_paiement")[:8]
        )

        notes = (
            Note.objects.filter(
                eleve__in=enfants,
                ecole=ecole,
                annee_scolaire=annee_scolaire,
            )
            .select_related("eleve", "matiere")
            .order_by("-id")[:8]
        )

        context = {
            "mode": "parent",
            "enfants": enfants,
            "apsences": absences,
            "paiements": paiements,
            "notes": notes,
            "total_enfants": enfants.count(),
            "total_absences_parent": absences.count(),
        }
        return render(request, "home_page.html", context)

    # =========================
    # ✅ PROF DASHBOARD
    # =========================
    if role == "proffesseur":
        prof = getattr(user, "profil_prof", None)

        classes = Classe.objects.none()
        eleves = Eleve.objects.none()
        emplois = EmploiDuTemps.objects.none()
        total_heures = 0

        if prof:
            classes = (
                Classe.objects.filter(professeurs=prof, ecole=ecole)
                .select_related("niveau")
                .distinct()
            )
            eleves = (
                Eleve.objects.filter(
                    classe__in=classes,
                    ecole=ecole,
                    annee_scolaire=annee_scolaire,
                )
                .select_related("classe")
                .distinct()
            )
            emplois = EmploiDuTemps.objects.filter(
                professeur=prof,
                ecole=ecole,
                annee_scolaire=annee_scolaire,
            ).select_related("classe", "matiere", "salle")

            total_heures = sum(
                (
                    datetime.combine(date.min, item.heure_fin)
                    - datetime.combine(date.min, item.heure_debut)
                ).seconds
                / 3600
                for item in emplois
            )

        context = {
            "mode": "Prof",
            "classes": classes,
            "eleves": eleves,
            "emplois_prof": emplois[:8],
            "total_classes_prof": classes.count(),
            "total_eleves_prof": eleves.count(),
            "total_heures_prof": round(total_heures, 1),
        }
        return render(request, "home_page.html", context)

    # =========================
    # ✅ ADMIN / SECRETAIRE DASHBOARD
    # =========================
    if role in ["admin", "secretaire"]:
        annee_actuelle = datetime.now().year
        mois_noms = [
            "janv",
            "févr",
            "mars",
            "avr",
            "mai",
            "juin",
            "juil",
            "août",
            "sept",
            "oct",
            "nov",
            "déc",
        ]

        absences_agregees = (
            Absence.objects.filter(
                ecole=ecole,
                annee_scolaire=annee_scolaire,
                statut="absence",
                date__year=annee_actuelle,
            )
            .annotate(month=ExtractMonth("date"))
            .values("month")
            .annotate(total=Count("id"))
            .order_by("month")
        )

        paiements_agreges = (
            RecuCaisse.objects.filter(
                ecole=ecole,
                annee_scolaire=annee_scolaire,
                statut="valide",
                date_operation__year=annee_actuelle,
            )
            .annotate(month=ExtractMonth("date_operation"))
            .values("month")
            .annotate(total=Sum("total"))
            .order_by("month")
        )

        absence_map = {item["month"]: int(item["total"] or 0) for item in absences_agregees}
        paiement_map = {item["month"]: float(item["total"] or 0) for item in paiements_agreges}

        totaux_abs = [absence_map.get(index, 0) for index in range(1, 13)]
        totaux_paie = [paiement_map.get(index, 0) for index in range(1, 13)]

        eleves = Eleve.objects.filter(ecole=ecole, annee_scolaire=annee_scolaire)
        utilisateurs = User.objects.filter(ecole=ecole)
        classes = Classe.objects.filter(ecole=ecole, actif=True)
        niveaux = Niveau.objects.filter(ecole=ecole, actif=True)

        effectif_par_classe_qs = (
            Classe.objects.filter(ecole=ecole, actif=True)
            .annotate(
                total_eleves=Count(
                    "eleves",
                    filter=Q(eleves__annee_scolaire=annee_scolaire, eleves__ecole=ecole),
                )
            )
            .order_by("-total_eleves", "nom")[:10]
        )
        classes_labels = [item.nom for item in effectif_par_classe_qs]
        classes_effectifs = [item.total_eleves for item in effectif_par_classe_qs]
        professeurs = Proffeseur.objects.filter(ecole=ecole, actif=True)
        employes = Employe.objects.filter(ecole=ecole, statut="active")
        batiments = Batiment.objects.filter(ecole=ecole, actif=True)
        salles = Salle.objects.filter(ecole=ecole)

        total_montant = (
            RecuCaisse.objects.filter(
                ecole=ecole,
                annee_scolaire=annee_scolaire,
                statut="valide",
            ).aggregate(total=Sum("total"))["total"]
            or 0
        )

        absences_recentes = (
            Absence.objects.filter(
                ecole=ecole,
                annee_scolaire=annee_scolaire,
                statut="absence",
            )
            .select_related("eleve", "eleve__classe")
            .order_by("-date", "-date_creation")[:5]
        )

        paiements_recents = (
            RecuCaisse.objects.filter(
                ecole=ecole,
                annee_scolaire=annee_scolaire,
                statut="valide",
            )
            .select_related("eleve")
            .order_by("-date_operation")[:5]
        )

        utilisateurs_recents = (
            utilisateurs.exclude(last_login__isnull=True)
            .order_by("-last_login")[:5]
        )

        total_parents = utilisateurs.filter(role="parent").count()
        total_messages = Message.objects.filter(ecole=ecole, annee_scolaire=annee_scolaire).count()
        total_convocations = ConvocationParent.objects.filter(ecole=ecole, annee_scolaire=annee_scolaire).count()
        total_violences = Violence.objects.filter(date__year=annee_actuelle).count()
        total_degradations = Degradation.objects.filter(date__year=annee_actuelle).count()
        total_abs_prof = ProfesseurAbsence.objects.filter(
            ecole=ecole,
            annee_scolaire=annee_scolaire,
            statut="absence",
            date__year=annee_actuelle,
        ).count()
        total_abs_employes = EmployeAbsence.objects.filter(
            ecole=ecole,
            annee_scolaire=annee_scolaire,
            statut="absence",
            date__year=annee_actuelle,
        ).count()

        context = {
            "mode": "admin",
            "mois_abs": json.dumps(mois_noms, ensure_ascii=False),
            "totaux_abs": json.dumps(totaux_abs),
            "totaux_paie": json.dumps(totaux_paie),
            "eleves": eleves,
            "utilisateur": utilisateurs,
            "total_eleves": eleves.count(),
            "Total_montant": total_montant,
            "paiments_recents": paiements_recents,
            "absenceRecent": absences_recentes,
            "users_recents": utilisateurs_recents,
            "total_classes": classes.count(),
            "total_professeurs": professeurs.count(),
            "total_parents": total_parents,
            "total_niveaux": niveaux.count(),
            "total_employes": employes.count(),
            "total_messages": total_messages,
            "total_convocations": total_convocations,
            "total_violences": total_violences,
            "total_degradations": total_degradations,
            "total_abs_prof": total_abs_prof,
            "total_abs_employes": total_abs_employes,
            "total_batiments": batiments.count(),
            "total_salles": salles.count(),
            "classes_labels": json.dumps(classes_labels, ensure_ascii=False),
            "classes_effectifs": json.dumps(classes_effectifs),
        }
        return render(request, "home_page.html", context)

    # =========================
    # ✅ DEFAULT
    # =========================
    return render(request, "home_page.html", {"mode": "user"})



# from django.http import HttpResponse
# from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
# from reportlab.lib.pagesizes import A4
# from reportlab.lib import colors
# from reportlab.lib.styles import getSampleStyleSheet
# from reportlab.lib.units import cm


# def bulletin_pdf(request, eleve_id):
#     eleve = Eleve.objects.get(pk=eleve_id)
#     notes = eleve.note_set.all()

#     # Réponse HTTP
#     response = HttpResponse(content_type='application/pdf')
#     response['Content-Disposition'] = f'attachment; filename="bulletin_{eleve.nom}_{eleve.prenom}.pdf"'

#     # Document PDF
#     doc = SimpleDocTemplate(response, pagesize=A4)
#     elements = []

#     styles = getSampleStyleSheet()
#     title_style = styles["Title"]
#     normal_style = styles["Normal"]

#     # --- Logo ---
#     try:
#         logo = Image("static/images/logo.png", width=3*cm, height=3*cm)  # adapte le chemin
#         logo.hAlign = "LEFT"
#         elements.append(logo)
#     except:
#         elements.append(Paragraph("École Privée XYZ", styles["Heading2"]))
#     elements.append(Spacer(1, 10))

#     # --- Titre ---
#     elements.append(Paragraph("Bulletin Scolaire", title_style))
#     elements.append(Spacer(1, 20))

#     # --- Infos élève ---
#     elements.append(Paragraph(f"<b>Nom :</b> {eleve.nom}", normal_style))
#     elements.append(Paragraph(f"<b>Prénom :</b> {eleve.prenom}", normal_style))
#     elements.append(Spacer(1, 20))

#     # --- Tableau des notes ---
#     data = [["Matière", "Note", "Semestre"]]
#     total = 0

#     for note in notes:
#         data.append([note.matiere.nom, str(note.note), note.semestre])
#         total += float(note.note)

#     # Moyenne
#     if notes.exists():
#         moyenne = total / notes.count()
#         data.append(["", "Moyenne Générale", f"{moyenne:.2f}"])

#     # Création du tableau stylé
#     table = Table(data, colWidths=[200, 100, 150])
#     table.setStyle(TableStyle([
#         ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1d4ed8")),  # bleu foncé
#         ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
#         ("ALIGN", (0, 0), (-1, -1), "CENTER"),
#         ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
#         ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
#         ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
#         ("GRID", (0, 0), (-1, -1), 1, colors.black),
#     ]))

#     elements.append(table)
#     elements.append(Spacer(1, 40))

#     # --- Signature ---
#     elements.append(Paragraph("Fait à Djibouti, le ____________", normal_style))
#     elements.append(Spacer(1, 40))
#     elements.append(Paragraph("Signature du Directeur :", normal_style))
#     elements.append(Spacer(1, 40))

#     try:
#         signature = Image("static/images/signature.png", width=4*cm, height=2*cm)
#         signature.hAlign = "LEFT"
#         elements.append(signature)
#     except:
#         elements.append(Paragraph("[Signature]", normal_style))

#     # Génération PDF
#     doc.build(elements)
#     return response