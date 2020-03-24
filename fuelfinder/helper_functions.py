# Importing random to generate  
# random string sequence  
import random  
     
# Importing string library function  
import string  
     
def random_password():  
         
    # Takes random choices from  
    # ascii_letters and digits  
    generate_pass = ''.join([random.choice( string.ascii_uppercase + string.ascii_lowercase + string.digits)  
                                            for n in range(6)])  
                             
    return generate_pass