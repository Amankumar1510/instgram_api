class MultipleAccountsMixin:
    """
    Helpers for multiple accounts.
    """

    def featured_accounts_v1(self, target_user_id: str) -> dict:
        print(f"[TRACE] ENTERING: instagrapi/mixins/multiple_accounts.py -> featured_accounts_v1")
        target_user_id = str(target_user_id)
        return self.private_request(
            "multiple_accounts/get_featured_accounts/",
            params={"target_user_id": target_user_id},
        )

    def get_account_family_v1(self) -> dict:
        print(f"[TRACE] ENTERING: instagrapi/mixins/multiple_accounts.py -> get_account_family_v1")
        return self.private_request("multiple_accounts/get_account_family/")
