from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Income, Expense, Category, UserProfile


def home(request):
    return render(request, 'home/home.html')


@login_required
def add_income(request):
    if request.method == 'POST':
        
        amount = request.POST.get('amount')
        date = request.POST.get('date')
        description = request.POST.get('description')
        category_id = request.POST.get('category')

        
        category = Category.objects.get(id=category_id) if category_id else None

       
        Income.objects.create(
            user=request.user,
            amount=amount,
            date=date,
            description=description,
            category=category
        )
        return redirect('dashboard')
    
    categories = Category.objects.filter(user=request.user)
    return render(request, 'home/add_income.html', {'categories': categories})

@login_required
def add_expense(request):
    if request.method == 'POST':
        
        amount = request.POST.get('amount')
        date = request.POST.get('date')
        description = request.POST.get('description')
        category_id = request.POST.get('category')

        
        category = Category.objects.get(id=category_id) if category_id else None

        
        Expense.objects.create(
            user=request.user,
            amount=amount,
            date=date,
            description=description,
            category=category
        )
        return redirect('dashboard')
    
    categories = Category.objects.filter(user=request.user)
    return render(request, 'home/add_expense.html', {'categories': categories})

@login_required

def add_category(request):
    if request.method == 'POST':
        name = request.POST.get('name')

        # Check if the category already exists for the user
        if Category.objects.filter(user=request.user, name=name).exists():
            return render(request, 'home/add_category.html', {
                'error': 'Category already exists.'
            })

        
        Category.objects.create(user=request.user, name=name)
        return redirect('dashboard')

    return render(request, 'home/add_category.html')



@login_required
def dashboard(request):
    
    incomes = Income.objects.filter(user=request.user).order_by('-date')  
    expenses = Expense.objects.filter(user=request.user).order_by('-date')
    categories = Category.objects.filter(user=request.user)

 
    total_income = sum(income.amount for income in incomes)
    total_expenses = sum(expense.amount for expense in expenses)

  
    balance = total_income - total_expenses

   
    try:
        user_profile = request.user.userprofile  
        budget_limit = user_profile.budget_limit
    except UserProfile.DoesNotExist:
        budget_limit = 0  
    
  
    budget_alert = False
    if budget_limit and total_expenses > budget_limit:
        budget_alert = True

    
    context = {
        'incomes': incomes,
        'expenses': expenses,
        'categories': categories,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'balance': balance,
        'budget_limit': budget_limit,
        'budget_alert': budget_alert,
    }

    return render(request, 'home/dashboard.html', context)




@login_required
def update_budget(request):
    
    user = request.user

    user_profile, created = UserProfile.objects.get_or_create(user=user)

    if request.method == 'POST':
        new_budget = request.POST.get('budget_limit') 
        if new_budget:
            
            if user_profile:
                user_profile.budget_limit = new_budget
                user_profile.save()  
                return redirect('dashboard') 
            else:
                
                return redirect('error_page') # error_page to be created later
        else:
           
            return render(request, 'home/update_budget.html', {'error': 'Please provide a valid budget limit.'})

    
    return render(request, 'home/update_budget.html', {'user_profile': user_profile})