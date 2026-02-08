from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from Ecole_admin.models import Employe, Ecole
from Ecole_admin.form import EmployeForm

ALLOWED_ROLES = {"admin", "secretaire"}  # adapte si tu veux

def _role_ok(user):
    return user.is_authenticated and getattr(user, "role", None) in ALLOWED_ROLES

@login_required
def employe_list(request):
    if not _role_ok(request.user):
        return HttpResponseForbidden("Accès interdit")

    # ecole courante (si tu relies user.ecole)
    ecole = getattr(request.user, "ecole", None)
    if not ecole:
        messages.error(request, "Votre compte n'est lié à aucune école.")
        return render(request, "employes/employe_list.html", {"items": [], "form": EmployeForm()})

    q = (request.GET.get("q") or "").strip()
    items = Employe.objects.filter(ecole=ecole)

    if q:
        items = items.filter(nom_complet__icontains=q) | items.filter(matricule__icontains=q)

    form = EmployeForm()
    return render(request, "employe_list.html", {"items": items, "form": form, "q": q})

@login_required
@require_POST
def employe_create(request):
    if not _role_ok(request.user):
        return JsonResponse({"ok": False, "message": "Accès interdit"}, status=403)

    ecole = getattr(request.user, "ecole", None)
    if not ecole:
        return JsonResponse({"ok": False, "message": "Utilisateur sans école."}, status=400)

    form = EmployeForm(request.POST)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.ecole = ecole
        obj.save()
        return JsonResponse({"ok": True, "message": "Employé ajouté."})
    return JsonResponse({"ok": False, "errors": form.errors}, status=400)

@login_required
def employe_get(request, pk):
    """Retourne les données JSON pour pré-remplir le modal update."""
    if not _role_ok(request.user):
        return JsonResponse({"ok": False, "message": "Accès interdit"}, status=403)

    ecole = getattr(request.user, "ecole", None)
    obj = get_object_or_404(Employe, pk=pk, ecole=ecole)

    data = {
        "id": obj.id,
        "nom_complet": obj.nom_complet,
        "matricule": obj.matricule,
        "sexe": obj.sexe,
        "telephone": obj.telephone,
        "email": obj.email,
        "fonction": obj.fonction,
        "autre_fonction": obj.autre_fonction,
        "statut": obj.statut,
        "bureau": obj.bureau,
        "date_embauche": obj.date_embauche.isoformat() if obj.date_embauche else "",
        "working_hours": obj.working_hours,
    }
    return JsonResponse({"ok": True, "data": data})

@login_required
@require_POST
def employe_update(request, pk):
    if not _role_ok(request.user):
        return JsonResponse({"ok": False, "message": "Accès interdit"}, status=403)

    ecole = getattr(request.user, "ecole", None)
    obj = get_object_or_404(Employe, pk=pk, ecole=ecole)

    form = EmployeForm(request.POST, instance=obj)
    if form.is_valid():
        form.save()
        return JsonResponse({"ok": True, "message": "Employé mis à jour."})
    return JsonResponse({"ok": False, "errors": form.errors}, status=400)

@login_required
@require_POST
def employe_delete(request, pk):
    if not _role_ok(request.user):
        return JsonResponse({"ok": False, "message": "Accès interdit"}, status=403)

    ecole = getattr(request.user, "ecole", None)
    obj = get_object_or_404(Employe, pk=pk, ecole=ecole)
    obj.delete()
    return JsonResponse({"ok": True, "message": "Employé supprimé."})





# views.py
from calendar import monthrange
from datetime import date
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from Ecole_admin.models import Employe, EmployeAbsence, AnneeScolaire

def staff_only(user):
    return user.is_authenticated and user.role in ("admin", "secretaire")

@login_required
def saisie_absences_employes(request):
    if not staff_only(request.user):
        raise PermissionDenied()

    annee = AnneeScolaire.get_active()
    ecole = request.user.ecole

    date_str = request.GET.get("date") or timezone.localdate().isoformat()
    emp_id = request.GET.get("emp") or ""
    h_debut = request.GET.get("h_debut") or ""
    h_fin = request.GET.get("h_fin") or ""

    emps_qs = Employe.objects.filter(ecole=ecole, statut="active").order_by("nom_complet")
    if emp_id:
        emps_qs = emps_qs.filter(id=emp_id)
    emps = list(emps_qs)

    exist_qs = EmployeAbsence.objects.filter(
        ecole=ecole, annee_scolaire=annee, date=date_str, employe__in=emps
    )
    if h_debut:
        exist_qs = exist_qs.filter(h_debut=h_debut)
    if h_fin:
        exist_qs = exist_qs.filter(h_fin=h_fin)

    exist_map = {a.employe_id: a for a in exist_qs}

    if request.method == "POST":
        date_post = request.POST.get("date") or date_str
        h_debut_post = request.POST.get("h_debut") or None
        h_fin_post = request.POST.get("h_fin") or None

        saved = 0
        for e in emps:
            statut = request.POST.get(f"statut_{e.id}", "present")
            motif = (request.POST.get(f"motif_{e.id}", "") or "").strip()
            justifiee = request.POST.get(f"justifiee_{e.id}") == "1"

            should_save = (statut != "present") or motif or justifiee
            if not should_save:
                old = exist_map.get(e.id)
                if old:
                    old.delete()
                continue

            obj = exist_map.get(e.id)
            if obj:
                obj.statut = statut
                obj.motif = motif
                obj.justifiee = justifiee
                obj.user = request.user
                obj.h_debut = h_debut_post
                obj.h_fin = h_fin_post
                obj.save()
            else:
                EmployeAbsence.objects.create(
                    user=request.user,
                    ecole=ecole,
                    annee_scolaire=annee,
                    employe=e,
                    date=date_post,
                    h_debut=h_debut_post,
                    h_fin=h_fin_post,
                    statut=statut,
                    motif=motif,
                    justifiee=justifiee,
                )
            saved += 1

        messages.success(request, f"✅ Absences employés enregistrées ({saved})")
        return redirect(f"{request.path}?date={date_post}&emp={emp_id}&h_debut={h_debut_post or ''}&h_fin={h_fin_post or ''}")

    rows = [{"e": e, "a": exist_map.get(e.id)} for e in emps]

    return render(request, "saisie_absences_employes.html", {
        "date_value": date_str,
        "emp_id": emp_id,
        "h_debut": h_debut,
        "h_fin": h_fin,
        "emps_select": Employe.objects.filter(ecole=ecole, statut="active").order_by("nom_complet"),
        "rows": rows,
    })





@login_required
def suivi_absences_employes(request):
    if not staff_only(request.user):
        raise PermissionDenied()

    ecole = request.user.ecole

    # ✅ années présentes en DB (select)
    annees_db = AnneeScolaire.objects.order_by("-debut")
    annee_id = request.GET.get("annee_id") or str(AnneeScolaire.get_active().id)

    # mois
    today = date.today()
    mois = int(request.GET.get("mois", today.month))
    emp_id = request.GET.get("emp") or ""

    annee_obj = get_object_or_404(AnneeScolaire, id=annee_id)

    start_date = date(annee_obj.debut.year if annee_obj.debut else today.year, mois, 1)
    end_date = date(start_date.year, mois, monthrange(start_date.year, mois)[1])

    qs = EmployeAbsence.objects.filter(
        ecole=ecole,
        annee_scolaire=annee_obj,
        date__range=(start_date, end_date),
    ).select_related("employe").order_by("date", "h_debut")

    if emp_id:
        qs = qs.filter(employe_id=emp_id)

    if request.method == "POST":
        delete_id = request.POST.get("delete_id")
        if delete_id:
            obj = get_object_or_404(EmployeAbsence, id=delete_id, ecole=ecole, annee_scolaire=annee_obj)
            obj.delete()
            messages.success(request, "✅ Absence supprimée")
            return redirect(request.get_full_path())

    return render(request, "suivi_absences_employes.html", {
        "rows": qs,
        "emps": Employe.objects.filter(ecole=ecole, statut="active").order_by("nom_complet"),
        "annees_db": annees_db,
        "annee_id": str(annee_obj.id),
        "mois": mois,
        "emp_id": emp_id,
    })




from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import HttpResponseForbidden
from django.shortcuts import render

from Ecole_admin.models import User  # adapte le chemin si besoin


def staff_only(user):
    return user.is_authenticated and user.role in ("admin", "secretaire")


@login_required
def liste_parents(request):
    if not staff_only(request.user):
        return HttpResponseForbidden("Accès refusé.")

    ecole = request.user.ecole
    q = (request.GET.get("q") or "").strip()

    parents = (
        User.objects.filter(role="parent", ecole=ecole)
        .annotate(nb_enfants=Count("enfants", distinct=True))  # Eleve.parent_user related_name="enfants"
        .order_by("-id")
    )

    if q:
        parents = parents.filter(
            Q(username__icontains=q)
            | Q(nom_complet__icontains=q)
            | Q(email__icontains=q)
            | Q(num_tel__icontains=q)
        )

    paginator = Paginator(parents, 10)  # 10 par page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "liste_parents.html", {
        "page_obj": page_obj,
        "q": q,
        "total": paginator.count,
    })

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET, require_POST

from Ecole_admin.models import Batiment


def staff_only(user):
    return user.is_authenticated and user.role in ("admin", "secretaire")


def _forbidden():
    return HttpResponseForbidden("Accès refusé.")


@login_required
def batiments_page(request):
    if not staff_only(request.user):
        return _forbidden()
    return render(request, "batiments_onepage_custommodal.html")


@login_required
@require_GET
def batiments_api_list(request):
    if not staff_only(request.user):
        return _forbidden()

    ecole = request.user.ecole
    q = (request.GET.get("q") or "").strip()
    actif = (request.GET.get("actif") or "").strip()  # "", "1", "0"
    page = int(request.GET.get("page") or 1)
    page_size = int(request.GET.get("page_size") or 10)

    qs = Batiment.objects.filter(ecole=ecole)

    if q:
        qs = qs.filter(
            Q(nom__icontains=q) |
            Q(code__icontains=q) |
            Q(adresse__icontains=q)
        )

    if actif == "1":
        qs = qs.filter(actif=True)
    elif actif == "0":
        qs = qs.filter(actif=False)

    qs = qs.order_by("nom", "id")

    paginator = Paginator(qs, page_size)
    page_obj = paginator.get_page(page)

    items = [{
        "id": b.id,
        "nom": b.nom,
        "code": b.code or "",
        "adresse": b.adresse or "",
        "nb_etages": b.nb_etages,
        "actif": bool(b.actif),
        "description": b.description or "",
    } for b in page_obj]

    return JsonResponse({
        "items": items,
        "page": page_obj.number,
        "pages": paginator.num_pages,
        "total": paginator.count,
        "page_size": page_size,
    })


@login_required
@require_GET
def batiments_api_detail(request, pk):
    if not staff_only(request.user):
        return _forbidden()

    ecole = request.user.ecole
    b = get_object_or_404(Batiment, pk=pk, ecole=ecole)

    return JsonResponse({
        "id": b.id,
        "nom": b.nom,
        "code": b.code or "",
        "adresse": b.adresse or "",
        "nb_etages": b.nb_etages,
        "actif": bool(b.actif),
        "description": b.description or "",
    })


@login_required
@require_POST
def batiments_api_create(request):
    if not staff_only(request.user):
        return _forbidden()

    ecole = request.user.ecole
    nom = (request.POST.get("nom") or "").strip()
    if not nom:
        return JsonResponse({"ok": False, "error": "Le nom est obligatoire."}, status=400)

    code = (request.POST.get("code") or "").strip()
    adresse = (request.POST.get("adresse") or "").strip()
    description = (request.POST.get("description") or "").strip()

    try:
        nb_etages = int(request.POST.get("nb_etages") or 0)
        if nb_etages < 0: nb_etages = 0
    except ValueError:
        nb_etages = 0

    actif = (request.POST.get("actif") or "1") == "1"

    b = Batiment.objects.create(
        ecole=ecole,
        nom=nom,
        code=code,
        adresse=adresse,
        nb_etages=nb_etages,
        actif=actif,
        description=description,
    )
    return JsonResponse({"ok": True, "id": b.id})


@login_required
@require_POST
def batiments_api_update(request, pk):
    if not staff_only(request.user):
        return _forbidden()

    ecole = request.user.ecole
    b = get_object_or_404(Batiment, pk=pk, ecole=ecole)

    nom = (request.POST.get("nom") or "").strip()
    if not nom:
        return JsonResponse({"ok": False, "error": "Le nom est obligatoire."}, status=400)

    b.nom = nom
    b.code = (request.POST.get("code") or "").strip()
    b.adresse = (request.POST.get("adresse") or "").strip()
    b.description = (request.POST.get("description") or "").strip()

    try:
        nb_etages = int(request.POST.get("nb_etages") or 0)
        if nb_etages < 0: nb_etages = 0
    except ValueError:
        nb_etages = 0

    b.nb_etages = nb_etages
    b.actif = (request.POST.get("actif") or "1") == "1"
    b.save()
    return JsonResponse({"ok": True})


@login_required
@require_POST
def batiments_api_delete(request, pk):
    if not staff_only(request.user):
        return _forbidden()

    ecole = request.user.ecole
    b = get_object_or_404(Batiment, pk=pk, ecole=ecole)
    b.delete()
    return JsonResponse({"ok": True})


from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET, require_POST

from Ecole_admin.models import Salle, Batiment


def staff_only(user):
    return user.is_authenticated and user.role in ("admin", "secretaire")


def _forbidden():
    return HttpResponseForbidden("Accès refusé.")


@login_required
def salles_page(request):
    if not staff_only(request.user):
        return _forbidden()
    return render(request, "salles_onepage_custommodal.html")


@login_required
@require_GET
def salles_api_batiments(request):
    """Bâtiments de l'école (pour filtre + select modal)"""
    if not staff_only(request.user):
        return _forbidden()

    ecole = request.user.ecole
    bats = Batiment.objects.filter(ecole=ecole, actif=True).order_by("nom", "id")
    return JsonResponse({
        "items": [
            {"id": b.id, "nom": b.nom, "code": b.code or "", "nb_etages": int(b.nb_etages or 0)}
            for b in bats
        ]
    })


@login_required
@require_GET
def salles_api_etages(request):
    """Retourne la liste des étages possibles selon le bâtiment choisi"""
    if not staff_only(request.user):
        return _forbidden()

    ecole = request.user.ecole
    batiment_id = (request.GET.get("batiment_id") or "").strip()
    if not batiment_id:
        return JsonResponse({"items": []})

    b = get_object_or_404(Batiment, id=batiment_id, ecole=ecole)

    # ✅ étages: 0..nb_etages-1
    n = int(b.nb_etages or 0)
    items = []
    for i in range(max(0, n)):
        label = "Étage 0" if i == 0 else f"Étage {i}"
        items.append({"value": i, "label": label})

    return JsonResponse({"items": items})


@login_required
@require_GET
def salles_api_list(request):
    if not staff_only(request.user):
        return _forbidden()

    ecole = request.user.ecole
    q = (request.GET.get("q") or "").strip()
    batiment_id = (request.GET.get("batiment") or "").strip()
    page = int(request.GET.get("page") or 1)
    page_size = int(request.GET.get("page_size") or 10)

    qs = Salle.objects.filter(ecole=ecole).select_related("batiment")

    if batiment_id:
        qs = qs.filter(batiment_id=batiment_id)

    if q:
        qs = qs.filter(
            Q(nom__icontains=q) |
            Q(description__icontains=q) |
            Q(batiment__nom__icontains=q)
        )

    qs = qs.order_by("batiment__nom", "etage", "nom", "id")

    paginator = Paginator(qs, page_size)
    page_obj = paginator.get_page(page)

    items = []
    for s in page_obj:
        items.append({
            "id": s.id,
            "nom": s.nom,
            "etage": s.etage,
            "description": s.description or "",
            "batiment": {"id": s.batiment_id, "nom": s.batiment.nom, "nb_etages": int(s.batiment.nb_etages or 0)},
        })

    return JsonResponse({
        "items": items,
        "page": page_obj.number,
        "pages": paginator.num_pages,
        "total": paginator.count,
        "page_size": page_size,
    })


@login_required
@require_GET
def salles_api_detail(request, pk):
    if not staff_only(request.user):
        return _forbidden()

    ecole = request.user.ecole
    s = get_object_or_404(Salle, pk=pk, ecole=ecole)

    return JsonResponse({
        "id": s.id,
        "batiment_id": s.batiment_id,
        "nom": s.nom,
        "etage": s.etage,
        "description": s.description or "",
    })


@login_required
@require_POST
def salles_api_create(request):
    if not staff_only(request.user):
        return _forbidden()

    ecole = request.user.ecole

    batiment_id = (request.POST.get("batiment_id") or "").strip()
    if not batiment_id:
        return JsonResponse({"ok": False, "error": "Choisis un bâtiment."}, status=400)
    b = get_object_or_404(Batiment, id=batiment_id, ecole=ecole)

    nom = (request.POST.get("nom") or "").strip()
    if not nom:
        return JsonResponse({"ok": False, "error": "Le nom de la salle est obligatoire."}, status=400)

    try:
        etage = int(request.POST.get("etage") or 0)
    except ValueError:
        etage = 0

    # ✅ validation etage selon batiment
    nb = int(b.nb_etages or 0)
    if etage < 0 or etage >= max(0, nb):
        return JsonResponse({"ok": False, "error": "Étage invalide pour ce bâtiment."}, status=400)

    description = (request.POST.get("description") or "").strip()

    s = Salle.objects.create(ecole=ecole, batiment=b, nom=nom, etage=etage, description=description)
    return JsonResponse({"ok": True, "id": s.id})


@login_required
@require_POST
def salles_api_update(request, pk):
    if not staff_only(request.user):
        return _forbidden()

    ecole = request.user.ecole
    s = get_object_or_404(Salle, pk=pk, ecole=ecole)

    batiment_id = (request.POST.get("batiment_id") or "").strip()
    if not batiment_id:
        return JsonResponse({"ok": False, "error": "Choisis un bâtiment."}, status=400)
    b = get_object_or_404(Batiment, id=batiment_id, ecole=ecole)

    nom = (request.POST.get("nom") or "").strip()
    if not nom:
        return JsonResponse({"ok": False, "error": "Le nom de la salle est obligatoire."}, status=400)

    try:
        etage = int(request.POST.get("etage") or 0)
    except ValueError:
        etage = 0

    nb = int(b.nb_etages or 0)
    if etage < 0 or etage >= max(0, nb):
        return JsonResponse({"ok": False, "error": "Étage invalide pour ce bâtiment."}, status=400)

    s.batiment = b
    s.nom = nom
    s.etage = etage
    s.description = (request.POST.get("description") or "").strip()
    s.save()

    return JsonResponse({"ok": True})


@login_required
@require_POST
def salles_api_delete(request, pk):
    if not staff_only(request.user):
        return _forbidden()

    ecole = request.user.ecole
    s = get_object_or_404(Salle, pk=pk, ecole=ecole)
    s.delete()
    return JsonResponse({"ok": True})
