from supplier.models import  SupplierRating, Offer
from company.models import FuelUpdate
from buyer.models import FuelRequest
from supplier.models import Subsidiaries
from django.db.models import Q
import operator
from buyer.constants import recommender_response
from buyer.models import User

def recommend(fuel_request):
    status = False
    if fuel_request.fuel_type == "Petrol":
        supplies = FuelUpdate.objects.filter(petrol_quantity__gte=fuel_request.amount, sub_type='Depot').filter(~Q(petrol_price=0.00)).order_by('-petrol_price').all()      
    else:
        supplies = FuelUpdate.objects.filter(diesel_quantity__gte=fuel_request.amount, sub_type='Depot').filter(~Q(diesel_price=0.00)).order_by('-diesel_price').all()    
    
    if supplies.count() == 0:        
        return status, "Nothing Found"
    else:
        scoreboard = {}
        for supplier in supplies: 
            if fuel_request.fuel_type == 'Petrol':
                scoreboard[str(supplier.relationship_id)] = round(float(supplier.petrol_price) * 0.6, 2) 
            else:                
                scoreboard[str(supplier.relationship_id)] = round(float(supplier.diesel_price) * 0.6, 2)
        for key in scoreboard:
            supplier_profile = Subsidiaries.objects.get(id=key)
            ratings = SupplierRating.objects.filter(id =1).first()
            total_rating = 0          
            if ratings is not None:
                for rating in ratings:
                    total_rating += rating.rating  
                scoreboard[key] = scoreboard[key] + (total_rating * 0.4)
            total_rating = 0
        max_rate_provider = min(scoreboard.items(), key=operator.itemgetter(1))[0]
        user = User.objects.filter(subsidiary_id=max_rate_provider).first()
        price_object = FuelUpdate.objects.filter(relationship_id=max_rate_provider, sub_type='Depot').first()
        selected_supply = Subsidiaries.objects.get(id=max_rate_provider)
        if fuel_request.fuel_type == 'Petrol':
            offer = Offer.objects.create(quantity=fuel_request.amount, supplier=user, request=fuel_request, price=price_object.petrol_price)
            response_message = recommender_response.format(selected_supply.company.name, selected_supply.name, fuel_request.fuel_type, fuel_request.amount, price_object.petrol_price)

        else:
            offer = Offer.objects.create(quantity=fuel_request.amount, supplier=user, request=fuel_request, price=price_object.diesel_price)
        response_message = recommender_response.format(selected_supply.company.name, selected_supply.name, fuel_request.fuel_type, fuel_request.amount, price_object.diesel_price)

        offer.save()
        response_message = "Here here"

        return offer.id


