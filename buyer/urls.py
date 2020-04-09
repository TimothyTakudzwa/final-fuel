from django.urls import path
from django.contrib.auth import views as auth_views

from . import views 


urlpatterns = [

    path('logout', auth_views.LogoutView.as_view(template_name='buyer/signin.html'), name='buyer-logout'),
    path('profile', views.profile, name='buyer-profile'),
    path('change_password', views.change_password, name='bchange-password'),
    path('delivery-branches', views.delivery_branches, name='delivery-branches'),
    path('create-branch', views.create_branch, name='create-branch'),
    path('edit-branch<int:id>', views.edit_branch, name='edit-branch'),
    path('accounts-status', views.account_application, name='accounts-status'),
    path('download-application/<int:id>', views.download_application, name='download-application'),
    path('upload-application/<int:id>', views.upload_application, name='upload-application'),
    path('release-note/<int:id>', views.view_release_note, name='release-note'),
    path('', views.dashboard, name='buyer-dashboard'),
    path('fuel', views.fuel_request, name='buyer-fuel-request'),
    path('offers/<int:id>', views.offers, name='fuel-offers'),
    path('transaction_review/delete/<int:id>', views.transactions_review_delete, name='tran-review-delete'),
    path('transaction_review/edit/<int:id>', views.transaction_review_edit, name='tran-review-edit'),
    path('accept/<int:id>', views.accept_offer, name='accept-offer'),
    path('reject/<int:id>', views.reject_offer, name='reject-offer'),
    path('transactions', views.transactions, name='buyer-transactions'),
    path('delivery-schedule/', views.delivery_schedules, name="delivery-schedule"),
    # path('delivery-schedule/<int:id>', views.delivery_schedule, name="delivery-schedule"),
    path('proof-of-payment/<int:id>', views.proof_of_payment, name="proof-of-payment"),
    path('invoice/<int:id>', views.invoice, name='buyer-invoice'),
    path('view_invoice/<int:id>', views.view_invoice, name='view-invoice'),
    path('accounts', views.accounts, name='accounts'),
    path('payment_history/<int:id>', views.payment_history, name='payment_history'),
    path('make_direct_request', views.make_direct_request, name='make_direct_request'),
    path('make_private_request', views.make_private_request, name='make_private_request'),
    path('edit_account_details/<int:id>', views.edit_account_details, name="edit_account_details"),
    path('payment_release_notes/<int:id>', views.payment_release_notes, name='payment_release_notes'),
    path('delivery_note/<int:id>', views.delivery_note, name='delivery_note'),
    path('download_release_note/<int:id>', views.download_release_note, name='download_release_note'),
    path('download_pop/<int:id>', views.download_pop, name='download_pop'),
    path('company_profile/', views.company_profile, name='company_profile'),
    path('activity/', views.activity, name='activity')

    

]

