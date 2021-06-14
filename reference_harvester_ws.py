from flask import Flask, jsonify, request
from utils import europe_pmc_api, mongo_access, config, nlp
from itertools import chain
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


@app.route("/harvest/<int:pmid>", methods=['GET', 'OPTIONS'])
def submit(pmid):
    use_alleles = request.args.get('useAlleles')
    alleles = None

    if use_alleles:
        with open(config.get('DEFAULT', 'TARGET_ALLELE_FILE')) as f:
            alleles = f.read().splitlines()

    if mongo_access.exist(pmid):
        reference = mongo_access.get_by_pmid(pmid)
        scrub(reference)
        return jsonify(reference)

    reference = europe_pmc_api.get_paper_by_pmid(pmid)

    if reference is None:
        return jsonify({'error': 'Error while trying to get data from EuropePMC'})

    reference = dict(
        chain({'status': 'pending', 'alleles': [],
               'datasource': 'manual', 'consortiumPaper': False,
               'citations': [], 'cites': [], 'citedBy': [],
               'alleleCandidates': [], 'comment': ''}.items(), reference.items()))
    reference['firstPublicationDate'] = str(reference['firstPublicationDate'].isoformat())
    reference = nlp.get_fragments(reference, alleles)
    return reference


def scrub(obj, bad_key="_id"):
    if isinstance(obj, dict):
        for key in list(obj.keys()):
            if key == bad_key:
                del obj[key]
            else:
                scrub(obj[key], bad_key)
    elif isinstance(obj, list):
        for i in reversed(range(len(obj))):
            if obj[i] == bad_key:
                del obj[i]
            else:
                scrub(obj[i], bad_key)

    else:
        pass


if __name__ == '__main__':
    app.run(debug=True, port=8000, host='0.0.0.0')