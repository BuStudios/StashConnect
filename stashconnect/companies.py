from .users import User


class CompanyHandler:
    def __init__(self, client):
        self.client = client

    def info(self, company_id: str | int):
        response = self.client._post("company/details", data={"company_id": company_id})
        return Company(self.client, response["company"])

    def member(self):
        response = self.client._post("company/member", data={"no_cache": True})
        return [Company(self.client, data) for data in response["companies"]]


class Company:
    def __init__(self, client, data):
        self.client = client
        self.id = data["id"]

        self.name = data["name"]
        self.manager = User(self.client, data["manager"])

        self.time_created = data["created"]
        self.time_joined = data["time_joined"]
        self.unread_messages = data["unread_messages"]

        self.logo_url = data["logo_url"]
        self.domain = data["domain"]

        self.max_users = data["max_users"]
        self.active_users = data["users"]["active"]
        self.created_users = data["users"]["created"]

        self.membership_expiry = data["membership_expiry"]
        self.online_payment = data["online_payment"]
        self.protected = data["protected"]

        self.provider = data["provider"]
        self.quota = data["quota"]
        self.freemium = data["freemium"]

        self.deactivated = data["deactivated"]
        self.deleted = data["deleted"]
        self.features = data["features"]

        self.permission = data["permission"]
        self.roles = data["roles"]
        self.settings = data["settings"]
