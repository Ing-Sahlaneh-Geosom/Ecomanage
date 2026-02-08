from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from Ecole_admin.models import Matier, Classe , Eleve , Note
from Ecole_admin.utils.mixins import ActiveYearMixin, EcoleAssignMixin
from Ecole_admin.utils.utils import get_annee_active
from Matier.form import MatierForm

from django.http import HttpResponse
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Image, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.lib import colors
from io import BytesIO
from datetime import datetime



def bulletin_pdf(request, eleve_id):
    eleve = Eleve.objects.get(id=eleve_id)
    notes = Note.objects.filter(eleve=eleve)

    # 🆕 --- Calcul des moyennes par matière et trimestre ---
    moyennes_matieres = {}
    for n in notes:
        mat = n.matiere.nom
        trimestre = getattr(n, 'trimestre', 1)  # si ton modèle Note a un champ trimestre
        key = (mat, trimestre)
        if key not in moyennes_matieres:
            moyennes_matieres[key] = {'total': 0, 'coef': 0}
        moyennes_matieres[key]['total'] += n.note * n.coefficient
        moyennes_matieres[key]['coef'] += n.coefficient

    # 🆕 Calcul des moyennes par matière (tous trimestres confondus)
    moyennes_finales = {}
    for (matiere, trimestre), data in moyennes_matieres.items():
        moy_trimestre = data['total'] / data['coef'] if data['coef'] else 0
        if matiere not in moyennes_finales:
            moyennes_finales[matiere] = []
        moyennes_finales[matiere].append(moy_trimestre)

    # 🆕 Moyenne totale par matière
    moyennes_matieres_totales = {}
    for matiere, liste_moyennes in moyennes_finales.items():
        moyennes_matieres_totales[matiere] = sum(liste_moyennes) / len(liste_moyennes)

    # 🧮 Moyenne générale
    total_note, total_coef = 0, 0
    for n in notes:
        total_note += n.note * n.coefficient
        total_coef += n.coefficient
    moyenne_generale = total_note / total_coef if total_coef else 0

    # 🧮 Rang dans la classe
    all_eleves = Eleve.objects.filter(classe=eleve.classe)
    classement = []
    for e in all_eleves:
        notes_e = Note.objects.filter(eleve=e)
        total_n, total_c = 0, 0
        for n in notes_e:
            total_n += n.note * n.coefficient
            total_c += n.coefficient
        moy = total_n / total_c if total_c else 0
        classement.append((e.id, moy))
    classement.sort(key=lambda x: x[1], reverse=True)
    rang = [i + 1 for i, (id_e, _) in enumerate(classement) if id_e == eleve.id][0]

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=80, bottomMargin=40)

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='CenterTitle', alignment=TA_CENTER, fontSize=16, leading=20, spaceAfter=15))
    styles.add(ParagraphStyle(name='RightText', alignment=TA_RIGHT))
    styles.add(ParagraphStyle(name='LeftText', alignment=TA_LEFT))
    styles.add(ParagraphStyle(name='NormalBold', fontSize=12, leading=14, fontName="Helvetica-Bold"))

    elements = []

    # --- En-tête ---
    if hasattr(eleve.ecole, 'logo') and eleve.ecole.logo:
        elements.append(Image(eleve.ecole.logo.path, width=70, height=70))
    elements.append(Paragraph(f"<b>{eleve.ecole.nom}</b>", styles['CenterTitle']))
    elements.append(Paragraph("Année scolaire : 2024 - 2025", styles['CenterTitle']))
    elements.append(Spacer(1, 15))

    # --- Infos élève ---
    elements.append(Paragraph(f"<b>Nom de l'élève :</b> {eleve.nom}", styles['Normal']))
    elements.append(Paragraph(f"<b>Classe :</b> {eleve.classe}", styles['Normal']))
    elements.append(Paragraph(f"<b>Rang :</b> {rang}ᵉ sur {len(all_eleves)} élèves", styles['Normal']))
    elements.append(Spacer(1, 15))

    # 🆕 --- Tableau des moyennes par matière ---
    data = [['Matière', 'Trimestre 1', 'Trimestre 2', 'Trimestre 3', 'Moyenne Totale']]
    for matiere, moyennes in moyennes_finales.items():
        t1 = f"{moyennes[0]:.2f}" if len(moyennes) > 0 else "-"
        t2 = f"{moyennes[1]:.2f}" if len(moyennes) > 1 else "-"
        t3 = f"{moyennes[2]:.2f}" if len(moyennes) > 2 else "-"
        moyenne_totale = f"{moyennes_matieres_totales[matiere]:.2f}"
        data.append([matiere, t1, t2, t3, moyenne_totale])
    data.append(['', '', '', 'Moyenne Générale', f"{moyenne_generale:.2f}"])

    table = Table(data, colWidths=[180, 90, 90, 90, 90])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0d6efd")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 25))

    # --- Appréciation ---
    if moyenne_generale >= 16:
        appreciation = "Excellent travail 👏"
    elif moyenne_generale >= 12:
        appreciation = "Bon travail 👍"
    elif moyenne_generale >= 10:
        appreciation = "Résultats satisfaisants"
    else:
        appreciation = "Doit redoubler d'efforts"
    elements.append(Paragraph(f"<b>Appréciation :</b> {appreciation}", styles['Normal']))
    elements.append(Spacer(1, 25))

    # --- Signature ---
    date_actuelle = datetime.now().strftime("%d %B %Y")
    elements.append(Paragraph(f"Fait à Djibouti, le {date_actuelle}", styles['LeftText']))
    elements.append(Paragraph("<b>Signature du Directeur</b>", styles['RightText']))

    if hasattr(eleve.ecole, 'signature') and eleve.ecole.signature:
        elements.append(Image(eleve.ecole.signature.path, width=120, height=60, hAlign='RIGHT'))
    
    doc.build(elements)

    pdf = buffer.getvalue()
    buffer.close()
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="bulletin_{eleve.nom}.pdf"'
    response.write(pdf)
    return response









class CreateMatiere( EcoleAssignMixin , CreateView):
    model = Matier
    form_class = MatierForm
    template_name = "CreeUneMatiere.html"
    success_url = reverse_lazy('listesdesmetier')


    def get_queryset(self):
        return Matier.objects.filter(ecole=self.request.user.ecole)


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['submit_text'] = "Ajouter"
        context['Title'] = "Ajouter une matiere"
        context['classes'] = Classe.objects.filter(ecole=self.request.user.ecole)
        return context



class ListMetier( LoginRequiredMixin , ListView):
    model = Matier
    template_name = 'liste_des_matier.html'
    context_object_name = 'matiers'
    paginate_by = 20

    def get_queryset(self):
        queryset = Matier.objects.filter(
            ecole=self.request.user.ecole,
        )
        nom = self.request.GET.get('nom')

        if nom and nom != "":
            queryset = queryset.filter(nom__icontains = nom)

        return queryset



class ModifierMatiere(UpdateView):
    model = Matier
    template_name = "CreeUneMatiere.html"
    form_class = MatierForm
    success_url = reverse_lazy("listesdesmetier")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['submit_text'] = "Modifier"
        context['Title'] = "Modifier une matiere"
        return context


class SupprimerMatiere(DeleteView):
    model = Matier
    template_name = 'SupprimerUneMatiere.html'
    success_url = reverse_lazy('listesdesmetier')




from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from Ecole_admin.models import (
    AnneeScolaire, Niveau, Proffeseur, PeriodeScolaire,
    AppreciationPeriode, AppreciationAnnuelle, AppreciationAbsence,
    ConfigMoyenne, ProlongationSaisieNotes
)
from Ecole_admin.form import (
    AppreciationPeriodeForm, AppreciationAnnuelleForm, AppreciationAbsenceForm,
    ConfigMoyenneForm, ProlongationSaisieNotesForm
)

def _ctx_ecole_annee(request):
    ecole = getattr(request.user, "ecole", None)
    annee = AnneeScolaire.get_active()
    return ecole, annee


# =========================
# APPRECIATIONS PERIODES
# =========================
@login_required
def appreciation_periode_list(request):
    ecole, annee = _ctx_ecole_annee(request)
    q = (request.GET.get("q") or "").strip()

    items = AppreciationPeriode.objects.filter(ecole=ecole, annee_scolaire=annee)
    if q:
        items = items.filter(Q(nom__icontains=q))

    form = AppreciationPeriodeForm()
    return render(request, "appreciation_periode_list.html", {
        "items": items,
        "q": q,
        "form": form,
        "tab": "periode",
    })


@login_required
@require_POST
def appreciation_periode_create(request):
    ecole, annee = _ctx_ecole_annee(request)
    form = AppreciationPeriodeForm(request.POST)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.ecole = ecole
        obj.annee_scolaire = annee
        if obj.note_max < obj.note_min:
            messages.error(request, "La valeur 'Pour les marques' doit être >= 'à partir de marques'.")
        else:
            obj.save()
            messages.success(request, "Appréciation de période ajoutée.")
    else:
        messages.error(request, "Formulaire invalide.")
    return redirect("periode_liste")


@login_required
@require_POST
def appreciation_periode_update(request, pk):
    ecole, annee = _ctx_ecole_annee(request)
    obj = get_object_or_404(AppreciationPeriode, pk=pk, ecole=ecole, annee_scolaire=annee)
    form = AppreciationPeriodeForm(request.POST, instance=obj)
    if form.is_valid():
        obj2 = form.save(commit=False)
        if obj2.note_max < obj2.note_min:
            messages.error(request, "La valeur 'Pour les marques' doit être >= 'à partir de marques'.")
        else:
            obj2.save()
            messages.success(request, "Appréciation de période modifiée.")
    else:
        messages.error(request, "Formulaire invalide.")
    return redirect("periode_liste")



@login_required
@require_POST
def appreciation_periode_delete(request, pk):
    ecole, annee = _ctx_ecole_annee(request)
    obj = get_object_or_404(AppreciationPeriode, pk=pk, ecole=ecole, annee_scolaire=annee)
    obj.delete()
    messages.success(request, "Supprimé.")
    return redirect("periode_list")


# =========================
# APPRECIATIONS ANNUELLES
# =========================
@login_required
def appreciation_annuelle_list(request):
    ecole, annee = _ctx_ecole_annee(request)
    q = (request.GET.get("q") or "").strip()

    items = AppreciationAnnuelle.objects.filter(ecole=ecole, annee_scolaire=annee)
    if q:
        items = items.filter(Q(nom__icontains=q))

    form = AppreciationAnnuelleForm()
    return render(request, "appreciation_annuelle_list.html", {
        "items": items,
        "q": q,
        "form": form,
        "tab": "annuelle",
    })


@login_required
@require_POST
def appreciation_annuelle_create(request):
    ecole, annee = _ctx_ecole_annee(request)
    form = AppreciationAnnuelleForm(request.POST)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.ecole = ecole
        obj.annee_scolaire = annee
        if obj.note_max < obj.note_min:
            messages.error(request, "La valeur 'Pour les marques' doit être >= 'à partir de marques'.")
        else:
            obj.save()
            messages.success(request, "Appréciation annuelle ajoutée.")
    else:
        messages.error(request, "Formulaire invalide.")
    return redirect("annuelle_list")


@login_required
@require_POST
def appreciation_annuelle_update(request, pk):
    ecole, annee = _ctx_ecole_annee(request)
    obj = get_object_or_404(AppreciationAnnuelle, pk=pk, ecole=ecole, annee_scolaire=annee)
    form = AppreciationAnnuelleForm(request.POST, instance=obj)
    if form.is_valid():
        obj2 = form.save(commit=False)
        if obj2.note_max < obj2.note_min:
            messages.error(request, "La valeur 'Pour les marques' doit être >= 'à partir de marques'.")
        else:
            obj2.save()
            messages.success(request, "Appréciation annuelle modifiée.")
    else:
        messages.error(request, "Formulaire invalide.")
    return redirect("annuelle_list")


@login_required
@require_POST
def appreciation_annuelle_delete(request, pk):
    ecole, annee = _ctx_ecole_annee(request)
    obj = get_object_or_404(AppreciationAnnuelle, pk=pk, ecole=ecole, annee_scolaire=annee)
    obj.delete()
    messages.success(request, "Supprimé.")
    return redirect("annuelle_list")


# =========================
# APPRECIATIONS ABSENCES
# =========================
@login_required
def appreciation_absence_list(request):
    ecole, annee = _ctx_ecole_annee(request)
    q = (request.GET.get("q") or "").strip()

    items = AppreciationAbsence.objects.filter(ecole=ecole, annee_scolaire=annee)
    if q:
        items = items.filter(Q(nom__icontains=q))

    form = AppreciationAbsenceForm()
    return render(request, "appreciation_absence_list.html", {
        "items": items,
        "q": q,
        "form": form,
        "tab": "absence",
    })


@login_required
@require_POST
def appreciation_absence_create(request):
    ecole, annee = _ctx_ecole_annee(request)
    form = AppreciationAbsenceForm(request.POST)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.ecole = ecole
        obj.annee_scolaire = annee
        if obj.abs_max < obj.abs_min:
            messages.error(request, "La valeur 'à' doit être >= 'De'.")
        else:
            obj.save()
            messages.success(request, "Appréciation d'absence ajoutée.")
    else:
        messages.error(request, "Formulaire invalide.")
    return redirect("absence_list")


@login_required
@require_POST
def appreciation_absence_update(request, pk):
    ecole, annee = _ctx_ecole_annee(request)
    obj = get_object_or_404(AppreciationAbsence, pk=pk, ecole=ecole, annee_scolaire=annee)
    form = AppreciationAbsenceForm(request.POST, instance=obj)
    if form.is_valid():
        obj2 = form.save(commit=False)
        if obj2.abs_max < obj2.abs_min:
            messages.error(request, "La valeur 'à' doit être >= 'De'.")
        else:
            obj2.save()
            messages.success(request, "Appréciation d'absence modifiée.")
    else:
        messages.error(request, "Formulaire invalide.")
    return redirect("absence_list")


@login_required
@require_POST
def appreciation_absence_delete(request, pk):
    ecole, annee = _ctx_ecole_annee(request)
    obj = get_object_or_404(AppreciationAbsence, pk=pk, ecole=ecole, annee_scolaire=annee)
    obj.delete()
    messages.success(request, "Supprimé.")
    return redirect("absence_list")


# =========================
# CONFIG MOYEN (SANS AGE)
# =========================
@login_required
def config_moyenne_list(request):
    ecole, annee = _ctx_ecole_annee(request)
    q = (request.GET.get("q") or "").strip()

    items = ConfigMoyenne.objects.filter(ecole=ecole, annee_scolaire=annee).select_related("niveau")
    if q:
        items = items.filter(Q(niveau__nom__icontains=q) | Q(status__icontains=q))

    form = ConfigMoyenneForm()
    # limiter niveaux à l'école
    form.fields["niveau"].queryset = Niveau.objects.filter(ecole=ecole, actif=True)

    return render(request, "config_moyenne_list.html", {
        "items": items,
        "q": q,
        "form": form,
        "tab": "moyenne",
    })


@login_required
@require_POST
def config_moyenne_create(request):
    ecole, annee = _ctx_ecole_annee(request)
    form = ConfigMoyenneForm(request.POST)
    form.fields["niveau"].queryset = Niveau.objects.filter(ecole=ecole, actif=True)

    if form.is_valid():
        obj = form.save(commit=False)
        obj.ecole = ecole
        obj.annee_scolaire = annee
        if obj.moyenne_a < obj.moyenne_de:
            messages.error(request, "Moyen à doit être >= Moyen de.")
        else:
            obj.save()
            messages.success(request, "Configuration de moyen ajoutée.")
    else:
        messages.error(request, "Formulaire invalide.")
    return redirect("moyenne_list")


@login_required
@require_POST
def config_moyenne_update(request, pk):
    ecole, annee = _ctx_ecole_annee(request)
    obj = get_object_or_404(ConfigMoyenne, pk=pk, ecole=ecole, annee_scolaire=annee)
    form = ConfigMoyenneForm(request.POST, instance=obj)
    form.fields["niveau"].queryset = Niveau.objects.filter(ecole=ecole, actif=True)

    if form.is_valid():
        obj2 = form.save(commit=False)
        if obj2.moyenne_a < obj2.moyenne_de:
            messages.error(request, "Moyen à doit être >= Moyen de.")
        else:
            obj2.save()
            messages.success(request, "Configuration de moyen modifiée.")
    else:
        messages.error(request, "Formulaire invalide.")
    return redirect("moyenne_list")


@login_required
@require_POST
def config_moyenne_delete(request, pk):
    ecole, annee = _ctx_ecole_annee(request)
    obj = get_object_or_404(ConfigMoyenne, pk=pk, ecole=ecole, annee_scolaire=annee)
    obj.delete()
    messages.success(request, "Supprimé.")
    return redirect("moyenne_list")


# =========================
# PROLONGER LA SAISIE DES NOTES
# =========================
@login_required
def prolonger_saisie_notes(request):
    ecole, annee = _ctx_ecole_annee(request)

    niveaux = Niveau.objects.filter(ecole=ecole, actif=True).order_by("ordre", "nom")
    periodes = PeriodeScolaire.objects.filter(ecole=ecole, annee_scolaire=annee).order_by("debut")

    niveau_id = request.GET.get("niveau") or ""
    periode_id = request.GET.get("periode") or ""

    rows = []
    if niveau_id and periode_id:
        niveau = get_object_or_404(Niveau, pk=niveau_id)
        periode = get_object_or_404(PeriodeScolaire, pk=periode_id)

        # profs de l'école (tu peux affiner selon niveau/classes)
        profs = Proffeseur.objects.filter(ecole=ecole, actif=True).order_by("nom_conplet")

        # dates affichées = période
        for prof in profs:
            obj, _created = ProlongationSaisieNotes.objects.get_or_create(
                ecole=ecole,
                annee_scolaire=annee,
                professeur=prof,
                niveau=niveau,
                periode=periode,
                defaults={"debut": periode.debut, "fin": periode.fin, "actif": False, "prolonger_jours": 0},
            )
            rows.append(obj)

    return render(request, "prolonger_saisie_notes.html", {
        "niveaux": niveaux,
        "periodes": periodes,
        "niveau_id": str(niveau_id),
        "periode_id": str(periode_id),
        "rows": rows,
        "tab": "prolonger",
    })

from django.db.models import Max
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

from Ecole_admin.models import ProlongationSaisieNotes, PeriodeScolaire
from Ecole_admin.form import ProlongationSaisieNotesForm
from Ecole_admin.utils.periode import sync_periodes_auto

@login_required
@require_POST
def prolonger_saisie_notes_update(request, pk):
    ecole, annee = _ctx_ecole_annee(request)
    obj = get_object_or_404(ProlongationSaisieNotes, pk=pk, ecole=ecole, annee_scolaire=annee)

    form = ProlongationSaisieNotesForm(request.POST, instance=obj)
    if form.is_valid():
        form.save()

        # ✅ Mettre à jour la prolongation globale de la période (MAX des jours actifs)
        periode = obj.periode
        max_j = (ProlongationSaisieNotes.objects
                 .filter(ecole=ecole, annee_scolaire=annee, periode=periode, actif=True)
                 .aggregate(m=Max("prolonger_jours"))["m"]) or 0

        periode.prolongation_jours = int(max_j or 0)
        periode.save(update_fields=["prolongation_jours"])

        # ✅ auto désactivation si besoin
        sync_periodes_auto(ecole, annee)

        messages.success(request, "Prolongation mise à jour (fin période recalculée).")
    else:
        messages.error(request, "Erreur: formulaire invalide.")

    return redirect(request.META.get("HTTP_REFERER", "prolonger"))




from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from Ecole_admin.models import (
    AnneeScolaire, PeriodeScolaire,
    DecisionPromotion, DecisionAbsence, CloturePeriode, SignatureConfig
)
from Ecole_admin.form import (
    DecisionPromotionForm, DecisionAbsenceForm, CloturePeriodeForm, SignatureConfigForm
)

def _ctx_ecole_annee(request):
    ecole = getattr(request.user, "ecole", None)
    annee = AnneeScolaire.get_active()
    return ecole, annee


# =========================
# DECISIONS DE PROMOTION
# =========================
@login_required
def decision_promotion_list(request):
    ecole, annee = _ctx_ecole_annee(request)
    q = (request.GET.get("q") or "").strip()

    items = DecisionPromotion.objects.filter(ecole=ecole, annee_scolaire=annee)
    if q:
        items = items.filter(Q(decision__icontains=q) | Q(description__icontains=q))

    form = DecisionPromotionForm()
    return render(request, "decision_promotion_list.html", {
        "items": items, "q": q, "form": form, "tab": "promotion"
    })

@login_required
@require_POST
def decision_promotion_create(request):
    ecole, annee = _ctx_ecole_annee(request)
    form = DecisionPromotionForm(request.POST)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.ecole = ecole
        obj.annee_scolaire = annee
        obj.save()
        messages.success(request, "Décision ajoutée.")
    else:
        messages.error(request, "Formulaire invalide.")
    return redirect("promotion_list")

@login_required
@require_POST
def decision_promotion_update(request, pk):
    ecole, annee = _ctx_ecole_annee(request)
    obj = get_object_or_404(DecisionPromotion, pk=pk, ecole=ecole, annee_scolaire=annee)
    form = DecisionPromotionForm(request.POST, instance=obj)
    if form.is_valid():
        form.save()
        messages.success(request, "Décision modifiée.")
    else:
        messages.error(request, "Formulaire invalide.")
    return redirect("promotion_list")

@login_required
@require_POST
def decision_promotion_delete(request, pk):
    ecole, annee = _ctx_ecole_annee(request)
    obj = get_object_or_404(DecisionPromotion, pk=pk, ecole=ecole, annee_scolaire=annee)
    obj.delete()
    messages.success(request, "Supprimé.")
    return redirect("promotion_list")


# =========================
# DECISION D'ABSENCE
# =========================
@login_required
def decision_absence_list(request):
    ecole, annee = _ctx_ecole_annee(request)
    q = (request.GET.get("q") or "").strip()

    items = DecisionAbsence.objects.filter(ecole=ecole, annee_scolaire=annee)
    if q:
        items = items.filter(Q(statut__icontains=q) | Q(max_abs__icontains=q))

    form = DecisionAbsenceForm()
    return render(request, "decision_absence_list.html", {
        "items": items, "q": q, "form": form, "tab": "decision_absence"
    })

@login_required
@require_POST
def decision_absence_create(request):
    ecole, annee = _ctx_ecole_annee(request)
    form = DecisionAbsenceForm(request.POST)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.ecole = ecole
        obj.annee_scolaire = annee
        obj.save()
        messages.success(request, "Décision d'absence ajoutée.")
    else:
        messages.error(request, "Formulaire invalide.")
    return redirect("decision_absence_list")

@login_required
@require_POST
def decision_absence_update(request, pk):
    ecole, annee = _ctx_ecole_annee(request)
    obj = get_object_or_404(DecisionAbsence, pk=pk, ecole=ecole, annee_scolaire=annee)
    form = DecisionAbsenceForm(request.POST, instance=obj)
    if form.is_valid():
        form.save()
        messages.success(request, "Décision d'absence modifiée.")
    else:
        messages.error(request, "Formulaire invalide.")
    return redirect("decision_absence_list")

@login_required
@require_POST
def decision_absence_delete(request, pk):
    ecole, annee = _ctx_ecole_annee(request)
    obj = get_object_or_404(DecisionAbsence, pk=pk, ecole=ecole, annee_scolaire=annee)
    obj.delete()
    messages.success(request, "Supprimé.")
    return redirect("decision_absence_list")


# =========================
# CLOTURE DES PERIODES
# =========================
@login_required
def cloture_periode_list(request):
    ecole, annee = _ctx_ecole_annee(request)
    q = (request.GET.get("q") or "").strip()

    items = CloturePeriode.objects.filter(ecole=ecole).select_related("annee_scolaire", "periode_scolaire")
    if q:
        items = items.filter(Q(description__icontains=q) | Q(periode_scolaire__nom__icontains=q))

    form = CloturePeriodeForm()
    form.fields["annee_scolaire"].queryset = AnneeScolaire.objects.all()
    form.fields["periode_scolaire"].queryset = PeriodeScolaire.objects.filter(ecole=ecole, annee_scolaire=annee)

    return render(request, "cloture_periode_list.html", {
        "items": items, "q": q, "form": form, "tab": "cloture"
    })

@login_required
@require_POST
def cloture_periode_create(request):
    ecole, annee_active = _ctx_ecole_annee(request)
    form = CloturePeriodeForm(request.POST)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.ecole = ecole
        obj.save()
        messages.success(request, "Clôture ajoutée.")
    else:
        messages.error(request, "Formulaire invalide.")
    return redirect("cloture_list")

from django.views.decorators.http import require_POST
from Ecole_admin.models import CloturePeriode
from Ecole_admin.utils.periode import sync_periodes_auto


def _ctx_school(request):
    ecole = request.user.ecole
    from Ecole_admin.utils.utils import get_annee_active
    annee = get_annee_active(request)
    return ecole, annee


@login_required
@require_POST
def cloture_periode_toggle(request, pk):
    ecole, annee = _ctx_school(request)
    obj = get_object_or_404(CloturePeriode, pk=pk, ecole=ecole, annee_scolaire=annee)

    value = request.POST.get("cloturee") == "on"
    obj.cloturee = value
    obj.save(update_fields=["cloturee"])

    # si on cloture => désactiver la période immédiatement
    if value:
        p = obj.periode_scolaire
        if p.est_active:
            p.est_active = False
            p.save(update_fields=["est_active"])

    # et sync auto (pour toutes les autres)
    sync_periodes_auto(ecole, annee)

    messages.success(request, "Statut de clôture mis à jour.")
    return redirect("cloture_list")



@login_required
@require_POST
def cloture_periode_delete(request, pk):
    ecole, _annee = _ctx_ecole_annee(request)
    obj = get_object_or_404(CloturePeriode, pk=pk, ecole=ecole)
    obj.delete()
    messages.success(request, "Supprimé.")
    return redirect("cloture_list")



from Ecole_admin.models import AnneeScolaire
from Ecole_admin.utils.periode import is_periode_closed, is_periode_expired
from django.urls import reverse

@login_required
def prolongation_periode(request):
    ecole, annee_active = _ctx_school(request)

    # filtre: année seulement
    annee_id = request.GET.get("annee") or ""
    annee = AnneeScolaire.objects.filter(id=annee_id).first() if annee_id else annee_active

    sync_periodes_auto(ecole, annee)

    periodes = PeriodeScolaire.objects.filter(ecole=ecole, annee_scolaire=annee).order_by("debut")
    rows = []
    for p in periodes:
        rows.append({
            "p": p,
            "closed": is_periode_closed(ecole, annee, p),
            "expired": is_periode_expired(p),
        })

    annees = AnneeScolaire.objects.all().order_by("-debut")

    return render(request, "prolongation_periode.html", {
        "annees": annees,
        "annee": annee,
        "rows": rows,
    })




@login_required
@require_POST
def prolongation_periode_update(request, pk):
    ecole, _annee_active = _ctx_school(request)
    p = get_object_or_404(PeriodeScolaire, pk=pk, ecole=ecole)

    # revenir au même filtre année
    annee_id = request.POST.get("annee_id") or str(p.annee_scolaire_id)
    annee = p.annee_scolaire

    # si clôturée => pas de prolongation (car clôture doit gagner)
    if is_periode_closed(ecole, annee, p):
        messages.error(request, "Période clôturée : prolongation impossible.")
        return redirect(f"/config/periodes/prolongation/?annee={annee_id}")

    try:
        j = int(request.POST.get("prolongation_jours") or 0)
        if j < 0:
            j = 0
    except Exception:
        j = 0

    p.prolongation_jours = j
    p.save(update_fields=["prolongation_jours"])

    # auto désactivation si malgré prolongation la période est dépassée
    sync_periodes_auto(ecole, annee)

    messages.success(request, "Prolongation de la période mise à jour.")
    return redirect(reverse("prolongation_periode") + f"?annee={annee_id}")