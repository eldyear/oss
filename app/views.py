from django.http import JsonResponse
from django.shortcuts import render
from .models import InfTablo
from django.core.cache import cache
import requests
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)  # Логгер для отладки

today = datetime.today().date()
tomorrow = today + timedelta(days=1)

def get_flights(direction):
    """Общий метод для получения данных рейсов."""
    return (
        InfTablo.objects.filter(
            direction=direction,
            date1__gte=today,
            date1__lte=tomorrow
        )
        .select_related('airline', 'flight', 'status', 'destination')
        .prefetch_related('stoika')
        .order_by('date1')
    )


def serialize_flight(item, lang='en', weather_data=None):
    """Сериализация данных рейса с добавлением информации о погоде."""
    return {
        'flight': item.flight.flights,
        'direction': item.direction,
        'destination': {
            'city_name': getattr(item.destination, f"city_name_{lang}"),
            'iata_code': item.destination.iata_code,
        },
        'stoika': [stoika.stoiki for stoika in item.stoika.all()],
        'airline': {
            'name': item.airline.name,
            'svg_logo': item.airline.svg_logo.url if item.airline.svg_logo else None
        },
        'date1': item.date1.strftime('%d.%m.%y'),
        'time1': item.time1.strftime('%H:%M'),
        'last_date': item.last_date.strftime('%d.%m.%y') if item.last_date else None,
        'last_time': item.last_time.strftime('%H:%M') if item.last_time else None,
        'status': {
            'id': item.status.status_id if item.status else None,
            'name': getattr(item.status, f"name_{lang}") if item.status else None,
        },
        'weather': {
            'icon': f"/media/weather_icons/SVG/{weather_data['icon']}.svg" if weather_data else None,
            'temperature': f"{weather_data['temperature']}°C" if weather_data else "N/A"
        } if weather_data else None
    }


def get_weather_data(city):
    """Получает и кэширует данные о погоде для заданного города."""
    cache_key = f"weather_data_{city}"
    weather_data = cache.get(cache_key)

    if not weather_data:
        try:
            api_key = "key"
            url = "http://api.openweathermap.org/data/2.5/weather"
            params = {"q": city, "appid": api_key, "units": "metric"}
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            weather_data = {
                'icon': data["weather"][0]["icon"],
                'temperature': int(data["main"]["temp"])
            }
            cache.set(cache_key, weather_data, timeout=600)
        except requests.RequestException as e:
            logger.error(f"Ошибка получения погоды для {city}: {e}")
            weather_data = None

    return weather_data


def tablo_dep(request, lang='en'):
    """Возвращает данные о вылетающих рейсах с учетом выбранного языка."""
    flights = get_flights('dep')  # Получаем все рейсы на вылет
    data = [serialize_flight(item, lang) for item in flights]  # Передаем язык в сериализацию
    return JsonResponse({'data': data}, safe=False)  # Возвращаем данные в формате JSON


def tablo_arr(request, lang='en'):
    """Возвращает данные о вылетающих рейсах с учетом выбранного языка."""
    flights = get_flights('arr')  # Получаем все рейсы на вылет
    data = [serialize_flight(item, lang) for item in flights]  # Передаем язык в сериализацию
    return JsonResponse({'data': data}, safe=False)  # Возвращаем данные в формате JSON


def get_flight_data_check(request, lang, pk=None):
    """Возвращает данные рейсов с добавлением информации о погоде."""
    flights = InfTablo.objects.filter(
        direction='dep',
        status__name_en='Check-in',
        date1__gte=today,
        date1__lte=tomorrow,
    )

    # Фильтрация по стойке, если pk указан
    if pk:
        flights = flights.filter(stoika__stoiki=pk)

    flights = flights.select_related('airline', 'flight', 'destination').prefetch_related('stoika').order_by('date1')

    data = []
    for item in flights:
        city = item.destination.city_name_en
        weather_data = get_weather_data(city)
        data.append(serialize_flight(item, lang, weather_data))

    if len(data) > 2:
        return JsonResponse({"error": "Количество рейсов превышает допустимый лимит (2)."}, status=400)

    return JsonResponse({"data": data} if data else {"advert": "Ваша реклама могла бы осветить этот экран!"}, status=200)

def get_flight_data_gate(request, lang, pk=None):
    """Возвращает данные рейсов с добавлением информации о погоде."""
    flights = InfTablo.objects.filter(
        direction='dep',
        status__name_en='Boarding',
        date1__gte=today,
        date1__lte=tomorrow,
    )

    # Фильтрация по стойке, если pk указан
    if pk:
        flights = flights.filter(gate__gate=pk)

    flights = flights.select_related('airline', 'flight', 'destination').prefetch_related('gate').order_by('date1')

    data = []
    for item in flights:
        city = item.destination.city_name_en
        weather_data = get_weather_data(city)
        data.append(serialize_flight(item, lang, weather_data))

    if len(data) > 2:
        return JsonResponse({"error": "Количество рейсов превышает допустимый лимит (2)."}, status=400)

    return JsonResponse({"data": data} if data else {"advert": "Ваша реклама могла бы осветить этот экран!"}, status=200)

def get_flight_data_bag(request, lang, pk=None):
    """Возвращает данные рейсов."""
    flights = InfTablo.objects.filter(
        direction='arr',
        status__name_en='Arrived/Baggage',
        date1__gte=today,
        date1__lte=tomorrow,
    )

    # Фильтрация по стойке, если pk указан
    if pk:
        flights = flights.filter(stoika__stoiki=pk)

    flights = flights.select_related('airline', 'flight', 'destination').prefetch_related('stoika').order_by('date1')

    data = []
    for item in flights:
        data.append(serialize_flight(item, lang))

    if len(data) > 2:
        return JsonResponse({"error": "Количество рейсов превышает допустимый лимит (2)."}, status=400)

    return JsonResponse({"data": data} if data else {"advert": "Ваша реклама могла бы осветить этот экран!"}, status=200)

def departure(request):
    """Рендерит страницу для вылетающих рейсов."""
    return render(request, 'app/departure_ajax.html')


def arrival(request):
    """Рендерит страницу для прилетающих рейсов."""
    return render(request, 'app/arrival.html')

def iframe_dep(request):
    """Рендерит страницу для прилетающих рейсов."""
    return render(request, 'app/iframe_dep.html')

def iframe_arr(request):
    """Рендерит страницу для прилетающих рейсов."""
    return render(request, 'app/iframe_arr.html')

def deparr(request):
    """Рендерит страницу для прилетающих рейсов."""
    return render(request, 'app/deparr.html')

def my_urls(request):
    """Рендерит страницу для прилетающих рейсов."""
    return render(request, 'app/my_urls.html')


def check_ajax(request, pk):
    """Рендерит страницу для проверки рейсов по стойке и получает данные о рейсах."""
    lang = request.GET.get('lang', 'en')  # Получаем язык из параметров запроса, если он есть
    flights_data = get_flight_data_check(request, lang, pk)  # Получаем данные рейсов

    # Проверяем, если данные были получены
    if 'data' in flights_data:
        return render(request, 'app/map.html', {
            'flights': flights_data['data'],  # Передаем отфильтрованные рейсы в шаблон
            'lang': lang,
            'pk': pk
        })
    else:
        # Если данных нет, можем передать сообщение о рекламе или ошибке
        return render(request, 'app/map.html', {
            'advert': flights_data.get('advert', 'Нет данных для отображения'),
            'lang': lang,
            'pk': pk
        })

def gate(request, pk):
    """Рендерит страницу для проверки рейсов по стойке и получает данные о рейсах."""
    lang = request.GET.get('lang', 'en')  # Получаем язык из параметров запроса, если он есть
    flights_data = get_flight_data_gate(request, lang, pk)  # Получаем данные рейсов

    # Проверяем, если данные были получены
    if 'data' in flights_data:
        return render(request, 'app/gate.html', {
            'flights': flights_data['data'],  # Передаем отфильтрованные рейсы в шаблон
            'lang': lang,
            'pk': pk
        })
    else:
        # Если данных нет, можем передать сообщение о рекламе или ошибке
        return render(request, 'app/gate.html', {
            'advert': flights_data.get('advert', 'Нет данных для отображения'),
            'lang': lang,
            'pk': pk
        })



def baggage(request, pk):
    """Рендерит страницу для проверки рейсов по стойке и получает данные о рейсах."""
    lang = request.GET.get('lang', 'en')  # Получаем язык из параметров запроса, если он есть
    flights_data = get_flight_data_check(request, lang, pk)  # Получаем данные рейсов

    # Проверяем, если данные были получены
    if 'data' in flights_data:
        return render(request, 'app/baggage_ajax.html', {
            'flights': flights_data['data'],  # Передаем отфильтрованные рейсы в шаблон
            'lang': lang,
            'pk': pk
        })
    else:
        # Если данных нет, можем передать сообщение о рекламе или ошибке
        return render(request, 'app/baggage_ajax.html', {
            'advert': flights_data.get('advert', 'Нет данных для отображения'),
            'lang': lang,
            'pk': pk
        })


