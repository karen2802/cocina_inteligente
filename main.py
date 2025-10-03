import os
import requests
import random
from dotenv import load_dotenv
from google import genai

load_dotenv()

API_KEY= os.getenv("GEMINI_API_KEY")
my_client = genai.Client(api_key=API_KEY)

def temperature_threshold(temperature):
    limit_cold = 10
    limit_hot = 25

    if temperature < limit_cold:
        return "Cold"
    elif temperature > limit_hot:
        return "Hot"
    else:
        return "Normal"

def calculate_temperature(lat, long):
    response = requests.get(
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={long}&hourly=temperature_2m,apparent_temperature,rain&forecast_days=1")
    data = response.json()

    if 'hourly' not in data or 'temperature_2m' not in data['hourly']:
        print("Error: Could not retrieve temperature data.")
        return None

    temperature_list = data['hourly']['temperature_2m']
    average_temperature = sum(temperature_list) / len(temperature_list)
    print(f'Today the average temperature was: {round(average_temperature, 2)}')

    return average_temperature

def select_categories(temperature_sense):
    if temperature_sense == "Cold":
        return ['Beef', 'Pasta', 'Pork']
    elif temperature_sense == "Normal":
        return ['Chicken', 'Miscellaneous', 'Pasta', 'Vegan']
    elif temperature_sense == "Hot":
        return ['Dessert', 'Miscellaneous', 'Seafood']
    return []

def get_ids(categories):
    ids = []
    for category in categories:
        response = requests.get(f"https://www.themealdb.com/api/json/v1/1/filter.php?c={category}")
        meals = response.json()
        for meal in meals['meals']:
            ids.append(meal['idMeal'])
    return ids

def get_meals_by_id(meal_ids):
    meals = []
    for i in meal_ids:
        data = requests.get(f"https://www.themealdb.com/api/json/v1/1/lookup.php?i={i}")
        meal_data = data.json()

        if meal_data.get('meals'):
            meal = meal_data['meals'][0]
            print(meal)
            meals.append(meal)
    return meals

def prompt_gemini(prompt_user):
    response = my_client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt_user
    )
    print(response.text)

# --- Main Program Flow ---
latitude = 15.8375
longitude = -92.7577
my_temperature = calculate_temperature(latitude, longitude)

if my_temperature is not None:
    apparent_temperature = temperature_threshold(my_temperature)
    print(f"The temperature is considered: {apparent_temperature}")

    selected_categories = select_categories(apparent_temperature)
    print(f"Based on the temperature, we selected the following categories: {selected_categories}")

    id_meals = get_ids(selected_categories)
    print(f"Found {len(id_meals)} meal IDs.")

    get_random_meals_ids = random.choices(id_meals, k=2)

    random_meals = get_meals_by_id(get_random_meals_ids)

    prompt = f''' 
    Eres un agente que se encarga de determinar la cómida que voy a preparar a través de conocer
    1.- La ciudad en la que estoy  a través de las coordenadas: {latitude, longitude}
    2.- La temperatura promedio es: {my_temperature}
    3.- Una lista de dos recetas que te voy a hacer llegar:
    
    receta 1 {random_meals[0]}
    receta 2 {random_meals[1]}
    
    Solo toma en cuenta los ingredientes y la preparación que vienen en las recetas.
    Traduce los ingredientes y la preparación al español.
    No me arrojes infomación inútil, solo la información de la receta.
    La información que arrojes, hazlo ÚNICA Y EXCLUSIVAMENTE en formato JSON.
    Toma en cuenta mi ubicación y la disponibilidad de los ingredientes en la receta.
    '''

    print('---- IA pensando... ---')

    prompt_gemini(prompt)