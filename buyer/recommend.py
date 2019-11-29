from supplier.models import Profile, SupplierRating, FuelReques, Offer
from company.models import FuelUpdate
from buyer.models import FuelRequest
from django.contrib.auth.models import User

def recommend(fuel_type, quantity, user_id, price):
    status = False
    supplies = FuelUpdate.objects.filter(max_amount__lte=quantity, min_amount__gte=quantity, fuel_type__icontains=fuel_type).order_by('-price')       
    if supplies.count() == 0:
        return status
    else:
        scoreboard = {}
        print(f"Supplies : {scoreboard}") 
        for supplier in supplies: 
            scoreboard[supplier.id] = round(supplier.price * 0.6, 2)       
        for key,value in scoreboard:
            supplier_profile = Profile.objects.get(id=key)
            ratings = SupplierRating.objects.filter(supplier=supplier_profile)  
            total_rating = 0          
            for rating in ratings:
                total_rating += rating.rating  
            scoreboard[key] = value + (total_rating * 0.4)
            total_rating = 0
        print(f"Scoreboard : {scoreboard}")
        max_rate_provider = max(scoreboard.items(), key=operator.itemgetter(1))[0]
        print(f"Max Rate Provider : {max_rate_provider}")
        
        selected_supply = FuelUpdate.objects.get(id=max_rate_provider)
        supplier_user = selected_supply.supplier.company.company_name
        request_user = FuelRequest.objects.get(id=user_id)
        offer = Offer.objects.create(quantity=quantity, supplier=supplier_user, request=request_user, price=price)
        return offer.id


