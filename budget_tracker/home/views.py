from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Income, Expense, Category, UserProfile
from django.db import models
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors


def home(request):
    return render(request, 'home/home.html')


@login_required
def add_income(request):
    categories = Category.objects.filter(category_type=Category.INCOME)
    if not categories.exists():
        messages.warning(request, "No income categories available. Please create one first.")
        return redirect('category')

    if request.method == 'POST':
        amount = request.POST.get('amount')
        date = request.POST.get('date')
        description = request.POST.get('description')
        category_id = request.POST.get('category')

        if amount and date and description and category_id:
            try:
                selected_category = Category.objects.get(id=category_id)
                Income.objects.create(
                    user=request.user,
                    amount=amount,
                    date=date,
                    description=description,
                    category=selected_category
                )
                messages.success(request, "Income added successfully!")
                return redirect('dashboard')
            except Category.DoesNotExist:
                messages.error(request, "Invalid category selected.")
        else:
            messages.error(request, "All fields are required.")
    return render(request, 'home/add_income.html', {'categories': categories})


@login_required
def add_expense(request):
    categories = Category.objects.filter(category_type=Category.EXPENSE)
    if not categories.exists():
        messages.warning(request, "No Expense categories available. Please create one first.")
        return redirect('category')
    if request.method == 'POST':
        amount = request.POST.get('amount')
        date = request.POST.get('date')
        description = request.POST.get('description')
        category_id = request.POST.get('category')

        if not amount or not date:
            messages.error(request, "Amount and date are required.")
            return redirect('expense')

        try:
            category = Category.objects.get(
                id=category_id, 
                user=request.user, 
                category_type=Category.EXPENSE
            )
        except Category.DoesNotExist:
            messages.error(request, "Please select a valid expense category.")
            return redirect('expense')

        Expense.objects.create(
            user=request.user,
            amount=amount,
            date=date,
            description=description,
            category=category
        )
        messages.success(request, "Expense added successfully!")
        return redirect('dashboard')

    categories = Category.objects.filter(user=request.user, category_type=Category.EXPENSE)
    return render(request, 'home/add_expense.html', {'categories': categories})


@login_required
def add_category(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        category_type = request.POST.get('category_type')

        if not name or not category_type:
            messages.error(request, "Both category name and type are required.")
            return redirect('category')

        valid_types = [choice[0] for choice in Category.CATEGORY_TYPES]
        if category_type not in valid_types:
            messages.error(request, "Invalid category type.")
            return redirect('category')

        if Category.objects.filter(user=request.user, name=name, category_type=category_type).exists():
            messages.error(request, "Category already exists.")
            return redirect('category')

        Category.objects.create(user=request.user, name=name, category_type=category_type)
        messages.success(request, "Category added successfully!")
        return redirect('dashboard')

    return render(request, 'home/add_category.html')


@login_required
def dashboard(request):
    incomes = Income.objects.filter(user=request.user).order_by('-date')
    expenses = Expense.objects.filter(user=request.user).order_by('-date')
    categories = Category.objects.filter(user=request.user)

    total_income = incomes.aggregate(total=models.Sum('amount'))['total'] or 0
    total_expenses = expenses.aggregate(total=models.Sum('amount'))['total'] or 0
    balance = total_income - total_expenses

    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    budget_limit = user_profile.budget_limit

    budget_alert = total_expenses > budget_limit if budget_limit else False

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

    if budget_alert:
        messages.warning(request, "Your expenses have exceeded the budget limit.")

    return render(request, 'home/dashboard.html', context)


@login_required
def update_budget(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        new_budget = request.POST.get('budget_limit')

        if not new_budget or float(new_budget) <= 0:
            messages.error(request, "Please provide a valid budget limit.")
            return redirect('update_budget')

        user_profile.budget_limit = float(new_budget)
        user_profile.save()
        messages.success(request, "Budget updated successfully!")
        return redirect('dashboard')

    return render(request, 'home/update_budget.html', {'user_profile': user_profile})


@login_required
def generate_report(request):
    incomes = Income.objects.filter(user=request.user)
    expenses = Expense.objects.filter(user=request.user)

    total_income = incomes.aggregate(total=models.Sum('amount'))['total'] or 0
    total_expenses = expenses.aggregate(total=models.Sum('amount'))['total'] or 0

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)

    p.setFillColor(colors.blue)
    p.setFont("Helvetica-Bold", 18)
    p.drawString(100, 750, "Budget Tracker Report")

    p.setFont("Helvetica", 12)
    p.setFillColor(colors.green)
    p.drawString(100, 730, f"Name: {request.user.name}")
    p.drawString(100, 710, f"Email: {request.user.email}")
    p.drawString(100, 690, f"Phone: {request.user.phone}")  

    p.setFillColor(colors.black)
    p.setFont("Helvetica-Bold", 14)
    p.drawString(100, 670, "Category-wise Breakdown:")

    p.setFont("Helvetica", 12)
    p.setFillColor(colors.black)
    p.drawString(100, 650, f"Total Income: Rs.{total_income}")
    p.drawString(100, 630, f"Total Expenses: Rs.{total_expenses}")

    balance = total_income - total_expenses
    p.drawString(100, 610, f"Balance: Rs.{balance}")

    y_position = 590
    p.setFillColor(colors.darkgreen)
    p.drawString(100, y_position, "Income Details:")
    y_position -= 20
    for income in incomes:
        p.setFillColor(colors.blue)
        p.drawString(100, y_position, f"{income.category.name}: Rs.{income.amount} on {income.date}")
        y_position -= 20

    y_position -= 20
    p.setFillColor(colors.red)
    p.drawString(100, y_position, "Expense Details:")
    y_position -= 20
    for expense in expenses:
        p.setFillColor(colors.red)
        p.drawString(100, y_position, f"{expense.category.name}: Rs.{expense.amount} on {expense.date}")
        y_position -= 20

    p.showPage()
    p.save()

    buffer.seek(0)
    return HttpResponse(buffer, content_type='application/pdf')
