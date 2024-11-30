from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import base64
import json
from openai import OpenAI
import re
from supporting import import_google_image



app = Flask(__name__)


with open('./recipes.json', 'r', encoding='utf-8-sig') as file:
    data = json.load(file)
    new_id = int(max([recipe['id'] for recipe in data['recipes']])) + 1


def modify_recipe(id, attribute, value):
    print(f"Modifying recipe {id}...")
    if attribute not in ['title', 'description', 'ingredients', 'instructions', 'image', 'recommended', 'favorite', 'generated']:
        return -1
    print('here')
    for recipe in data['recipes']:
        if str(recipe['id']).strip() == id.strip():
            print(f"Updating recipe {id}...")
            data['recipes'][data['recipes'].index(recipe)][attribute] = value
            print(f"Recipe {id} updated.")
            break

    with open('./recipes.json', 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

def get_recommended():
    return [recipe for recipe in data['recipes'] if recipe['recommended']]

def get_favorites():
    return [recipe for recipe in data['recipes'] if recipe['favorite']]

def get_saved_recipes():
    return data['recipes']

def add_recipes_to_recipes_json(list_recipes):
    # get file with highest number in recipes.json
    '''with open('./recipes.json', 'r') as file:
        data = json.load(file)
        new_id = int(max([recipe['id'] for recipe in data['recipes']])) + 1'''

    provisional_result = []
    global new_id
    global data

    for recipe in list_recipes:
        # add the recipe to the json file
        recipe_json = {
            "title": recipe['title'],
            "ingredients": recipe['ingredients'],
            "instructions": recipe['instructions'],
            "id": new_id,
            "favorite": False,
            "recommended": False,
            "generated": True,
            "image": import_google_image(recipe['title'], new_id)
        }
        data['recipes'].append(recipe_json)
        provisional_result.append(recipe_json)
        new_id += 1

    with open('./recipes.json', 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
    
    return provisional_result


@app.route('/', methods=['GET'])
def index():
    print(request.method)

    return render_template('index.html', favorites=get_favorites(), recommended_recipes=get_recommended())


@app.route('/upload_image', methods=['POST'])
def upload_image():

    data = request.get_json()
    if not data or 'base64string' not in data:
        return jsonify({"error": "Invalid input"}), 400

    # Decode the Base64 string (if needed for further processing)
    base64_string = data['base64string']

    openai = OpenAI(api_key= os.environ.get("OPEN_AI_KEY"))
    response = openai.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "user", "content": [
            {"type": "image_url",
            "image_url": {
                "url": f"{base64_string}"
            }}
        ]}, {"role": "system", "content": 'You will be passed an image containing various ingredients. (it is possible that the image will depict the interior of a fridge). Your job is to identify all the different ingredients in the picture. The response MUST be in JSON, in such a way that the response could be immediately parsed as json without rasing any errors. The form of the JSON structure should be like the following: {"ingredientsRecognized": ["celery", "tomato", "cheese", "cream", "lettuce", "milk", "garlic", "onion", "bread"]}. The response should contain the JSON and nothing else.'}
    ])
    
    ingredients = response.choices[0].message.content

    json_match = re.search(r'{.*}', ingredients, re.DOTALL)

    if json_match:
        json_string = json_match.group(0) 

    print(ingredients)

    return jsonify({"ingredients": json_string}), 200


@app.route('/toggle_favorite', methods=['POST'])
def toggle_favorite():
    data = request.json
    recipe_id = data['recipe_id']
    is_favorite = data['is_favorite']
    print(f'is_favorite: {is_favorite}')
    print('recipe_id: ', recipe_id)

    if is_favorite:
        # Add to favorites
        recipe = next((r for r in get_saved_recipes() if str(r['id']).strip() == str(recipe_id).strip()), None)
        modify_recipe(recipe_id, 'favorite', True)
        print("recipe")
        print(recipe)

    else:
        # Remove from favorites
        modify_recipe(recipe_id, 'favorite', False)
    
    return jsonify({"success": True, "recipe": recipe if is_favorite else None})

@app.route('/get_recipe')
def get_recipe():
    recipe_id = request.args.get('recipe_id')
    
    recipe = next((r for r in get_saved_recipes() if str(r['id']).strip() == str(recipe_id).strip()), None)

    if not recipe:
        print({"error": "Recipe not found."})
    return jsonify(recipe)

@app.route('/get_favorites_json')
def get_favorites_json():
    return jsonify(get_favorites())

@app.route('/find_recipes', methods=['POST'])
def fetch_recipes():
    ingredients_list = request.get_json()["ingredients"]

    if not ingredients_list:
        return jsonify({"error": "Invalid input"}), 400

    openai = OpenAI(api_key=os.environ.get("OPEN_AI_KEY"))
    response = openai.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "user", "content": f"{ingredients_list}"}, 
        {"role": "system", "content": 'You will be passed a list of ingredients, you will need to suggest 1-3 recipes that you could make from the given ingredients. Minor ingredients like condiments can be assumed. The response MUST be in JSON, in such a way that the response could be immediately parsed as json without rasing any errors. The form of the JSON structure should be like the following: { "recipes": [{"title": "Title of the recipe", "ingredients": ["tomato", "cheese", "bread"], "instructions": "Make the..."}, {"title": "Title of the recipe2", "ingredients": ["lettuce", "cream"], "instructions": "Mix the..."}]}. The instructions for each recipe must be clear and about 1-3 paragraphs in length. The response should be the JSON and NOTHING else.'}
    ])
    
    recipes = response.choices[0].message.content

    json_match = re.search(r'{.*}', recipes, re.DOTALL)

    if json_match:
        json_recipes = json_match.group(0) 

    output_recipes = json.loads(json_recipes)
    list_recipes = output_recipes['recipes']

    list_recipes = add_recipes_to_recipes_json(list_recipes)
    
    print('list_recipes: ')
    print(list_recipes)

    return jsonify({"recipes": list_recipes}), 200




if __name__ == '__main__':

    app.run(debug=True)
