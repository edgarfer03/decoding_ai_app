import json
import requests
import os


def import_google_image(query, id):

    # Your Custom Search API key and CX (Custom Search Engine ID)
    API_KEY = os.environ.get("GOOGLE_SEARCH_API")
    CX = '65ceb5607416f4c51'

    # Request URL
    url = f"https://www.googleapis.com/customsearch/v1?q={query.replace(' ', '+')}&cx={CX}&searchType=image&key={API_KEY}"

    # Send GET request
    response = requests.get(url)
    data = response.json()

    # Download and save the first image
    if 'items' in data:
        for item in data['items']:
            image_url = item['link']
            print(f"Image found: {image_url}")
            img_response = requests.get(image_url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Safari/537.36'
            }, allow_redirects=True)
            print(f"Content-Type: {img_response.headers['Content-Type']}")
            if 'image' not in img_response.headers['Content-Type']:
                print("Not an image. Skipping...")
                continue
            file_type = image_url.split('.')[-1]
            if file_type != 'jpg' and file_type != 'jpeg' and file_type != 'png':
                print("Not a supported image type. Skipping...")
                continue
            # Save the image
            with open(f"./static/images/{id}.{file_type}", 'wb') as f:
                f.write(img_response.content)
            print("Image saved successfully!")
            break
    else:
        print("No image found.")

    return f"./static/images/{id}.{file_type}"


'''with open('./recipes.json', 'r', encoding='utf-8-sig') as file:
    data = json.load(file)


for recipe in data['recipes']:
    print(recipe['title'])
    file_type = import_google_image(recipe['title'], recipe['id'])
    data['recipes'][data['recipes'].index(recipe)]['image'] = f'./static/images/{recipe["id"]}.{file_type}'


with open('./recipes.json', 'w', encoding='utf-8') as file:
    json.dump(data, file, ensure_ascii=False, indent=4)'''




