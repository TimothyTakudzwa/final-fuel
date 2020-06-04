@login_required()
@user_role
def fuel_request(request):
    notifications, num_of_notifications = notifications_retriever(request.user)
    sub = Subsidiaries.objects.filter(id=request.user.subsidiary_id).first()
    requests = []
    acceptable_requests = []
    complete_requests = []
    
    if sub.praz_reg_num != None:
        all_requests = FuelRequest.objects.filter(is_deleted=False, is_complete=False).all()
        for fuel_request in all_requests:
            if not fuel_request.is_direct_deal and not fuel_request.private_mode:
                requests.append(fuel_request)
            elif fuel_request.is_direct_deal and not fuel_request.private_mode:
                if fuel_request.last_deal == request.user.subsidiary_id:
                    requests.append(fuel_request)
                else:
                    pass
            elif not fuel_request.is_direct_deal and fuel_request.private_mode:
                account_exists = Account.objects.filter(supplier_company=request.user.company,
                                                        buyer_company=fuel_request.name.company).exists()
                if account_exists:
                    requests.append(fuel_request)
                else:
                    pass
            elif fuel_request.is_direct_deal and fuel_request.private_mode:
                if fuel_request.supplier_company == request.user.company:
                    requests.append(fuel_request)
                else:
                    pass
            else:
                pass
        requests.sort(key=attrgetter('date', 'time'), reverse=True)
    else:
        all_requests = FuelRequest.objects.filter(~Q(name__company__is_govnt_org=True)).filter(is_deleted=False,
                                                                                               wait=True,
                                                                                               is_complete=False).all()
        for fuel_request in all_requests:
            if not fuel_request.is_direct_deal and not fuel_request.private_mode:
                requests.append(fuel_request)
            elif fuel_request.is_direct_deal and not fuel_request.private_mode:
                if fuel_request.last_deal == request.user.subsidiary_id:
                    requests.append(fuel_request)
                else:
                    pass
            elif not fuel_request.is_direct_deal and fuel_request.private_mode:
                account_exists = Account.objects.filter(supplier_company=request.user.company,
                                                        buyer_company=fuel_request.name.company).exists()
                if account_exists:
                    requests.append(fuel_request)
                else:
                    pass
            elif fuel_request.is_direct_deal and fuel_request.private_mode:
                if fuel_request.supplier_company == request.user.company:
                    requests.append(fuel_request)
                else:
                    pass
            else:
                pass
        requests.sort(key=attrgetter('date', 'time'), reverse=True)

    for buyer_request in requests:
        if buyer_request.payment_method == 'USD':
            fuel = SuballocationFuelUpdate.objects.filter(subsidiary__id=request.user.subsidiary_id).filter(
                payment_type='USD').first()
        elif buyer_request.payment_method == 'RTGS':
            fuel = SuballocationFuelUpdate.objects.filter(subsidiary__id=request.user.subsidiary_id).filter(
                payment_type='RTGS').first()
        elif buyer_request.payment_method == 'USD & RTGS':
            fuel = SuballocationFuelUpdate.objects.filter(subsidiary__id=request.user.subsidiary_id).filter(
                payment_type='USD & RTGS').first()
        else:
            fuel = None
        if buyer_request.dipping_stick_required == buyer_request.meter_required == buyer_request.pump_required == False:
            buyer_request.no_equipment = True
        if buyer_request.cash == buyer_request.ecocash == buyer_request.swipe == buyer_request.usd == False:
            buyer_request.no_payment = True
        # if not buyer_request.delivery_address.strip():
        #     buyer_request.delivery_address = f'N/A'
        if Offer.objects.filter(supplier_id=request.user, request_id=buyer_request).exists():
            offer = Offer.objects.filter(supplier_id=request.user, request_id=buyer_request).first()
            buyer_request.my_offer = f'{offer.quantity}ltrs @ ${offer.price}'
            buyer_request.offer_price = offer.price
            buyer_request.offer_quantity = offer.quantity
            buyer_request.offer_id = offer.id
            buyer_request.transport_fee = offer.transport_fee
        else:
            buyer_request.my_offer = 'No Offer'
            buyer_request.offer_id = 0
        if fuel:
            if buyer_request.fuel_type.lower() == 'petrol':

                buyer_request.price = fuel.petrol_price
            else:
                buyer_request.price = fuel.diesel_price
        else:
            buyer_request.price = 0.00
        complete_requests = FuelRequest.objects.filter(is_complete=True).all()
        for buyer_request in complete_requests:
            if buyer_request.dipping_stick_required == buyer_request.meter_required == buyer_request.pump_required == False:
                buyer_request.no_equipment = True
    
    for reqq in requests:
        if reqq is not None:
            if sub.is_usd_active == True:
                acceptable_requests.append(reqq)
            else:
                if reqq.payment_method != 'USD':
                    acceptable_requests.append(reqq)
                else:
                    pass


    if request.method == "POST":
        if request.POST.get('start_date') and request.POST.get('end_date') :
            filtered = True;
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            if start_date:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
                start_date = start_date.date()
            if end_date:
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
                end_date = end_date.date()
            
            sub = Subsidiaries.objects.filter(id=request.user.subsidiary_id).first()
            requests = []
            acceptable_requests = []
            complete_requests = []

            if sub.praz_reg_num != None:
                all_requests = FuelRequest.objects.filter(is_deleted=False, is_complete=False).filter(date__range=[start_date, end_date])
            else:
                all_requests = FuelRequest.objects.filter(~Q(name__company__is_govnt_org=True)).filter(is_deleted=False,
                                                                                                    wait=True,
                                                                                                    is_complete=False).all()
            
            for fuel_request in all_requests:
                if not fuel_request.is_direct_deal and not fuel_request.private_mode:
                    requests.append(fuel_request)
                elif fuel_request.is_direct_deal and not fuel_request.private_mode:
                    if fuel_request.last_deal == request.user.subsidiary_id:
                        requests.append(fuel_request)
                    else:
                        pass
                elif not fuel_request.is_direct_deal and fuel_request.private_mode:
                    account_exists = Account.objects.filter(supplier_company=request.user.company,
                    buyer_company=fuel_request.name.company).exists()
                    if account_exists:
                        requests.append(fuel_request)
                    else:
                        pass
                elif fuel_request.is_direct_deal and fuel_request.private_mode:
                    if fuel_request.supplier_company == request.user.company:
                        requests.append(fuel_request)
                    else:
                        pass
                else:
                    pass

                requests.sort(key=attrgetter('date', 'time'), reverse=True)

            for buyer_request in requests:
                if buyer_request.payment_method == 'USD':
                    fuel = SuballocationFuelUpdate.objects.filter(subsidiary__id=request.user.subsidiary_id).filter(
                        payment_type='USD').first()
                elif buyer_request.payment_method == 'RTGS':
                    fuel = SuballocationFuelUpdate.objects.filter(subsidiary__id=request.user.subsidiary_id).filter(
                        payment_type='RTGS').first()
                elif buyer_request.payment_method == 'USD & RTGS':
                    fuel = SuballocationFuelUpdate.objects.filter(subsidiary__id=request.user.subsidiary_id).filter(
                        payment_type='USD & RTGS').first()
                else:
                    fuel = None
                if buyer_request.dipping_stick_required == buyer_request.meter_required == buyer_request.pump_required == False:
                    buyer_request.no_equipment = True
                if buyer_request.cash == buyer_request.ecocash == buyer_request.swipe == buyer_request.usd == False:
                    buyer_request.no_payment = True
                # if not buyer_request.delivery_address.strip():
                #     buyer_request.delivery_address = f'N/A'
                if Offer.objects.filter(supplier_id=request.user, request_id=buyer_request).exists():
                    offer = Offer.objects.filter(supplier_id=request.user, request_id=buyer_request).first()
                    buyer_request.my_offer = f'{offer.quantity}ltrs @ ${offer.price}'
                    buyer_request.offer_price = offer.price
                    buyer_request.offer_quantity = offer.quantity
                    buyer_request.offer_id = offer.id
                    buyer_request.transport_fee = offer.transport_fee
                else:
                    buyer_request.my_offer = 'No Offer'
                    buyer_request.offer_id = 0
                if fuel:
                    if buyer_request.fuel_type.lower() == 'petrol':

                        buyer_request.price = fuel.petrol_price
                    else:
                        buyer_request.price = fuel.diesel_price
                else:
                    buyer_request.price = 0.00
                complete_requests = FuelRequest.objects.filter(is_complete=True).all()
                for buyer_request in complete_requests:
                    if buyer_request.dipping_stick_required == buyer_request.meter_required == buyer_request.pump_required == False:
                        buyer_request.no_equipment = True

            for reqq in requests:
                if reqq is not None:
                    if sub.is_usd_active == True:
                        acceptable_requests.append(reqq)
                    else:
                        if reqq.payment_method != 'USD':
                            acceptable_requests.append(reqq)
                        else:
                            pass

            context = {
                'notifications': notifications,
                'num_of_notifications': num_of_notifications,
                'acceptable_requests': acceptable_requests,
                'requests': requests,
                'complete_requests': complete_requests,
                'start_date': start_date,
                'end_date': end_date
            }

            return render(request, 'supplier/fuel_request.html', context=context)

        if request.POST.get('export_to_csv')=='csv':
            start_date = request.POST.get('csv_start_date')
            end_date = request.POST.get('csv_end_date')
            if start_date:
                start_date = datetime.strptime(start_date, '%b %d, %Y')
                start_date = start_date.date()
            if end_date:
                end_date = datetime.strptime(end_date, '%b %d, %Y')
                end_date = end_date.date()
            if end_date and start_date:
                filtered_activities = Activity.objects.filter(user=request.user).filter(date__range=[start_date, end_date])
                      
            fields = ['date','time', 'company__name', 'action', 'description', 'reference_id']
            
            if filtered_activities:
                filtered_activities = filtered_activities.values('date','time', 'company__name', 'action', 'description', 'reference_id')
                df = pd.DataFrame(filtered_activities, columns=fields)
            else:
                df_current = pd.DataFrame(current_activities.values('date','time', 'company__name', 'action', 'description', 'reference_id'), columns=fields)
                df_previous = pd.DataFrame(activities.values('date','time', 'company__name', 'action', 'description', 'reference_id'), columns=fields)
                df = df_current.append(df_previous)

            filename = f'{request.user.company.name}'
            df.columns = ['Date','Time', 'Company', 'Action', 'Description', 'Reference Id']
            df.to_csv(filename, index=None, header=True)

            with open(filename, 'rb') as csv_name:
                response = HttpResponse(csv_name.read())
                response['Content-Disposition'] = f'attachment;filename={filename} - Activity - {today}.csv'
                return response     

        else:
            start_date = request.POST.get('pdf_start_date')
            end_date = request.POST.get('pdf_end_date')
            if start_date:
                start_date = datetime.strptime(start_date, '%b %d, %Y')
                start_date = start_date.date()
            if end_date:
                end_date = datetime.strptime(end_date, '%b %d, %Y')
                end_date = end_date.date()
            if end_date and start_date:
                filtered_activities = Activity.objects.filter(user=request.user).filter(date__range=[start_date, end_date])

            context = {
                'notifications': notifications,
                'num_of_notifications': num_of_notifications,
                'acceptable_requests': acceptable_requests,
                'requests': requests,
                'complete_requests': complete_requests
            }

            html_string = render_to_string('supplier/export/export_activities.html', context=context)
            html = HTML(string=html_string)
            export_name = f"{request.user.company.name}"
            html.write_pdf(target=f'media/transactions/{export_name}.pdf')

            download_file = f'media/transactions/{export_name}'

            with open(f'{download_file}.pdf', 'rb') as pdf:
                response = HttpResponse(pdf.read(), content_type="application/vnd.pdf")
                response['Content-Disposition'] = f'attachment;filename={export_name} - Activities - {today}.pdf'
                return response
                

    
    return render(request, 'supplier/fuel_request.html', {'notifications': notifications, 'num_of_notifications': num_of_notifications, 'acceptable_requests': acceptable_requests, 'requests': requests, 'complete_requests': complete_requests})