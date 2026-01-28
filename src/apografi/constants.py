APOGRAFI_API_URL = "https://hrms.gov.gr/api"

# https://hr.apografi.gov.gr/api.html#genikes-plhrofories-le3ika

APOGRAFI_DICTIONARIES_URL = f"{APOGRAFI_API_URL}/public/metadata/dictionary/"

APOGRAFI_DICTIONARIES = {
  "UnitTypes": "Επιστρέφει όλες τους τύπους μονάδων που περιέχονται στο αντίστοιχο λεξικό του ΣΔΑΔ",
  "Specialities": "Επιστρέφει όλες τις ειδικότητες που περιέχονται στο αντίστοιχο λεξικό του ΣΔΑΔ",
  "SpecialPositions":"Επιστρέφει όλες τις ειδικές θέσεις που περιέχονται στο αντίστοιχο λεξικό του ΣΔΑΔ",
  "Ranks":"Επιστρέφει όλους τους βαθμούς που περιέχονται στο αντίστοιχο λεξικό του ΣΔΑΔ",
  "ProfessionCategories": "Επιστρέφει όλους τους κλάδους που περιέχονται στο αντίστοιχο λεξικό του ΣΔΑΔ",
  "OrganizationTypes": "Επιστρέφει όλες τους τύπους φορέων που περιέχονται στο αντίστοιχο λεξικό του ΣΔΑΔ",
  "OrganizationCategories": "Επιστρέφει όλες τις κατηγορίες φορέων που περιέχονται στο αντίστοιχο λεξικό του ΣΔΑΔ",
  "Functions": "Επιστρέφει όλες τις λειτουργίες που περιέχονται στο αντίστοιχο λεξικό του ΣΔΑΔ",
  "FunctionalAreas": "Επιστρέφει όλους τους τομείς πολιτικής που περιέχονται στο αντίστοιχο λεξικό του ΣΔΑΔ",
  "EmploymentTypes": "Επιστρέφει όλες τις εργασιακές σχέσεις που περιέχονται στο αντίστοιχο λεξικό του ΣΔΑΔ",
  "EmployeeCategories": "Επιστρέφει όλες τις κατηγορίες προσωπικού που περιέχονται στο αντίστοιχο λεξικό του ΣΔΑΔ",
  "EducationTypes": "Επιστρέφει όλες τις κατηγορίες εκπαίδευσης που περιέχονται στο αντίστοιχο λεξικό του ΣΔΑΔ",
  "DutyTypes": "Επιστρέφει όλα τα καθήκοντα θέσης απασχόλησης που περιέχονται στο αντίστοιχο λεξικό του ΣΔΑΔ",
  "Countries": "Επιστρέφει όλες τις χώρες που περιέχονται στο αντίστοιχο λεξικό του ΣΔΑΔ",
  "Cities": "Επιστρέφει όλους τους δήμους που περιέχονται στο αντίστοιχο λεξικό του ΣΔΑΔ"
}

# https://hr.apografi.gov.gr/api.html#genikes-plhrofories-foreis

APOGRAFI_ORGANIZATIONS_URL = f"{APOGRAFI_API_URL}/public/organizations"

# https://hr.apografi.gov.gr/api.html#genikes-plhrofories-monades-lista-monadwn

APOGRAFI_ORGANIZATIONAL_UNITS_URL = (
    f"{APOGRAFI_API_URL}/public/organizational-units?organizationCode="
)

# https://hr.apografi.gov.gr/api.html#genikes-plhrofories-monades-ierarxia-monadwn

APOGRAFI_ORGANIZATION_TREE_URL = (
    f"{APOGRAFI_API_URL}/public/organization-tree?organizationCode="
)
