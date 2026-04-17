import random
import string

MIN_CARD_MEMORY_ROUNDS = 3

class ExerciseGeneratorService:
    @staticmethod
    def generate_symbol_matching(difficulty: int):
        symbols = ['◯', '□', '△', '◇', '★', '♡', '▪', '●', '✕', '⬡']
        target_idx = random.randint(0, len(symbols) - 1)
        target = symbols[target_idx]

        num_distractors = min(3, difficulty // 3 + 2)
        distractors = [symbols[i] for i in range(len(symbols)) if i != target_idx]
        distractors = random.sample(distractors, min(num_distractors, len(distractors)))
        options = [target] + distractors
        random.shuffle(options)

        return {
            "target": target,
            "options": options,
            "correct_index": options.index(target)
        }

    @staticmethod
    def generate_visual_categorisation(difficulty: int):
        categories = ["living", "non-living"]
        items_living = ["cat", "tree", "dog", "flower", "bird", "fish", "elephant", "bear"]
        items_non_living = ["chair", "car", "book", "table", "phone", "cup", "shoe", "hat"]

        item_pool = items_living + items_non_living
        item = random.choice(item_pool)
        correct_category = categories[0] if item in items_living else categories[1]

        return {
            "item": item,
            "categories": categories,
            "correct_category": correct_category
        }

    @staticmethod
    def generate_n_back(difficulty: int):
        if difficulty <= 3:
            n = 1
        elif difficulty <= 6:
            n = 2
        else:
            n = 3

        letters = list(string.ascii_uppercase[:15])
        sequence = [random.choice(letters) for _ in range(15 + n)]

        target_positions = []
        for i in range(n, len(sequence)):
            if sequence[i] == sequence[i - n]:
                target_positions.append(i)

        return {
            "n": n,
            "sequence": sequence,
            "target_positions": target_positions
        }

    @staticmethod
    def generate_digit_span(difficulty: int):
        min_length = 3
        max_length = min(12, 3 + difficulty)
        length = random.randint(min_length, max_length)

        digits = [str(random.randint(0, 9)) for _ in range(length)]
        return {
            "digits": digits,
            "expected_response": "".join(digits)
        }

    @staticmethod
    def generate_go_no_go(difficulty: int):
        num_trials = 15
        go_ratio = max(0.4, 1.0 - (difficulty * 0.05))
        num_go = int(num_trials * go_ratio)
        num_no_go = num_trials - num_go

        trials = ["go"] * num_go + ["no_go"] * num_no_go
        random.shuffle(trials)

        return {
            "trials": trials
        }

    @staticmethod
    def generate_stroop(difficulty: int):
        colors_text = ["RED", "BLUE", "GREEN", "YELLOW"]
        colors_rgb = ["red", "blue", "green", "yellow"]

        num_options = min(4, 2 + difficulty // 3)
        options = random.sample(colors_rgb, num_options)

        word = random.choice(colors_text)
        ink_color_idx = random.randint(0, len(options) - 1)
        ink_color = options[ink_color_idx]

        return {
            "word": word,
            "ink_color": ink_color,
            "options": options,
            "correct_index": ink_color_idx
        }

    @staticmethod
    def generate_card_memory(difficulty: int, num_rounds: int = None):
        if num_rounds is None:
            num_rounds = MIN_CARD_MEMORY_ROUNDS
        num_rounds = max(num_rounds, MIN_CARD_MEMORY_ROUNDS)

        rounds = []
        for _ in range(num_rounds):
            rounds.append(ExerciseGeneratorService._generate_single_card_memory_round(difficulty))

        return {
            "rounds": rounds,
            "total_rounds": num_rounds
        }

    @staticmethod
    def _generate_single_card_memory_round(difficulty: int):
        shapes = ['◯', '△', '★', '□', '◇']
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E2']

        if difficulty <= 3:
            card_count = 4
        elif difficulty <= 6:
            card_count = 8
        else:
            card_count = 12

        cards = []
        used_pairs = set()
        while len(cards) < card_count:
            shape = random.choice(shapes)
            color = random.choice(colors)
            pair = f"{shape}-{color}"
            if pair not in used_pairs:
                used_pairs.add(pair)
                cards.append({
                    "id": len(cards),
                    "shape": shape,
                    "color": color,
                    "pair": pair
                })

        target = random.choice(cards)

        return {
            "cards": cards,
            "target": target,
            "card_count": card_count
        }
