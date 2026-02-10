import json

from flask import Blueprint, Response, request

from src.blueprints.utils import convert_greek_accented_chars
from src.models.apografi.dictionary import Dictionary
from src.models.apografi.organization import Organization
from src.models.apografi.organizational_unit import OrganizationalUnit

from bson import json_util

apografi = Blueprint("apografi", __name__)

# Dictionary Routes


@apografi.route("/dictionary/<string:dictionary>/<int:id>/description")
def get_dictionary_id(dictionary: str, id: int):
    try:
        doc = Dictionary.objects().get(code=dictionary, apografi_id=id)
        description = {"description": doc["description"]}
        return Response(json.dumps(description), mimetype="application/json", status=200)
    except Exception as e:
        error = {"error": str(e)}
        return Response(json.dumps(error), mimetype="application/json", status=404)


@apografi.route( "/dictionary/<string:dictionary>/<string:description>/id" )  # fmt: skip
def get_dictionary_code(dictionary: str, description: str):
    try:
        doc = Dictionary.objects().get(code=dictionary, description=description)
        print(doc)
        id = {"id": doc["apografi_id"]}
        return Response(json.dumps(id), mimetype="application/json", status=200)
    except Exception as e:
        error = {"error": str(e)}
        return Response(json.dumps(error), mimetype="application/json", status=404)


@apografi.route("/dictionary/<string:dictionary>")
def get_dictionary(dictionary: str):
    dictionary = Dictionary.objects(code=dictionary).only("apografi_id", "description").exclude("id")
    return Response(dictionary.to_json(), mimetype="application/json", status=200)


@apografi.route("/dictionary/<string:dictionary>/ids")
def get_dictionary_ids(dictionary: str):
    docs = Dictionary.objects(code=dictionary)
    ids = [doc["apografi_id"] for doc in docs]
    return Response(json.dumps(ids), mimetype="application/json", status=200)


# Organization Routes


@apografi.route("/organization")
def get_organization():
    organization = Organization.objects().only("code", "preferredLabel").exclude("id")
    return Response(organization.to_json(), mimetype="application/json", status=200)


@apografi.route("/organization/all")
def get_all_organizations():
    data = (
        Organization.objects.get(status="active").only("code", "organizationType", "preferredLabel", "subOrganizationOf", "status")
        .exclude("id")
        .order_by("preferredLabel")
    )
    return Response(
        data.to_json(),
        mimetype="application/json",
        status=200,
    )


@apografi.route("/organization/<string:code>")
def get_organization_enhanced(code: str):
    try:
        doc = Organization.objects().get(code=code)
        return Response(doc.to_json_enhanced(), mimetype="application/json", status=200)
    except Exception as e:
        error = {"error": str(e)}
        return Response(json.dumps(error), mimetype="application/json", status=404)


@apografi.route("/organization/<string:label>/label")
def get_organization_label(label: str):
    try:
        doc = Organization.objects(preferredLabel__icontains=convert_greek_accented_chars(label))
        return Response(doc.to_json(), mimetype="application/json", status=200)
    except Exception as e:
        error = {"error": str(e)}
        return Response(json.dumps(error), mimetype="application/json", status=404)


# Organizational Units Routes


@apografi.route("/organizationalUnit")
def get_organization_unit():
    organization = OrganizationalUnit.objects().only("code", "preferredLabel").exclude("id")
    return Response(organization.to_json(), mimetype="application/json", status=200)


@apografi.route("/organizationalUnit/all")
def get_all_organizational_units():
    data = (
        OrganizationalUnit.objects.only("code", "preferredLabel", "unitType", "organizationCode", "supervisorUnitCode", "remitsFinalized")
        .exclude("id")
        .order_by("preferredLabel")
    )

    return Response(
        data.to_json(),
        mimetype="application/json",
        status=200,
    )

@apografi.route("/organizationalUnit/all/pagination")
def get_all_organizational_units_with_pagination():

    try:
        # Pagination
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("pageSize", 100))

        # Filtering
        filters = json.loads(request.args.get("filter", "{}"))
        print("FIlters>>",filters)
        query = {}
        
        for field, condition in filters.items():
            value = condition.get("filter")
            if value:
                # Use icontains for text fields
                query[f"{field}__icontains"] = value

        # Sorting
        sort_model = json.loads(request.args.get("sortModel", "[]"))
        order_by_list = []
        for sort in sort_model:
            col = sort.get("colId")
            order = sort.get("sort")
            if col and order:
                order_by_list.append(f"{'' if order == 'asc' else '-'}{col}")

        total = OrganizationalUnit.objects(**query).count()

        print("Query>>",**query)
        print("order_by_list>>",order_by_list)
        print("Pages>>",page, page_size)

        org_units  = (
          OrganizationalUnit.objects(**query)
            .order_by(*order_by_list)
            .skip((page - 1) * page_size)
            .limit(page_size)
            .order_by("preferredLabel")
        )

        data = [u.to_mongo().to_dict() for u in org_units]

        return json.loads(json_util.dumps({"rows": data, "total": total})), 200
    except Exception as e:
        print("Error:", e)
        return Response(
            json.dumps({"error": f"Δεν βρέθηκαν στοιχεία για τις μονάδες {e}"}),
            mimetype="application/json",
            status=404,
        )


@apografi.route("/organizationalUnit/count")
def get_organizational_unit_count():
    data = OrganizationalUnit.objects().count()
    return Response(
        json.dumps({"count": data}),
        mimetype="application/json",
        status=200,
    )


@apografi.route("/organizationalUnit/<string:code>")
def get_organizational_unit(code: str):
    try:
        monada = OrganizationalUnit.objects.get(code=code)
        # print("1<<<<<<", monada.to_json())
        # print("2<<<<<<", str(monada.to_json_enhanced()))
        return Response(
            monada.to_json_enhanced(),
            mimetype="application/json",
            status=200,
        )
    except OrganizationalUnit.DoesNotExist:
        return Response(
            json.dumps({"error": f"Δεν βρέθηκε μονάδα με κωδικό {code}"}),
            mimetype="application/json",
            status=404,
        )


@apografi.route("/organizationalUnit/<string:code>/organizationCode")
def get_organizational_unit_organization_code(code: str):
    try:
        monada = OrganizationalUnit.objects.get(code=code)
        return Response(
            json.dumps({"organizationCode": monada.organizationCode}),
            mimetype="application/json",
            status=200,
        )
    except OrganizationalUnit.DoesNotExist:
        return Response(
            json.dumps({"error": f"Δεν βρέθηκε μονάδα με κωδικό {code}"}),
            mimetype="application/json",
            status=404,
        )
