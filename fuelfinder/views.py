from django.shortcuts import render, redirect

def landing_page(request):
    if request.user.is_authenticated:
        current_user = request.user
        if current_user.user_type == "BUYER":
            return redirect("buyer-dashboard")
        elif current_user.user_type == 'SS_SUPPLIER':
            return redirect("serviceStation:home")
        elif current_user.user_type == 'SUPPLIER':
            return redirect("fuel-request")
        elif current_user.user_type == 'S_ADMIN':
            return redirect("users:allocate")
        elif current_user.user_type == 'ZERA':
            return redirect("zeraPortal:dashboard")
        elif current_user.user_type == 'NOIC_STAFF':
            return redirect("noicDepot:orders")
        elif current_user.user_type == 'NOIC_ADMIN':
            return redirect("noic:dashboard")
    return render(request, 'buyer/index.html')

def verify(request):
    return render(request, 'buyer/godaddy.html')
