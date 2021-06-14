import datetime
import json
import string

import requests
from utils import mongo_access, config
from json.decoder import JSONDecodeError
import googlemaps
from dateutil import parser


def get_geocode_mapaffil(pmid):
    url = f"http://abel.lis.illinois.edu/cgi-bin/mapaffil/search.py?PMIDs={pmid}&format=json"
    response = requests.get(url)
    affiliations = []
    unique = set()
    try:
        for affiliation in response.json():
            affiliation_name = remove_prefix(affiliation["affiliation"])
            if affiliation["affiliation"] not in unique:
                unique.add(affiliation_name)
                affiliations.append(
                    _create_affiliation(
                        name=affiliation_name,
                        city=affiliation["city"],
                        country=affiliation["country"],
                        lat=affiliation["lat"],
                        long=affiliation["lon"],
                    )
                )
        return affiliations
    except JSONDecodeError:
        return None


def remove_prefix(name):
    return (
        name.replace("FROMPMC: ", "").replace("FROMNIH: ", "").replace("FROMPAT: ", "")
    )


def get_id(name):
    return (
        remove_prefix(name)
        .translate(str.maketrans("", "", string.punctuation))
        .lower()
        .replace(" ", "_")
    )


def get_gecode_wikimedia(affiliation_name):
    search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={affiliation_name}&utf8=&format=json"
    geocode_url = ""
    response = requests.get(search_url)
    try:
        best_match = response.json()["query"]["search"][0]
        page_id = best_match["pageid"]
        geocode_url = f"https://en.wikipedia.org/w/api.php?action=query&prop=coordinates&pageids={page_id}&utf8=&format=json"
        geo_response = requests.get(geocode_url)
        geo_data = geo_response.json()["query"]["pages"][str(page_id)]
        lat = geo_data["coordinates"][0]["lat"]
        long = geo_data["coordinates"][0]["lon"]

        access_token = config.get("DEFAULT", "GMAPS_API_KEY")
        gmaps = googlemaps.Client(key=access_token)
        gmaps_result = gmaps.reverse_geocode((lat, long))
        address_components = gmaps_result[0]["address_components"]
        city = next(
            city
            for city in address_components
            if "locality" in city["types"] or "sublocality" in city["types"]
        )["long_name"]
        country = next(
            country for country in address_components if "country" in country["types"]
        )["long_name"]

        return _create_affiliation(
            name=affiliation_name,
            alt_name=geo_data["title"],
            lat=lat,
            long=long,
            city=city,
            country=country,
        )
    except Exception:
        print("Failed getting wikimedia data for: ")
        print(search_url)
        print(geocode_url)
        print(affiliation_name)
        return None


def get_geocode_gmaps(affiliation_name):
    access_token = config.get("DEFAULT", "GMAPS_API_KEY")
    gmaps = googlemaps.Client(key=access_token)

    gmaps_results = gmaps.geocode(affiliation_name)
    if len(gmaps_results) > 0:
        gmaps_result = gmaps_results[0]
        address_components = gmaps_result["address_components"]
        cities = [
            city
            for city in address_components
            if "locality" in city["types"] or "sublocality" in city["types"]
        ]
        city = cities[0]["long_name"] if len(cities) > 0 else None
        countries = [
            country for country in address_components if "country" in country["types"]
        ]

        country = countries[0]["long_name"] if len(countries) > 0 else None
        location = gmaps_result["geometry"]["location"]
        return _create_affiliation(
            name=affiliation_name,
            lat=location["lat"],
            long=location["lng"],
            city=city,
            country=country,
        )
    else:
        return None


def _create_affiliation(name, lat, long, alt_name=None, city=None, country=None):
    return dict(
        name=name, alt_name=alt_name, city=city, country=country, lat=lat, long=long
    )


if __name__ == "__main__":
    all_references = mongo_access.get_all()
    all_affiliations = []
    for reference in all_references:
        pmid = reference["pmid"]
        if not mongo_access.affiliation_exists(pmid):
            affiliations_by_pmid = dict(pmid=pmid)
            publication_date: datetime.datetime = reference[
                "firstPublicationDate"
            ].replace(tzinfo=None)
            last_mapaffil_date = parser.parse("2018-10-01T00:00:00.0000Z").replace(
                tzinfo=None
            )
            affiliations = []
            if publication_date < last_mapaffil_date:
                affiliations = get_geocode_mapaffil(pmid)
            else:
                affiliation_names = [
                    author["affiliation"]
                    for author in reference["authorList"]
                    if "affiliation" in author
                ]
                unique_affiliations = set()
                for affiliation_name in affiliation_names:
                    if affiliation_name not in unique_affiliations:
                        unique_affiliations.add(affiliation_name)
                        affiliation = get_geocode_gmaps(affiliation_name)
                        if affiliation is None:
                            affiliation = get_gecode_wikimedia(affiliation_name)
                        if affiliation is not None:
                            affiliations.append(affiliation)
            affiliations_by_pmid["affiliations"] = (
                affiliations if affiliations is not None else []
            )
            all_affiliations.append(affiliations_by_pmid)
        if len(all_affiliations) > 50:
            mongo_access.insert_all(
                all_affiliations,
                "affiliations",
                "org.impc.publications.models.Affiliation",
            )
            all_affiliations = []
    print(
        mongo_access.insert_all(
            all_affiliations, "affiliations", "org.impc.publications.models.Affiliation"
        )
    )

    # print(
    #     get_gecode_wikimedia(
    #         "Shanghai Institute for Advanced Immunochemical Studies, ShanghaiTech University, Shanghai, China"
    #     )
    # )
    # print(
    #     get_geocode_gmaps(
    #         "Shanghai Institute for Advanced Immunochemical Studies, ShanghaiTech University, Shanghai, China"
    #     )
    # )
