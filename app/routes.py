import logging

import flask
import requests
import re
from flask import Response
from flask import request
from flask import jsonify

app = flask.Flask(__name__)
logger = flask.logging.create_logger(app)
logger.setLevel(logging.INFO)

# attempt to normalize the language name
# this will catch cases like:
# Objective C
# Objective-C
# ObjectiveC
# JavaScript
# Javascript
def normalizeLang( lang ):
    lang = lang.lower()
    regex = re.compile("[^a-z]")
    lang = regex.sub("", lang)
   
    return lang


@app.route("/health-check", methods=["GET"])
def health_check():
    """
    Endpoint to health check API
    """
    app.logger.info("Health Check!")
    return Response("All Good!", status=200)

# endpoint that takes json data from github and bitbucket and merges them
@app.route("/merge", methods=["GET"])
def merge():
    """
    Endpoint to merge API
    """
    app.logger.info("merge!")

    originals = 0
    forks = 0
    watchers = 0
    topics = 0
    setLangs = set()
    error = False

    organization = request.args.get("organization")
    team = request.args.get("team")

    if (organization != None and team != None):
        github = "https://api.github.com/orgs/" + organization + "/repos"
        bitbucket = "https://api.bitbucket.org/2.0/repositories/" + team
        #githeaders = {"Accept": "application/vnd.github.v3+json"}
        githeaders = {"Accept": "application/vnd.github.mercy-preview+json"}
            
        responseGithub = requests.get(github, headers=githeaders)
        responseBitbucket = requests.get(bitbucket)
        jsonGitHub = responseGithub.json()
        jsonBitbucket = responseBitbucket.json()

        # all repos are public since we are not authenticated
        
        if (responseGithub.status_code == 200):
            for val in jsonGitHub:
                if val["fork"] == True:
                    forks += 1
                else:
                    originals += 1

                watchers += val["watchers_count"]
                s = val["language"]

                if s != None:
                    s = normalizeLang(s)
                    setLangs.add(s)

                topics += len(val["topics"])
        else:
            error = True

        if (responseBitbucket.status_code == 200):
            # Bitbucket fork count is in a different API,
            # so it looks like this API is all original repos
            originals += len(jsonBitbucket["values"])

            for val in jsonBitbucket["values"]:
                url = val["links"]["watchers"]["href"]
                response = requests.get(url)
                json = response.json()
                watchers += json["size"]

                s = val["language"]

                if s != None:
                    s = normalizeLang(s)
                    setLangs.add(s)

                # bitbucket doesn't seem to have topics
        else:
            error = True
    else:
        error = True

    dict = {"originals": originals,
        "forks": forks,
        "watchers": watchers,
        "langs": len(setLangs),
        "topics": topics,
        "error": error
        }

    return jsonify(dict)
    