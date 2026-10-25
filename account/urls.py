from django.urls import path
from . import views


urlpatterns = [
    path('home/',views.Home,name='home'),
    path('profile/',views.profile,name='profile'),
    path('login/',views.Userlogin,name="login"),
    path('sign/',views.signup,name="signup"),
    path('logout/',views.logoutUser,name="logout"),
]