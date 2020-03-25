from django.shortcuts import render, redirect

def landing_page(request):
    if request.user.is_authenticated:
        current_user = request.user
        if current_user.user_type == "BUYER":
            return redirect("buyer-dashboard")
        elif current_user.user_type == 'SS_SUPPLIER':
            if current_user.password_reset:
                return redirect("serviceStation:initial-password-change")
            else:
                return redirect("serviceStation:home")
        elif current_user.user_type == 'SUPPLIER':
            if current_user.password_reset:
                return redirect("supplier:initial-password-change")
            else:
                return redirect("fuel-request")
        elif current_user.user_type == 'S_ADMIN':
            if current_user.password_reset:
                return redirect("users:initial-password-change")
            else:
                return redirect("users:allocate")
        elif current_user.user_type == 'ZERA':
            return redirect("zeraPortal:dashboard")
        elif current_user.user_type == 'NOIC_STAFF':
            if current_user.password_reset:
                return redirect("noicDepot:initial-password-change")
            else:
                return redirect("noicDepot:orders")
        elif current_user.user_type == 'NOIC_ADMIN':
            return redirect("noic:dashboard")
    return render(request, 'buyer/index.html')

def verify(request):
    return render(request, 'buyer/godaddy.html')
