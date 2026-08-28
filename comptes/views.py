from django.contrib.auth import login
from django.shortcuts import redirect, render

from .forms import InscriptionForm


def inscription(request):
    if request.user.is_authenticated:
        return redirect("tableau_de_bord")
    form = InscriptionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        utilisateur = form.save()
        login(request, utilisateur)
        return redirect("tableau_de_bord")
    return render(request, "comptes/inscription.html", {"form": form})

# Create your views here.
