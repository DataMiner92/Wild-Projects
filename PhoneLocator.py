import phonenumbers

number = "+255700222888"

from phonenumbers import geocoder, carrier, timezone

ch_number = phonenumbers.parse(number, "CH")
print("Location:", geocoder.description_for_number(ch_number, "en"))

service_number = phonenumbers.parse(number, "RO")
carrier_name = carrier.name_for_number(service_number, "en")
if carrier_name:
    print("Carrier:", carrier_name)
    print("Status: Active")
else:
    print("Status: Inactive")


time_zone = timezone.time_zones_for_number(ch_number)
if time_zone:
    print("Time Zone:", time_zone[0])  
else:
    print("Time Zone: Not available")
