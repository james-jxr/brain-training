from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from backend.models import DomainProgress
from backend.services.adaptive_difficulty import AdaptiveDifficultyService, adjust_difficulty_in_session

class SessionPlannerService:
    DOMAIN_EXERCISE_MAP = {
        "processing_speed": ["symbol_matching", "visual_categorisation"],
        "working_memory": ["n_back", "digit_span"],
        "attention": ["go_no_go", "stroop"],
        "mindfulness": ["mindfulness"]
    }

    MINIMUM_ROUNDS = {
        "card_memory": 3
    }

    NO_SCORING_EXERCISES = {"mindfulness"}

    @staticmethod
    def plan_session(db: Session, user_id: int):
        domains = ["processing_speed", "working_memory", "attention"]
        domain_scores = {}

        for domain in domains:
            progress = db.query(DomainProgress).filter(
                and_(
                    DomainProgress.user_id == user_id,
                    DomainProgress.domain == domain
                )
            ).first()

            if progress and progress.last_score is not None:
                domain_scores[domain] = progress.last_score
            else:
                domain_scores[domain] = 0

        sorted_domains = sorted(domain_scores.items(), key=lambda x: x[1])

        max_score = max(domain_scores.values()) if domain_scores else 0

        # If the weakest domain is significantly behind (more than 10 points below
        # the maximum), prioritise it to help the user catch up. Otherwise, the
        # domains are roughly balanced, so prioritise the highest-scoring domain
        # to maintain momentum via rotation.
        priority_domain = sorted_domains[0][0] if sorted_domains[0][1] < max_score - 10 else sorted_domains[-1][0]
        other_domains = [d for d in domains if d != priority_domain]
        selected_domain_2 = other_domains[0] if other_domains else domains[0]

        exercises = {
            priority_domain: SessionPlannerService.DOMAIN_EXERCISE_MAP[priority_domain],
            selected_domain_2: SessionPlannerService.DOMAIN_EXERCISE_MAP[selected_domain_2],
            "mindfulness": SessionPlannerService.DOMAIN_EXERCISE_MAP["mindfulness"]
        }

        return {
            "domain_1": priority_domain,
            "domain_2": selected_domain_2,
            "exercises": exercises
        }

    @staticmethod
    def get_trials_per_domain() -> int:
        return 8

    @staticmethod
    def get_trials_per_exercise() -> int:
        return 4

    @staticmethod
    def get_rounds_for_exercise(exercise_name: str) -> int:
        minimum = SessionPlannerService.MINIMUM_ROUNDS.get(exercise_name, 1)
        return max(minimum, 1)

    @staticmethod
    def is_no_scoring_exercise(exercise_name: str) -> bool:
        return exercise_name in SessionPlannerService.NO_SCORING_EXERCISES
