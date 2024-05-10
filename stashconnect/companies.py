from .models import Company


class CompanyManager:
    def __init__(self, client) -> None:
        self.client = client

    def info(self, company_id: str | int) -> Company:
        """Gets the info of a company

        Args:
            company_id (str | int): The companies id.

        Returns:
            Company: A company object.
        """
        response = self.client._post("company/details", data={"company_id": company_id})
        return Company(self.client, response["company"])

    def member(self) -> list:
        """Lists the companies of the logged in user

        Returns:
            list: The company objects in a list.
        """
        response = self.client._post("company/member", data={"no_cache": True})
        return [Company(self.client, data) for data in response["companies"]]

    def get_settings(self, company_id: str | int) -> dict:
        """Gets the settings of a company

        Args:
            company_id (str | int): The companies id.

        Returns:
            dict: The companies settings.
        """
        response = self.client._post(
            "company/settings", data={"company_id": company_id}
        )
        return response["settings"]
