from django.contrib.auth import authenticate, update_session_auth_hash
from django.core.mail import EmailMultiAlternatives
from django.core.mail.message import BadHeaderError
from django.http.response import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from django.contrib.auth import get_user_model

from buyer.models import User
from supplier.models import Subsidiaries, SubsidiaryFuelUpdate
from users.models import Audit_Trail
from comments.models import CommentsPermission, Comment

import secrets
from datetime import date
from fuelfinder import settings

from whatsapp.helper_functions import sord_update

user = get_user_model()
today = date.today()


@csrf_exempt
@api_view(['POST'])
def login(request):
    if request.method == 'POST':
        # fetch details
        username = request.POST.get('username')
        password = request.POST.get('password')
        # authenticate user
        status = authenticate(username=username, password=password)
        if status:
            # auth success
            user = User.objects.get(username=username)
            # service station admin and must reset password
            if user.user_type == 'SS_SUPPLIER' and user.password_reset:
                data = {'username': user.username}
                return JsonResponse(status=201, data=data)
            # service station admin
            elif user.user_type == 'SS_SUPPLIER':
                data = {'username': user.username}
                return JsonResponse(status=200, data=data)
            # wrong details
            else:
                return HttpResponse(status=403)
        # no account
        else:
            return HttpResponse(status=401)


@csrf_exempt
@api_view(['POST'])
def login_user(request):
    if request.method == 'POST':
        # user details
        username = request.POST.get('username')
        password = request.POST.get('password')
        # authenticating
        check = User.objects.filter(username=username)
        if check.exists():
            status = authenticate(username=username, password=password)
            # auth success
            if status:
                user = User.objects.get(username=username)
                # user must reset password
                if user.password_reset:
                    data = {'username': user.username}
                    return JsonResponse(status=201, data=data)
                # login
                else:
                    data = {'username': user.username}
                    return JsonResponse(status=200, data=data)
            # wrong details
            else:
                return HttpResponse(status=401)
        # no account
        else:
            return HttpResponse(status=403)


@csrf_exempt
@api_view(['POST'])
def register(request):
    if request.method == 'POST':
        # fetch details
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        # checking for existing details
        email_check = User.objects.filter(email=email)
        username_check = User.objects.filter(username=username)
        # username check
        if username_check.exists():
            return HttpResponse(status=409)
        # email check
        elif email_check.exists():
            return HttpResponse(status=406)
        else:
            try:
                # creating account
                client = user.objects.create_user(username=username, email=email, password=password)
                client.phone_number = phone
                client.user_type = 'INDIVIDUAL'
                client.first_name = first_name
                client.last_name = last_name
                client.save()

                data = {'username': client.username}
                return JsonResponse(status=200, data=data)
            # password not meeting standards
            except:
                return HttpResponse(status=403)


@csrf_exempt
@api_view(['POST'])
def update_station(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        # fetch user data
        user = User.objects.get(username=username)
        # check for fuel station
        status = SubsidiaryFuelUpdate.objects.filter(subsidiary__id=user.subsidiary_id).first()
        # station exists
        if status:
            update = SubsidiaryFuelUpdate.objects.filter(subsidiary__id=user.subsidiary_id).first()

            previous_petrol = update.petrol_quantity
            previous_diesel = update.diesel_quantity

            # fetch details
            p_quantity = request.POST.get('petrol_quantity')
            d_quantity = request.POST.get('diesel_quantity')
            queue = request.POST.get('queue')
            s_status = request.POST.get('status')
            limit = request.POST.get('limit')
            swipe = request.POST.get('swipe')
            ecocash = request.POST.get('ecocash')
            cash = request.POST.get('cash')
            # payment method
            update.swipe = swipe
            update.ecocash = ecocash
            update.cash = cash
            # update other quanties
            update.petrol_quantity = p_quantity
            update.diesel_quantity = d_quantity
            update.queue_length = queue
            update.status = s_status
            update.limit = limit
            update.last_updated = today
            # save update
            update.save()

            # sord update
            sord_update(user, previous_diesel-float(d_quantity), 'Fuel Update', 'Diesel')
            sord_update(user, previous_petrol - float(p_quantity), 'Fuel Update', 'Petrol')

            # add audit trail
            Audit_Trail.objects.create(
                user=user,
                company=user.company,
                service_station=Subsidiaries.objects.filter(id=user.subsidiary_id).first(),
                action='Updating fuel quantities and station status via mobile app',
                reference='Fuel update',
                reference_id=update.id,
            )
            # success response
            return HttpResponse(status=200)
        # no station
        else:
            return HttpResponse(status=404)


@csrf_exempt
@api_view(['POST'])
def view_station_updates(request):
    if request.method == 'POST':
        # fetch username
        username = request.POST.get('username')
        # data to be returned
        data = []
        # get user data
        user = User.objects.get(username=username)
        # check if user has update object
        status = SubsidiaryFuelUpdate.objects.filter(subsidiary__id=user.subsidiary_id).first()
        # if update object exists
        if status:
            updates = SubsidiaryFuelUpdate.objects.filter(subsidiary__id=user.subsidiary_id)
            # fetching data
            for update in updates:
                company = Subsidiaries.objects.get(id=update.subsidiary.id)
                image = f'https://{request.get_host()}{company.logo.url}/'
                # end fetch
                station_update = {
                    'name': company.name, 'diesel_quantity': update.diesel_quantity,
                    'diesel_price': update.diesel_price, 'petrol_quantity': update.petrol_quantity,
                    'petrol_price': update.petrol_price, 'cash': update.cash, 'ecocash': update.ecocash,
                    'swipe': update.swipe, 'queue': update.queue_length, 'limit': update.limit,
                    'status': update.status, 'image': image, 'company': company.company.name
                }
                # add to dictionary
                data.append(station_update)
            return JsonResponse(list(data), status=200, safe=False)
        # error response
        else:
            return HttpResponse(status=403)


@csrf_exempt
@api_view(['POST'])
def view_updates_user(request):
    if request.method == 'POST':
        # data container
        data = []
        # fetch updates
        try:
            updates = SubsidiaryFuelUpdate.objects.filter(subsidiary__is_depot=False).all()
            for update in updates:
                image = f'https://{request.get_host()}{update.subsidiary.logo.url}/'
                if update.diesel_quantity == 0 and update.petrol_quantity == 0:
                    pass
                else:
                    station_update = {
                        'station': update.subsidiary.name, 'queue': update.queue_length, 'petrol': update.petrol_price,
                        'diesel': update.diesel_price, 'open': update.subsidiary.opening_time,
                        'close': update.subsidiary.closing_time, 'limit': update.limit, 'cash': update.cash,
                        'ecocash': update.ecocash, 'swipe': update.swipe, 'status': update.status,
                        'image': image, 'company': update.subsidiary.company.name,
                    }
                    data.append(station_update)
        # if error, skip object
        except:
            pass
        # after fetching data, return data
        finally:
            return JsonResponse(list(data), status=200, safe=False)


@csrf_exempt
@api_view(['POST'])
def get_profile(request):
    if request.method == 'POST':
        # fetch username
        username = request.POST.get('username')
        # profile data
        data = []
        # check if user exists
        check = User.objects.filter(username=username)
        if check.exists():
            client = User.objects.get(username=username)
            user_data = {'username': client.username, 'firstName': client.first_name,
                         'lastName': client.last_name, 'phone': client.phone_number, 'email': client.email}
            data.append(user_data)
            return JsonResponse(list(data), status=200, safe=False)
        # error response
        else:
            return HttpResponse(status=403)


@csrf_exempt
@api_view(['POST'])
def force_password_change(request):
    if request.method == 'POST':
        # fetch data
        username = request.POST.get('username')
        # get user
        check = User.objects.filter(username=username)
        # user exists
        if check.exists():
            new1 = request.POST.get('new1')
            new2 = request.POST.get('new2')
            # validation
            if new1 == new2:
                client = User.objects.get(username=username)
                client.set_password(new1)
                client.password_reset = False
                client.save()
                update_session_auth_hash(request, client)
                values = dict(user=client.username)
                return JsonResponse(status=200, data=values)
            # validation error
            else:
                return HttpResponse(status=401)
        # user doesn't exist
        else:
            return HttpResponse(status=403)


@csrf_exempt
@api_view(['POST'])
def change_password(request):
    if request.method == 'POST':
        # fetch username
        username = request.POST.get('username')
        # check if a user exists
        check = User.objects.filter(username=username)
        # user exists
        if check.exists():
            old = request.POST.get('old')
            new1 = request.POST.get('new1')
            new2 = request.POST.get('new2')
            # validation
            auth = authenticate(username=username, password=old)
            # validation too
            if auth and (new1 == new2):
                client = User.objects.get(username=username)
                client.set_password(new1)
                client.save()
                update_session_auth_hash(request, client)
                values = dict(user=client.username)
                return JsonResponse(status=200, data=values)
            # validation error
            else:
                return HttpResponse(status=401)
        # no validation
        else:
            return HttpResponse(status=403)


@csrf_exempt
@api_view(['POST'])
def password_reset(request):
    if request.method == 'POST':
        # fetch email
        email = request.POST.get('email')
        # check if email exists
        check = User.objects.filter(email=email)
        if check.exists():
            client = User.objects.get(email=email)
            # generate temporary password
            password = secrets.token_hex(3)
            client.set_password(password)
            # force password reset
            client.password_reset = True
            client.save()
            # update session incase user is logged on somewhere
            update_session_auth_hash(request, client)
            # set details for sending email
            sender = f'Fuel Finder Accounts<{settings.EMAIL_HOST_USER}>'
            title = 'Password Reset'
            message = f"Your account password was reset.Please use this password when signing in : \n" \
                      f"{password}\n" \
                      f"Remember to change the password when you sign in."
            # send email
            try:
                msg = EmailMultiAlternatives(title, message, sender, [email])
                msg.send()
                return HttpResponse(200)
            # if error occures
            except BadHeaderError:
                return HttpResponse(400)
        # user doesn't exist
        else:
            return HttpResponse(status=404)


@api_view(['POST'])
def update_comments(request):
    if request.method == 'POST':
        station = request.POST.get('station')
        company = request.POST.get('company')
        comment = request.POST.get('comment')
        username = request.POST.get('username')
        comment_type = request.POST.get('comment_type')

        permission = CommentsPermission.objects.filter().first()
        if permission.allowed:
            Comment.objects.create(
                user=User.objects.get(username=username),
                station=Subsidiaries.objects.get(name=station, company__name=company, is_depot=False),
                comment=comment,
                comment_type=comment_type
            )
            return HttpResponse(200)
        else:
            return HttpResponse(404)


@api_view(['POST'])
def view_comments(request):
    if request.method == 'POST':
        station = request.POST.get('station')
        company = request.POST.get('company')

        comments_data = []

        all_comments = Comment.objects.filter(station__name=station, station__company__name=company, date=today)
        if all_comments:
            for comment in all_comments:
                data = {
                    'name': comment.user.username, 'comment': comment.comment, 'type': comment.comment_type,
                    'date': comment.date.strftime('%a %d %B %y'), 'time': comment.time.strftime("%H:%M")
                }
                comments_data.append(data)
            return JsonResponse(list(comments_data), status=200, safe=False)
        else:
            return HttpResponse(status=404)
