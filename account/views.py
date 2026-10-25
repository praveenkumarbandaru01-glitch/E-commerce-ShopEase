from django.shortcuts import render,redirect
from django.contrib import messages

# Create your views here.
from django.contrib.auth.decorators import login_required
from .forms import UserProfileForm
from product.views import get_storefront_context


@login_required
def Home(request):
    return render(
        request,
        "product/dashboard.html",
        get_storefront_context(request),
    )


@login_required
def profile(request):
    if request.method == "POST":
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated.")
            return redirect("profile")
    else:
        form = UserProfileForm(instance=request.user)

    return render(request, "account/profile.html", {"form": form})



#Login User Authentication


from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm,AuthenticationForm
from django.contrib.auth import login,logout
def Userlogin(request):
    if request.method == 'POST':

        form = AuthenticationForm(request,data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')

    else:
        form = AuthenticationForm()

    return render(request,'account/login.html',{'form': form})


def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserCreationForm()

    return render(request,'account/register.html',{'form': form})



@login_required
def logoutUser(request):
    logout(request)
    return redirect('login')