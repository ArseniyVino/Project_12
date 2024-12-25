import os
import requests
from flask import Flask, request, render_template, jsonify

app = Flask(__name__)

API_KEY = "oFOFGFLqlAh2X6feSEsRYP0R1247oCLA" 
BASE_URL = "http://dataservice.accuweather.com"


def get_weather(location_key):
    """
    Получает текущие погодные условия для заданного ключа локации.

    :param location_key: Уникальный ключ местоположения (LocationKey)
    :return: Словарь с данными о погоде
    """
    endpoint = f"{BASE_URL}/currentconditions/v1/{location_key}"
    params = {
        "apikey": API_KEY,
        "details": "true"
    }
    response = requests.get(endpoint, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        return {"error": response.json()}


def get_location_key(city_name):
    """
    Получает ключ местоположения для заданного города.

    :param city_name: Название города
    :return: LocationKey или сообщение об ошибке
    """
    endpoint = f"{BASE_URL}/locations/v1/cities/search"
    params = {
        "apikey": API_KEY,
        "q": city_name
    }
    response = requests.get(endpoint, params=params)

    if response.status_code == 200 and response.json():
        return response.json()[0]["Key"]
    else:
        return {"error": response.json()}

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        city1 = request.form.get("city1")
        city2 = request.form.get("city2")

        if not city1 or not city2:
            return render_template("index.html", error="Оба поля должны быть заполнены")

        location_key1 = get_location_key(city1)
        location_key2 = get_location_key(city2)

        if "error" in location_key1 or "error" in location_key2:
            return render_template("index.html", error="Не удалось найти один или оба города")

        weather_data1 = get_weather(location_key1)
        weather_data2 = get_weather(location_key2)

        if "error" in weather_data1 or "error" in weather_data2:
            return render_template("index.html", error="Ошибка при получении данных о погоде")

        def analyze_weather(data):
            wind_speed = data["Wind"]["Speed"]["Metric"]["Value"]
            temperature = data["Temperature"]["Metric"]["Value"]
            precipitation_type = data.get("PrecipitationType", None)
            not_good = wind_speed > 10 or (precipitation_type and precipitation_type != "Snow")
            bad_weather = not_good or temperature < -5 or temperature > 30
            stay_home = wind_speed > 25 or temperature > 40 or temperature < -20
            return {
                "wind_speed": wind_speed,
                "temperature": temperature,
                "precipitation_type": precipitation_type,
                "not_good": not_good,
                "bad_weather": bad_weather,
                "stay_home": stay_home
            }

        analysis1 = analyze_weather(weather_data1[0])
        analysis2 = analyze_weather(weather_data2[0])

        return render_template(
            "index.html",
            city1=city1, city2=city2,
            weather1=weather_data1[0], analysis1=analysis1,
            weather2=weather_data2[0], analysis2=analysis2
        )

    return render_template("index.html")


if __name__ == "__main__":
    os.makedirs("templates", exist_ok=True)
    with open("templates/index.html", "w", encoding="utf-8") as f:
        f.write("""<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>Weather Route</title>
</head>
<body>
    <h1>Проверка погоды</h1>
    <form method=\"POST\">
        <label for=\"city1\">Город старта:</label>
        <input type=\"text\" id=\"city1\" name=\"city1\" required>
        <br>
        <label for=\"city2\">Город прибытия:</label>
        <input type=\"text\" id=\"city2\" name=\"city2\" required>
        <br><br>
        <button type=\"submit\">Узнать погоду</button>
    </form>

    {% if error %}
        <p style=\"color: red;\">{{ error }}</p>
    {% endif %}

    {% if weather1 and weather2 %}
        <h2>Погода в {{ city1 }}:</h2>
        <p>Температура: {{ weather1.Temperature.Metric.Value }}°C</p>
        <p>Скорость ветра: {{ analysis1.wind_speed }} м/с</p>
        <p>Осадки: {{ analysis1.precipitation_type if analysis1.precipitation_type else "Нет" }}</p>
        {% if analysis1.stay_home %}
            <p style=\"color: red; font-weight: bold;\">Рекомендуем не выходить из дома</p>
        {% elif analysis1.bad_weather %}
            <p style=\"color: red;\">Погода плохая</p>
        {% elif analysis1.not_good %}
            <p style=\"color: red;\">Погода не очень</p>
        {% endif %}

        <h2>Погода в {{ city2 }}:</h2>
        <p>Температура: {{ weather2.Temperature.Metric.Value }}°C</p>
        <p>Скорость ветра: {{ analysis2.wind_speed }} м/с</p>
        <p>Осадки: {{ analysis2.precipitation_type if analysis2.precipitation_type else "Нет" }}</p>
        {% if analysis2.stay_home %}
            <p style=\"color: red; font-weight: bold;\">Рекомендуем не выходить из дома</p>
        {% elif analysis2.bad_weather %}
            <p style=\"color: red;\">Погода плохая</p>
        {% elif analysis2.not_good %}
            <p style=\"color: red;\">Погода не очень</p>
        {% endif %}
    {% endif %}
</body>
</html>""")

    # Запуск приложения
    app.run(debug=False)
