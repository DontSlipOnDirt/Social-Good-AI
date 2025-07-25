from datetime import datetime
import re

def build_mongo_query(parsed_query: dict): # type: ignore
    """
    Convert parsed query dictionary to MongoDB query.
    """
    mongo_query = {}
    
    # Handle crime type with fuzzy matching
    if parsed_query.get("crime_category"):
        crime_category = parsed_query["crime_category"].lower()
        # Use regex for fuzzy matching
        mongo_query["crime_category"] = {"$regex": crime_category, "$options": "i"}
    
    # Handle location with fuzzy matching
    if parsed_query.get("location"):
        location = parsed_query["location"].lower()
        mongo_query["$or"] = [
            {"city": {"$regex": location, "$options": "i"}},
            {"location": {"$regex": location, "$options": "i"}},
            {"address": {"$regex": location, "$options": "i"}}
        ]
    
    # Handle date range
    date_filter = {}
    if parsed_query.get("date_start"):
        try:
            start_date = datetime.strptime(parsed_query["date_start"], "%Y-%m-%d")
            date_filter["$gte"] = start_date
        except ValueError:
            pass  # Invalid date format, skip
    
    if parsed_query.get("date_end"):
        try:
            end_date = datetime.strptime(parsed_query["date_end"], "%Y-%m-%d")
            date_filter["$lte"] = end_date
        except ValueError:
            pass  # Invalid date format, skip
    
    if date_filter:
        mongo_query["date"] = date_filter
    
    # Handle status
    if parsed_query.get("status"):
        mongo_query["status"] = {"$regex": parsed_query["status"], "$options": "i"}
    
    # Handle reported_by
    if parsed_query.get("reported_by"):
        mongo_query["reported_by"] = {"$regex": parsed_query["reported_by"], "$options": "i"}
    
    return mongo_query

def translate_synonyms(query_dict: dict): # type: ignore
    """
    Translate common crime type synonyms to standardized terms.
    """
    crime_synonyms = {
        # English
        "theft": "theft",
        "stealing": "theft",
        "burglary": "burglary",
        "robbery": "robbery",
        "assault": "assault",
        "murder": "murder",
        "fraud": "fraud",

        # Hindi
        "चोरी": "theft",
        "चोरी करना": "theft",
        "चोर": "theft",
        "डकैती": "robbery",
        "डकैत": "robbery",
        "हिंसा": "assault",
        "हत्या": "murder",
        "धोखा": "fraud",
        "ठगी": "fraud",
        "घर में चोरी": "burglary",

        # Bengali
        "চুরি": "theft",
        "চোর": "theft",
        "ডাকাতি": "robbery",
        "হামলা": "assault",
        "হত্যা": "murder",
        "প্রতারণা": "fraud",
        "ভাঙচুর": "vandalism",  # added vandalism as example
        "ঘর চুরি": "burglary",

        # Tamil
        "திருட்டு": "theft",
        "மோசடி": "fraud",
        "கொள்ளை": "robbery",
        "தாக்குதல்": "assault",
        "கொலை": "murder",
        "மனைவி திருட்டு": "burglary",

        # Telugu
        "దొంగతనం": "theft",
        "ఊరిపోక": "robbery",
        "మోసం": "fraud",
        "దాడి": "assault",
        "హత్య": "murder",
        "చోరీ": "burglary",

        # Marathi
        "चोरी": "theft",
        "चोर": "theft",
        "छापा मारणे": "robbery",
        "हल्ला": "assault",
        "खून": "murder",
        "फसवणूक": "fraud",
        "घरफोडी": "burglary",

        # Kannada
        "ಮೋಸ": "fraud",
        "ಕಳ್ಳತನ": "theft",
        "ದಾಳೆ": "robbery",
        "ಹಲ್ಲೆ": "assault",
        "ಕೊಲೆ": "murder",
        "ತೋಟದ ಕಳ್ಳತನ": "burglary",

        # Punjabi
        "ਚੋਰੀ": "theft",
        "ਡਾਕੇਬਾਜ਼ੀ": "robbery",
        "ਹਮਲਾ": "assault",
        "ਕਤਲ": "murder",
        "ਠੱਗੀ": "fraud",
        "ਘਰ ਦੀ ਚੋਰੀ": "burglary",
    }

    if query_dict.get("crime_category"):
        crime_category = query_dict["crime_category"].lower()
        for synonym, standard in crime_synonyms.items():
            if synonym in crime_category:
                query_dict["crime_category"] = standard
                break
    
    return query_dict