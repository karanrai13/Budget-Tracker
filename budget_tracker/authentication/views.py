from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm


def login_page(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)  
                return redirect('/')  
            else:
                form.add_error(None, 'Invalid username or password.')
    else:
        form = AuthenticationForm() 

    return render(request, 'authentication/login.html', {'form': form})


def register_page(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        username = request.POST.get('user_name')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        
        if password != confirm_password:
            messages.error(request, "Passwords do not match!")
            return redirect('/auth/register/')
      
        if User.objects.filter(username=username).exists():
            messages.info(request, "Username already taken!")
            return redirect('/auth/register/')
        
       
        if User.objects.filter(email=email).exists():
            messages.info(request, "Email already registered!")
            return redirect('/auth/register/')
  
        user = User.objects.create_user(
            username=username,  
            email=email,
            password=password
        )
        user.save()
        
        messages.success(request, "Your Budget Tracker Account is Created! Please log in.")
        return redirect('/auth/login/') 
    
    return render(request, 'authentication/register.html')

def logout_page(request):
    logout(request)  
    return redirect('/auth/login/') 