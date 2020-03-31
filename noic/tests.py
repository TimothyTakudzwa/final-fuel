from django.test import TestCase

zimbabwean_towns = ['Select City ---', 'Beitbridge', 'Bindura', 'Bulawayo', 'Chinhoyi', 'Chirundu', 'Gweru', 'Harare',
                    'Hwange', 'Juliusdale', 'Kadoma', 'Kariba', 'Karoi', 'Kwekwe', 'Marondera', 'Masvingo', 'Mutare',
                    'Mutoko', 'Nyanga', 'Victoria Falls']

Harare = ['Avenues', 'Budiriro', 'Dzivaresekwa', 'Kuwadzana', 'Warren Park', 'Glen Norah', 'Glen View', 'Avondale',
              'Belgravia', 'Belvedere', 'Eastlea', 'Gun Hill', 'Milton Park', 'Borrowdale', 'Chisipiti', 'Glen Lorne',
              'Greendale', 'Greystone Park', 'Helensvale', 'Highlands', 'Mandara', 'Manresa', 'Msasa', 'Newlands',
              'The Grange', 'Ashdown Park', 'Avonlea', 'Bluff Hill', 'Borrowdale', 'Emerald Hill', 'Greencroft',
              'Hatcliffe', 'Mabelreign', 'Marlborough', 'Meyrick Park', 'Mount Pleasant', 'Pomona', 'Tynwald',
              'Vainona', 'Arcadia', 'Braeside', 'CBD', 'Cranbourne', 'Graniteside', 'Hillside', 'Queensdale',
              'Sunningdale', 'Epworth', 'Highfield' 'Kambuzuma', 'Southerton', 'Warren Park', 'Southerton', 'Mabvuku',
              'Tafara', 'Mbare', 'Prospect', 'Ardbennie', 'Houghton Park', 'Marimba Park', 'Mufakose']

Bulawayo = ['New Luveve', 'Newsmansford', 'Newton', 'Newton West', 'Nguboyenja', 'Njube', 'Nketa', 'Nkulumane',
                'North End', 'Northvale', 'North Lynne', 'Northlea', 'North Trenance', 'Ntaba Moyo', 'Ascot',
                'Barbour Fields', 'Barham Green', 'Beacon Hill', 'Belmont Industrial area', 'Bellevue', 'Belmont',
                'Bradfield']

Mutare = ['Murambi', 'Hillside', 'Fairbridge Park', 'Morningside', 'Tigers Kloof', 'Yeovil', 'Westlea', 'Florida',
              'Chikanga', 'Garikai', 'Sakubva', 'Dangamvura', 'Weirmouth', 'Fern Valley', 'Palmerstone', 'Avenues',
              'Utopia', 'Darlington', 'Greeside', 'Greenside Extension', 'Toronto', 'Bordervale', 'Natview Park',
              'Mai Maria', 'Gimboki', 'Musha Mukadzi']

Gweru = ['Gweru East', 'Woodlands Park', 'Kopje', 'Mtausi Park', 'Nashville', 'Senga', 'Hertifordshire', 'Athlone',
             'Daylesford', 'Mkoba', 'Riverside', 'Southview', 'Nehosho', 'Clydesdale Park', 'Lundi Park', 'Montrose',
             'Ascot', 'Ridgemont', 'Windsor Park', 'Ivene', 'Haben Park', 'Bata', 'ThornHill Air Field' 'Green Dale',
             'Bristle', 'Southdowns']

Harare.sort()
Bulawayo.sort()
Mutare.sort()
Gweru.sort()

print(Harare)
print(Bulawayo)
print(Mutare)
print(Gweru)


Harare = ['Arcadia', 'Ardbennie', 'Ashdown Park', 'Avenues', 'Avondale', 'Avonlea', 'Belgravia', 'Belvedere', 'Bluff Hill', 'Borrowdale', 'Borrowdale', 'Braeside', 'Budiriro', 'CBD', 'Chisipiti', 'Cranbourne', 'Dzivaresekwa', 'Eastlea', 'Emerald Hill', 'Epworth', 'Glen Lorne', 'Glen Norah', 'Glen View', 'Graniteside', 'Greencroft', 'Greendale', 'Greystone Park', 'Gun Hill', 'Hatcliffe', 'Helensvale', 'HighfieldKambuzuma', 'Highlands', 'Hillside', 'Houghton Park', 'Kuwadzana', 'Mabelreign', 'Mabvuku', 'Mandara', 'Manresa', 'Marimba Park', 'Marlborough', 'Mbare', 'Meyrick Park', 'Milton Park', 'Mount Pleasant', 'Msasa', 'Mufakose', 'Newlands', 'Pomona', 'Prospect', 'Queensdale', 'Southerton', 'Southerton', 'Sunningdale', 'Tafara', 'The Grange', 'Tynwald', 'Vainona', 'Warren Park', 'Warren Park']
BUlawayo = ['Ascot', 'Barbour Fields', 'Barham Green', 'Beacon Hill', 'Bellevue', 'Belmont', 'Belmont Industrial area', 'Bradfield', 'New Luveve', 'Newsmansford', 'Newton', 'Newton West', 'Nguboyenja', 'Njube', 'Nketa', 'Nkulumane', 'North End', 'North Lynne', 'North Trenance', 'Northlea', 'Northvale', 'Ntaba Moyo']
Mutare = ['Avenues', 'Bordervale', 'Chikanga', 'Dangamvura', 'Darlington', 'Fairbridge Park', 'Fern Valley', 'Florida', 'Garikai', 'Gimboki', 'Greenside Extension', 'Greeside', 'Hillside', 'Mai Maria', 'Morningside', 'Murambi', 'Musha Mukadzi', 'Natview Park', 'Palmerstone', 'Sakubva', 'Tigers Kloof', 'Toronto', 'Utopia', 'Weirmouth', 'Westlea', 'Yeovil']
Gweru = ['Ascot', 'Athlone', 'Bata', 'Bristle', 'Clydesdale Park', 'Daylesford', 'Gweru East', 'Haben Park', 'Hertifordshire', 'Ivene', 'Kopje', 'Lundi Park', 'Mkoba', 'Montrose', 'Mtausi Park', 'Nashville', 'Nehosho', 'Ridgemont', 'Riverside', 'Senga', 'Southdowns', 'Southview', 'ThornHill Air FieldGreen Dale', 'Windsor Park', 'Woodlands Park']
