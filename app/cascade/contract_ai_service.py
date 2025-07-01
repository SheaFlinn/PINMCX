from app.cascade.scraper_to_draft import transform_headline_to_draft
from app.cascade.reframer_api import reframe_title_as_question
from app.cascade.refiner_api import refine_question_with_scope
from app.cascade.patcher_api import patch_bias_and_vagueness
from app.cascade.filter_api import filter_contract_quality
from app.cascade.weigher_api import weigh_contract_predictive_value
from app.cascade.balancer_api import balance_for_odds_and_xp
from app.cascade.publisher_api import publish_contract

class ContractAIService:
    """
    Orchestrates the full 8-stage cascade pipeline for civic contract generation.
    Can be called from admin routes, APIs, or backend schedulers.
    """

    def __init__(self, headline: str, city: str = "Memphis"):
        self.headline = headline
        self.city = city
        self.draft = {}

    def run_full_chain(self) -> dict:
        """
        Executes the complete 8-stage cascade pipeline.
        Returns the final draft dictionary with all processing stages applied.
        """
        self.draft = transform_headline_to_draft(self.headline, self.city)
        self.draft = reframe_title_as_question(self.draft)
        self.draft = refine_question_with_scope(self.draft)
        self.draft = patch_bias_and_vagueness(self.draft)
        self.draft = filter_contract_quality(self.draft)

        if self.draft.get("status") != "rejected":
            self.draft = weigh_contract_predictive_value(self.draft)
            self.draft = balance_for_odds_and_xp(self.draft)
            self.draft = publish_contract(self.draft)

        return self.draft

    def get_stage_log(self) -> list:
        """
        Returns the complete stage log for this contract's processing.
        """
        return self.draft.get("stage_log", [])

    def get_final_status(self) -> str:
        """
        Returns the final status of the contract (draft, rejected, or published).
        """
        return self.draft.get("status", "unknown")
