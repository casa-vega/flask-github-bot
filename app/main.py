from datetime import datetime, timezone
import time # for sleep, not required


from flask import Flask, request
from github import Github, GithubIntegration
from yaml import load, SafeLoader


app = Flask(__name__)


@app.route("/demo", methods=["POST"])
def demo():
    req = request.json
    if "action" in req and "pull_request" in req:
        if req["action"] == "opened" or req["action"] == "synchronize":
            cr = GithubCheckRun(req)
            cr.create()
            time.sleep(15)
            """
            ^^^
            this is where the magic happens, or where you would otherwise put
            your code. You would also want to properly return http status codes
            and set your status based on the result of your code.
            """
            cr.update_success()
    return ("", 201)
    


class GithubApp(object):
    def __init__(self):
        self.meta = config
        self._auth, self.expires_at, self.gh = None, None, None
        with open(self.meta["pem"]) as private_key:
            self.private_key = private_key.read()


    @staticmethod
    def auth(func):
        def wrapper(self, *args, **kwargs):
            self.github_client() if not self.gh or self.is_expired() else None
            return func(self, *args, **kwargs)
        return wrapper


    def is_expired(self):
        return datetime.now().timestamp() + 60 >= self.expires_at.timestamp()


    def token(self):
        return GithubIntegration(
            self.meta.get("app_id"), self.private_key
        ).get_access_token(self.meta.get("installation_id"))


    def github_client(self):
        self._auth = self.token()
        self.gh = Github(self._auth.token)
        self.expires_at = self._auth.expires_at.replace(tzinfo=timezone.utc)


class GithubCheckRun(GithubApp):

    def __init__(self, req):
        super().__init__()
        self.req = req


    @GithubApp.auth
    def check_run(self, **kwargs):
        repo = self.gh.get_repo(self.req["repository"]["full_name"])
        repo.create_check_run(**{
            "name": "integration/flask-demo",
            "head_sha": self.req["pull_request"]["head"]["sha"],
            "started_at": datetime.now(),
            "details_url": self.req["pull_request"]["html_url"],
            "external_id": str(self.req["pull_request"]["number"]),
            **kwargs
        })


    def create(self):
        self.check_run(status="in_progress")


    def update_success(self):
        self.check_run(status="completed", conclusion="success")


    def update_failure(self):
        self.check_run(status="completed", conclusion="failure")


if __name__ == "__main__":
    with open("config.yml") as config_file:
        config = load(config_file, Loader=SafeLoader)

    app.run(host="0.0.0.0", debug=False, port=8443)