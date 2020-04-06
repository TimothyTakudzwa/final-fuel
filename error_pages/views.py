from django.shortcuts import render, redirect


def error_400(request, exception):
    context = {
        'title': '400',
        'data': exception
    }
    return render(request, 'error_pages/400.html', context=context)


def error_403(request, exception):
    context = {
        'title': '403',
        'data': exception
    }
    return render(request, 'error_pages/403.html', context=context)


def error_404(request, exception):
    context = {
        'title': '404',
        'data': exception
    }
    return render(request, 'error_pages/404.html', context=context)


def error_500(request):
    context = {
        'title': '500',
    }
    return render(request, 'error_pages/500.html', context=context)


def csrf_failure(request, reason=""):
    context = {
        'title': 'CSRF',
    }
    return redirect('login')


