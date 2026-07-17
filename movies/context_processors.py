from .models import City

def location_context(request):
    cities = City.objects.all().order_by('name')
    selected_city_name = request.session.get('selected_city_name', 'Chennai')
    selected_city_id = request.session.get('selected_city_id')
    
    # If no city selected yet but cities exist, set a default
    if not selected_city_id and cities.exists():
        default_city = cities.first()
        selected_city_id = default_city.id
        selected_city_name = default_city.name
        
    return {
        'all_cities': cities,
        'selected_city_name': selected_city_name,
        'selected_city_id': selected_city_id,
    }
