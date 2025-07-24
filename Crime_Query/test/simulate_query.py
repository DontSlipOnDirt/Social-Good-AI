import json
import re
from datetime import datetime

sample_data_str = '''
[
  {
    "id": 1,
    "date": "2023-01-18",
    "time": "18:45",
    "location": "Fraser Road, Patna, Bihar",
    "crime_category": "Vandalism (तोड़फोड़)",
    "crime_subcategory": "Public property damage",
    "description": "बस स्टॉप के शीशा तोड़ दिहल गइल",
    "reported_by": "नगर निगम कर्मी",
    "status": "Open"
  },
  {
    "id": 2,
    "date": "2023-02-02",
    "time": "15:45",
    "location": "Mylapore, Chennai, Tamil Nadu",
    "crime_category": "Fraud (मोसडी)",
    "crime_subcategory": "Fake job scam",
    "description": "வேலை வாய்ப்பு என்ற பெயரில் பணம் மோசடி செய்யப்பட்டது",
    "reported_by": "விக்ரம் சிங்",
    "status": "Case Filed"
  },
  {
    "id": 3,
    "date": "2023-02-10",
    "time": "04:15",
    "location": "Borivali, Mumbai, Maharashtra",
    "crime_category": "Burglary (सेंधमारी)",
    "crime_subcategory": "Residential burglary",
    "description": "Apartment broken into while residents were away",
    "reported_by": "Resident",
    "status": "Under Investigation"
  },
  {
    "id": 4,
    "date": "2023-02-15",
    "time": "23:15",
    "location": "Sherpur Chowk, Ludhiana, Punjab",
    "crime_category": "Burglary (ਸੇਧਮਾਰੀ)",
    "crime_subcategory": "Warehouse break-in",
    "description": "ਗੋਦਾਮ ਵਿੱਚੋਂ ਸਮਾਨ ਚੋਰੀ ਹੋ ਗਿਆ",
    "reported_by": "ਸੁਰੱਖਿਆ ਗਾਰਡ",
    "status": "Under Investigation"
  },
  {
    "id": 5,
    "date": "2023-02-28",
    "time": "21:15",
    "location": "Sitapura, Jaipur, Rajasthan",
    "crime_category": "Assault (हमला)",
    "crime_subcategory": "Street harassment",
    "description": "एक महिला ने सड़क पर परेशान किए जाने की शिकायत की",
    "reported_by": "अनाम",
    "status": "Case Filed"
  },
  {
    "id": 6,
    "date": "2023-03-03",
    "time": "14:45",
    "location": "Punaichak, Patna, Bihar",
    "crime_category": "Fraud (ठगी)",
    "crime_subcategory": "Insurance fraud",
    "description": "झूठ चोट के दावा पकड़ा गइल",
    "reported_by": "बीमा कंपनी",
    "status": "Under Investigation"
  },
  {
    "id": 7,
    "date": "2023-03-03",
    "time": "13:30",
    "location": "Ambabari, Jaipur, Rajasthan",
    "crime_category": "Fraud (धोखाधड़ी)",
    "crime_subcategory": "Insurance fraud",
    "description": "झूठे चोट के दावे का पता चला",
    "reported_by": "बीमा कंपनी",
    "status": "Under Investigation"
  },
  {
    "id": 8,
    "date": "2023-02-05",
    "time": "20:15",
    "location": "Ashiana Nagar, Patna, Bihar",
    "crime_category": "Vandalism (तोड़फोड़)",
    "crime_subcategory": "Graffiti",
    "description": "सार्वजनिक दीवार पर गंदा चित्र बना दिहल गइल",
    "reported_by": "स्थानीय निवासी",
    "status": "Open"
  },
  {
    "id": 9,
    "date": "2023-01-15",
    "time": "11:20",
    "location": "Exhibition Road, Patna, Bihar",
    "crime_category": "Fraud (ठगी)",
    "crime_subcategory": "Credit card cloning",
    "description": "एगो पर्यटक के क्रेडिट कार्ड से गैरकानूनी लेनदेन भइल",
    "reported_by": "अनन्या पटेल",
    "status": "Case Filed"
  },
  {
    "id": 10,
    "date": "2023-02-22",
    "time": "07:45",
    "location": "Thane, Mumbai, Maharashtra",
    "crime_category": "Theft (चोरी)",
    "crime_subcategory": "Two-wheeler theft",
    "description": "Motorcycle stolen from parking lot",
    "reported_by": "Sanjay Verma",
    "status": "Under Investigation"
  }
]
'''

sample_data = json.loads(sample_data_str)

mongo_query = {
    "$or": [
        {"city": {"$regex": "maharashtra", "$options": "i"}},
        {"location": {"$regex": "maharashtra", "$options": "i"}},
        {"address": {"$regex": "maharashtra", "$options": "i"}}
    ]
}

results = []
for record in sample_data:
    match = False
    if "$or" in mongo_query:
        for or_condition in mongo_query["$or"]:
            for field, regex_obj in or_condition.items():
                if field in record and "$regex" in regex_obj:
                    if re.search(regex_obj["$regex"], record[field], re.IGNORECASE):
                        match = True
                        break
            if match:
                break
    else:
        match = True # If no $or, assume all other conditions are direct matches

    if match:
        results.append(record)

print(json.dumps(results, indent=2))


