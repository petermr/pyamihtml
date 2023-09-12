from geopy.geocoders import Nominatim

from test.test_all import AmiAnyTest


class MiscTest(AmiAnyTest):

    def test_geolocate(self):
        geolocator = Nominatim(timeout=10, user_agent = "myGeolocator")
        for location in [
            "Delhi",
            "Mysore",
            "Benares",
            "Mumbai",
            "Bengaluru",
            "Ladakh",
        ]:
            location = geolocator.geocode(location)
            print(location)
            print((location.latitude, location.longitude))
