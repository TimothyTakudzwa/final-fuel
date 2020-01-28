from supplier.models import  UserReview, Offer
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
        supplies = FuelUpdate.objects.filter(petrol_quantity__gte=fuel_request.amount, sub_type='Suballocation').filter(entry_type=fuel_request.payment_method).filter(~Q(petrol_price=0.00)).order_by('-petrol_price').all()      
    else:
        supplies = FuelUpdate.objects.filter(diesel_quantity__gte=fuel_request.amount, sub_type='Suballocation').filter(entry_type=fuel_request.payment_method).filter(~Q(diesel_price=0.00)).order_by('-diesel_price').all()    
    
    if supplies.count() == 0:        
        return status, "Nothing Found"
    else:
        scoreboard = {}
        for supplier in supplies: 
            if fuel_request.fuel_type == 'Petrol':
                scoreboard[str(supplier.relationship_id)] = round(float(supplier.petrol_price) * 0.7, 2) 
            else:                
                scoreboard[str(supplier.relationship_id)] = round(float(supplier.diesel_price) * 0.7, 2)
            
        for key in scoreboard:
            supplier_profile = Subsidiaries.objects.get(id=key)
            
            ratings = UserReview.objects.filter(depot__id=key).all()           
            total_rating = 0          
            if len(ratings) > 0:
                for rating in ratings:                   
                    total_rating += rating.rating
               
                scoreboard[key] = scoreboard[key] + round(float((total_rating/len(ratings))* -0.3), 2)
            else:
                total_rating = 0
        max_rate_provider = max(scoreboard.items(), key=operator.itemgetter(1))[0]
        user = User.objects.filter(subsidiary_id=max_rate_provider).first()
        price_object = FuelUpdate.objects.filter(relationship_id=max_rate_provider, sub_type='Suballocation').filter(entry_type=fuel_request.payment_method).first()
        selected_supply = Subsidiaries.objects.get(id=max_rate_provider)
        print(selected_supply.id)
        if fuel_request.fuel_type == 'Petrol':
            offer = Offer.objects.create(quantity=fuel_request.amount, supplier=user, request=fuel_request, price=price_object.petrol_price)
            response_message = recommender_response.format(selected_supply.company.name, selected_supply.name, fuel_request.fuel_type, fuel_request.amount, price_object.petrol_price)

        else:
            offer = Offer.objects.create(quantity=fuel_request.amount, supplier=user, request=fuel_request, price=price_object.diesel_price)
            
        response_message = recommender_response.format(selected_supply.company.name, selected_supply.name, fuel_request.fuel_type, fuel_request.amount, price_object.diesel_price)

        offer.save()
        response_message = "Here here"

        return offer.id, response_message


