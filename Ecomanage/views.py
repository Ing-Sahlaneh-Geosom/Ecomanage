import json
from bdb import effective

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.db.models.functions import ExtractMonth
from django.http import HttpResponse
from django.shortcuts import render
from Ecole_admin.models import Eleve, User, Absence, Paiment, Note, Proffeseur, Classe , RecuCaisse
from datetime import datetime
from django.contrib.auth.mixins import LoginRequiredMixin
from Ecole_admin.utils.utils import get_annee_active


@login_required(login_url='Connection')
def page_acceuil(request):
    user = request.user
    ecole = user.ecole
    annee_scolaire = get_annee_active(request)

    role = (user.role or "").lower().strip()

    # =========================
    # ✅ PARENT DASHBOARD
    # =========================
    if role == "parent":
        # Les enfants du parent: Eleve.parent_user -> User parent
        enfants = Eleve.objects.filter(
            parent_user=user,
            ecole=ecole,
            annee_scolaire=annee_scolaire
        ).select_related("classe")

        # stats simples
        absences = Absence.objects.filter(
            eleve__in=enfants,
            ecole=ecole,
            annee_scolaire=annee_scolaire
        ).order_by("-date")[:10]

        paiements = Paiment.objects.filter(
            eleve__in=enfants,
            ecole=ecole,
            annee_scolaire=annee_scolaire
        ).order_by("-date_paiement")[:10]

        notes = Note.objects.filter(
            eleve__in=enfants,
            ecole=ecole,
            annee_scolaire=annee_scolaire
        ).order_by("-id")[:10]

        context = {
            "mode": "parent",
            "enfants": enfants,
            "apsences": absences,
            "paiements": paiements,
            "notes": notes,
        }
        return render(request, "home_page.html", context)

    # =========================
    # ✅ PROF DASHBOARD
    # =========================
    if role == "proffesseur":
        # si tu as bien prof.user -> User
        prof = getattr(user, "proffeseur", None)

        classes = Classe.objects.none()
        eleves = Eleve.objects.none()

        if prof:
            classes = Classe.objects.filter(professeurs=prof, ecole=ecole).distinct()
            eleves = Eleve.objects.filter(
                classe__in=classes,
                ecole=ecole,
                annee_scolaire=annee_scolaire
            ).distinct()

        context = {
            "mode": "Prof",
            "classes": classes,
            "eleves": eleves,
        }
        return render(request, "home_page.html", context)

    # =========================
    # ✅ ADMIN / SECRETAIRE DASHBOARD
    # =========================
    if role in ["admin", "secretaire"]:
        mois_noms = ["janv","fevr","mars","avr","mai","juin","juil","aout","sept","oct","nov","dec"]
        absence_par_mois = [0] * 12
        paiement_par_mois = [0] * 12

        annee_actuelle = datetime.now().year

        abs_qs = Absence.objects.filter(
            ecole=ecole,
            annee_scolaire=annee_scolaire,
            date__year=annee_actuelle
        )
        for a in abs_qs:
            absence_par_mois[a.date.month - 1] += 1

        pay_qs = RecuCaisse.objects.filter(
            ecole=ecole,
            annee_scolaire=annee_scolaire,
            date_operation__year=annee_actuelle
        )
        for p in pay_qs:
            paiement_par_mois[p.date_operation.month - 1] += float(p.total)

        eleves = Eleve.objects.filter(ecole=ecole, annee_scolaire=annee_scolaire)
        total_eleves = eleves.count()

        total_montant = RecuCaisse.objects.filter(
            ecole=ecole,
            annee_scolaire=annee_scolaire
        ).aggregate(Sum("total"))["total__sum"] or 0

        utilisateur = user.__class__.objects.filter(ecole=ecole)  # User.objects
        absenceRecent = Absence.objects.filter(ecole=ecole, annee_scolaire=annee_scolaire).order_by("-date")[:5]
        paiements_recents = RecuCaisse.objects.filter(ecole=ecole, annee_scolaire=annee_scolaire).order_by("-date_operation")[:5]

        context = {
            "mode": "admin",
            "mois_abs": json.dumps(mois_noms),
            "totaux_abs": json.dumps([int(x) for x in absence_par_mois]),
            "totaux_paie": json.dumps(paiement_par_mois),
            "eleves": eleves,
            "utilisateur": utilisateur,
            "absenceRecent": absenceRecent,
            "total_eleves": total_eleves,
            "Total_montant": total_montant,
            "paiments_recents": paiements_recents
        }
        return render(request, "home_page.html", context)

    # =========================
    # ✅ DEFAULT
    # =========================
    context = {"mode": "user"}
    return render(request, "home_page.html", context)

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