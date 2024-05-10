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

    def email_templates(self, company_id: str | int) -> dict:
        """Gets the email templates of the company

        Args:
            company_id (str | int): The companies id.

        Returns:
            dict: Return a dict i think
        """
        response = self.client._post(
            "server/get_email_templates", data={"company_id": company_id}
        )
        return response["templates"]

    def get_ldaps(self, company_id: str | int) -> dict:
        """Gets the companies ldaps [untested]

        Args:
            company_id (str | int): The companies id.

        Returns:
            dict: [untested]
        """
        response = self.client._post(
            "connections/servers", data={"company_id": company_id}
        )
        return response["servers"]

    def delete(self, company_id: str | int) -> dict:
        """Deletes the company [dangerous!]

        Args:
            company_id (str | int): The companies id.

        Returns:
            dict: The success status.
        """
        response = self.client._post(
            "server/delete_company", data={"company_id": company_id}
        )
        return response

    def quit(self, company_id: str | int) -> dict:
        """Leaves a company [dangerous!]

        Args:
            company_id (str | int): The companies id.

        Returns:
            dict: The success status.
        """
        response = self.client._post("company/quit", data={"company_id": company_id})
        return response

    def list_features(self, company_id: str | int) -> dict:
        """Lists company features

        Args:
            company_id (str | int): The companies id.

        Returns:
            dict: Company features
        """
        response = self.client._post(
            "server/list_company_features", data={"company_id": company_id}
        )
        return response["company_features"]

    def get_market(self, company_id: str | int) -> dict:
        """Gets the companies market

        Args:
            company_id (str | int): The companies id.

        Returns:
            dict: The market
        """
        response = self.client._post(
            "manage/get_company_market", data={"company_id": company_id}
        )
        return response["market"]
