# Import parent dir
import os
import sys
import argparse
from csv import reader
currentdir = os.path.dirname(os.path.abspath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "opacity_api.settings")
django.setup()

# Django imports
from api.models import Product, Company


## CellType
##########
company = Company.objects.first()
print("-- Creating CELL TYPES --")
Product.objects.all().delete()
with open(currentdir + '/./opacity_products_manager.csv', 'r') as read_obj:
  # pass the file object to reader() to get the reader object
  csv_reader = reader(read_obj)
  
  # This skips the first row of the CSV file.
  row = next(csv_reader)
  #print("Header ", row)

  product_list = []
  for row in csv_reader:
    # row variable is a list that represents a row in csv
    product = Product(company=company, seller_sku=row[0], asin=row[1], name=row[2], listing_id=row[3],
            status=row[6], variant_type=row[7], 
            category1=row[8], category2=row[9], 
            product_type=row[10], color=row[11], size=row[12],
            custom_label0=row[13], custom_label1=row[14],
            custom_label2=row[15], custom_label3=row[16],
            custom_label4=row[17])
    product_list.append(product)
  

  Product.objects.bulk_create( product_list )

print("created ", Product.objects.all().count() )