from .models import Company


class CompanyManager:
    def __init__(self, client):
        self.client = client

    def info(self, company_id: str | int):
        response = self.client._post("company/details", data={"company_id": company_id})
        return Company(self.client, response["company"])

    def member(self):
        response = self.client._post("company/member", data={"no_cache": True})
        return [Company(self.client, data) for data in response["companies"]]
