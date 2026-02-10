from src.models.apografi.dictionary import Dictionary
from src.models.utils import SyncLog as Log 
from src.apografi.constants import APOGRAFI_DICTIONARIES, APOGRAFI_DICTIONARIES_URL
from src.apografi.utils import apografi_get
from deepdiff import DeepDiff
from alive_progress import alive_bar
import redis
import json

def sync_apografi_dictionaries():
  print("Συγχρονισμός λεξικών από το ΣΔΑΔ...")

  with alive_bar(len(APOGRAFI_DICTIONARIES)) as bar:
    for dictionary in APOGRAFI_DICTIONARIES.keys():
      print(f"  - Συγχρονισμός λεξικού: {dictionary}...")
      response = apografi_get(f"{APOGRAFI_DICTIONARIES_URL}{dictionary}")
      for item in response.json()["data"]:
        doc = {
          "code": dictionary,
          "code_el": APOGRAFI_DICTIONARIES[dictionary],
          "apografi_id": item["id"],
          "description": item["description"],
        }
        if "parentId" in item:
          doc["parentId"] = item["parentId"]
        doc_id = f"{dictionary}:{item['id']}:{item['description']}"

        existing = Dictionary.objects(
          code=dictionary,
          apografi_id=item["id"],
          description=item["description"],
        ).first()

        if existing:
          existing_dict = existing.to_mongo().to_dict()
          existing_dict.pop("_id")
          existing_dict.pop("createdAt")
          existing_dict.pop("updatedAt")

          diff = DeepDiff(existing_dict, doc, view='tree').to_json() 
          diff = json.loads(diff)
          if diff:
            for key, value in doc.items():
              setattr(existing, key, value)
            existing.save()
            Log(
              entity="dictionary",
              action="update",
              doc_id=doc_id,
              value=diff,
            ).save()
        else:
          Dictionary(**doc).save()
          Log(
            entity="dictionary", action="insert", doc_id=doc_id, value=doc
          ).save()
      bar()

  print("Τέλος συγχρονισμού λεξικών από το ΣΔΑΔ.")


def cache_dictionaries():
  r = redis.Redis(db=0)
  r.flushdb()
  print("Καταχώρηση συνόλων στην cache...")
  for dictionary in APOGRAFI_DICTIONARIES.keys():
    # r.delete(dictionary)
    docs = Dictionary.objects(code=dictionary)
    ids = set([doc["apografi_id"] for doc in docs])
    r.sadd(dictionary, *ids)
  print("Τέλος καταχώρησης συνόλων στην cache.")

  r = redis.Redis(db=1)
  r.flushdb()
  print("Καταχώρηση λεξικών στην cache...")
  for entry in Dictionary.objects():
    if entry["code"] in [
      "Functions",
      "Cities",
      "Countries",
      "OrganizationTypes",
      "UnitTypes",
    ]:
      r.set(f"{entry['code']}:{entry['apografi_id']}", entry["description"])
  print("Τέλος καταχώρησης λεξικών στην cache.")
