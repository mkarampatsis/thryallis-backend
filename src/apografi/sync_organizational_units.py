from src.models.apografi.organization import Organization
from src.models.apografi.organizational_unit import OrganizationalUnit
from src.models.apografi.embedded import Address, Spatial
from src.models.utils import SyncLog as Log
from src.apografi.utils import apografi_get
from src.apografi.constants import APOGRAFI_ORGANIZATIONAL_UNITS_URL
from deepdiff import DeepDiff
import json

units_with_problems = [
  { "code":"763976", "field":"email", 'problem':'email is tm.sint.td.akiklades@efka.gov.gr  / tm.par.td.akiklades@efka.gov.gr' }
]

def sync_one_organization_units(units):
  for unit in units:
    doc = {k: v for k, v in unit.items() if v}
    doc_id = doc["code"]
    print("Μονάδα:", doc_id)

    # Units with problem
    if doc_id == "763976":
      doc['email'] = unit['email'].split('/')[0].strip()

    for key, value in doc.items():
      if key in ["purpose", "alternativeLabels"]:
        value = sorted(value or [])
        doc[key] = value
      if key == "spatial":
        value = sorted(
          value or [],
          key=lambda x: (x.get("countryId", 0), x.get("dimosId", 0) or x.get("cityId", 0) ),
        )
        value = [Spatial(**item) for item in value]
        doc[key] = value
      if key in ["mainAddress", "secondaryAddresses"]:
        if isinstance(value, list):
          value = sorted(
            value or [],
            key=lambda x: (
              x.get("fullAddress", ""),
              x.get("postCode", ""),
              x.get("adminUnitLevel1", 0),
              x.get("adminUnitLevel2", 0),
            ),
          )
          value = [Address(**item) for item in value]
        else:
          value = Address(**value)
        doc[key] = value

    existing = OrganizationalUnit.objects(code=doc["code"]).first()
    if existing:
      existing_dict = existing.to_mongo().to_dict()
      existing_dict.pop("_id")
      new_doc = OrganizationalUnit(**doc).to_mongo().to_dict()
      # diff = DeepDiff(existing_dict, new_doc)
      diff = DeepDiff(existing_dict, new_doc, view='tree').to_json() 
      # print("DIFF:", diff)
      diff = json.loads(diff)
      if diff:
        for key, value in doc.items():
          setattr(existing, key, value)
        # print(existing.to_mongo().to_dict())
        existing.save()
        Log(
          entity="organizational-unit",
          action="update",
          doc_id=doc_id,
          value=diff,
        ).save()
    else:
      OrganizationalUnit(**doc).save()
      Log(entity="organizational-unit", action="insert", doc_id=doc_id, value=doc).save()


def sync_organizational_units():
  print("Συγχρονισμός οργανωτικών μονάδων από το ΣΔΑΔ...")
  for organization in Organization.objects():
    print("Φορέας:", organization['code'])
    response = apografi_get(f"{APOGRAFI_ORGANIZATIONAL_UNITS_URL}{organization['code']}")

    if response.status_code != 404:
      units = response.json()["data"]
      sync_one_organization_units(units)

  print("Τέλος συγχρονισμού οργανωτικών μονάδων από το ΣΔΑΔ.")
