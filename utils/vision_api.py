from googletrans import Translator
translator = Translator()

def jp(text: str) -> str:
    return translator.translate(text, dest="ja").text

def identify_fish_vision(image_bytes: bytes) -> Optional[str]:
    try:
        client = vision.ImageAnnotatorClient()
        image = vision.Image(content=image_bytes)
        
        response = client.label_detection(image=image)
        labels = response.label_annotations
        
        web_response = client.web_detection(image=image)
        web_entities = web_response.web_detection.web_entities
        
        print(f"🏷️ All labels: {[l.description for l in labels]}")
        print(f"🌐 Web entities: {[e.description for e in web_entities if e.description]}")
        
        specific_fish = [
            'mackerel', 'tuna', 'salmon', 'sardine', 'bass', 
            'bream', 'flounder', 'cod', 'trout', 'snapper'
        ]
        
        for entity in web_entities:
            if entity.description:
                desc = entity.description.lower()
                for fish in specific_fish:
                    if fish in desc:
                        print(f"✅ Specific fish from web: {entity.description}")
                        return jp(entity.description)
        
        for label in labels:
            desc = label.description.lower()
            for fish in specific_fish:
                if fish in desc:
                    print(f"✅ Specific fish from label: {label.description}")
                    return jp(label.description)
        
        for label in labels:
            if 'fish' in label.description.lower():
                print(f"⚠️ Generic fish: {label.description}")
                return jp(label.description)
        
        return None
        
    except Exception as e:
        print(f"❌ Vision API error: {e}")
        return None
