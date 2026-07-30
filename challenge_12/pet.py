import math
import random

from settings import (
    ACTION_COSTS,
    ACTION_EFFECTS,
    ENERGY_SLEEP_WAKE_THRESHOLD,
    FOOD_DEATH_COUNTDOWN,
    GAME_SECONDS_PER_REAL_SECOND,
    HAPPINESS_RECOVERY_RATE,
    HEALTHY_STAT_THRESHOLD,
    MOOD_LOW_THRESHOLD,
    MOOD_RECOVERY_THRESHOLD,
    PET_ADULT_AGE_DAYS,
    PET_DEFAULT_NAME,
    PET_NAME_MAX_LENGTH,
    PET_PERSONALITIES,
    PET_SENIOR_AGE_DAYS,
    PERSONALITY_PROFILES,
    REST_DURATION,
    SIMULATION_STEP_SECONDS,
    SLEEP_ENERGY_GAIN_RATE,
    SLEEP_FOOD_COST,
    STAT_DECAY_RATES,
    STAT_MAX,
    STAT_MIN,
    STORE_ITEMS,
)


def clamp(value, minimum=STAT_MIN, maximum=STAT_MAX):
    return max(minimum, min(maximum, value))


def finite_number(value):
    if isinstance(value, bool):
        raise ValueError("Boolean values are not valid numbers")

    number = float(value)
    if not math.isfinite(number):
        raise ValueError("Save-file numbers must be finite")
    return number


def saved_boolean(value):
    if not isinstance(value, bool):
        raise ValueError("Save-file boolean fields must be true or false")
    return value


class Pet:
    """Pygame-free state and rules for the pet simulation."""

    def __init__(self, personality=None):
        if personality is None:
            personality = random.choice(PET_PERSONALITIES)
        if personality not in PERSONALITY_PROFILES:
            raise ValueError(f"Unknown pet personality: {personality}")

        self.stats = {
            "food": 100,
            "happiness": 100,
            "energy": 100,
        }
        self.balance = 100
        self.dead = False
        self.food_death_timer = FOOD_DEATH_COUNTDOWN
        self.rest_timer = 0
        self.energy_sleeping = False
        self.age_seconds = 0.0
        self.name = PET_DEFAULT_NAME
        self.personality = personality
        self._reset_mood_tracking()

    def update(self, dt):
        """Advance the simulation and return whether the pet woke this update."""
        if self.dead:
            return False

        elapsed = float(dt)
        if not math.isfinite(elapsed):
            raise ValueError("Elapsed time must be finite")
        if elapsed < 0:
            return False
        if elapsed == 0:
            return self._update_step(0)

        remaining = elapsed
        woke_up = False

        while remaining > 0:
            step = min(remaining, SIMULATION_STEP_SECONDS)
            woke_up = self._update_step(step) or woke_up
            remaining -= step

        return woke_up

    def _update_step(self, dt):
        """Advance one bounded simulation step."""
        self._update_energy_sleep_state()
        was_sleeping = self.is_sleeping()
        self._update_stats(dt, sleeping=was_sleeping)
        self._update_food_death_timer(dt)
        self._update_rest_timer(dt)
        self._update_energy_sleep_state()

        woke_up = was_sleeping and not self.is_sleeping()
        if woke_up:
            self._apply_sleep_food_cost()

        self._record_mood_changes()
        return woke_up

    def update_age(self, dt):
        if not self.dead:
            self.age_seconds += max(0, dt) * GAME_SECONDS_PER_REAL_SECOND

    @property
    def age_text(self):
        days = int(self.age_seconds // (24 * 60 * 60))
        return f"{days}D"

    @property
    def life_stage(self):
        age_days = self.age_seconds / (24 * 60 * 60)
        if age_days < PET_ADULT_AGE_DAYS:
            return "BABY"
        if age_days < PET_SENIOR_AGE_DAYS:
            return "ADULT"
        return "SENIOR"

    @property
    def personality_profile(self):
        return PERSONALITY_PROFILES[self.personality]

    @property
    def animation_choices(self):
        return self.personality_profile["animation_choices"]

    def can_perform(self, action):
        if action not in ACTION_COSTS:
            return False

        if self.dead or self.is_resting():
            return False

        if self.is_sad() and action == "play":
            return False

        action_blocked = action in ("play", "rest")
        condition_blocked = (
            action_blocked
            and (self.is_food_death_active() or self.is_energy_sleep_active())
        )
        return (
            not condition_blocked
            and self.balance >= ACTION_COSTS[action]
        )

    def perform(self, action):
        if not self.can_perform(action):
            return False

        self.balance -= ACTION_COSTS[action]
        for stat, change in ACTION_EFFECTS[action].items():
            multiplier = (
                self.personality_profile["actions"]
                .get(action, {})
                .get(stat, 1.0)
            )
            self.stats[stat] = clamp(
                self.stats[stat] + change * multiplier
            )

        if action == "rest":
            self.rest_timer = REST_DURATION

        self._record_mood_changes()
        return True

    def buy(self, item_name):
        item = STORE_ITEMS.get(item_name)
        if item is None or self.balance < item["price"]:
            return False

        self.balance -= item["price"]
        for stat, change in item["effects"].items():
            self.stats[stat] = clamp(self.stats[stat] + change)

        self._record_mood_changes()
        return True

    def drain_mood_events(self):
        events = self._mood_events
        self._mood_events = []
        return events

    def to_dict(self):
        return {
            "stats": self.stats.copy(),
            "balance": self.balance,
            "dead": self.dead,
            "food_death_timer": self.food_death_timer,
            "rest_timer": self.rest_timer,
            "energy_sleeping": self.energy_sleeping,
            "age_seconds": self.age_seconds,
            "name": self.name,
            "personality": self.personality,
        }

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict):
            raise ValueError("Pet save data must be an object")

        stats = data.get("stats")
        if not isinstance(stats, dict):
            raise ValueError("Pet save data is missing stats")

        try:
            personality = data.get("personality", "BALANCED")
            if personality not in PERSONALITY_PROFILES:
                raise ValueError("Unknown pet personality")

            pet = cls(personality=personality)
            pet.stats = {
                stat: clamp(finite_number(stats[stat]))
                for stat in ("food", "happiness", "energy")
            }
            pet.balance = max(0, int(finite_number(data["balance"])))
            pet.dead = saved_boolean(data["dead"])
            pet.food_death_timer = max(
                0,
                finite_number(data["food_death_timer"]),
            )
            pet.rest_timer = max(0, finite_number(data["rest_timer"]))
            pet.energy_sleeping = saved_boolean(data["energy_sleeping"])
            pet.age_seconds = max(
                0,
                finite_number(data.get("age_seconds", 0)),
            )
            name = str(data.get("name", PET_DEFAULT_NAME)).strip()
            pet.name = name[:PET_NAME_MAX_LENGTH] or PET_DEFAULT_NAME
        except (KeyError, OverflowError, TypeError, ValueError) as error:
            raise ValueError("Pet save data is invalid") from error

        pet._reset_mood_tracking()
        return pet

    def _reset_mood_tracking(self):
        self._mood_states = {
            stat: value <= MOOD_LOW_THRESHOLD
            for stat, value in self.stats.items()
        }
        self._mood_events = []

    def _record_mood_changes(self):
        for stat, value in self.stats.items():
            was_low = self._mood_states[stat]

            if not was_low and value <= MOOD_LOW_THRESHOLD:
                self._mood_states[stat] = True
                self._mood_events.append((stat, "low"))

            elif was_low and value >= MOOD_RECOVERY_THRESHOLD:
                self._mood_states[stat] = False
                self._mood_events.append((stat, "recovered"))

    def _update_stats(self, dt, sleeping=False):
        for stat, rate in STAT_DECAY_RATES.items():
            if sleeping and stat == "food":
                continue

            if sleeping and stat == "energy":
                rate = (
                    SLEEP_ENERGY_GAIN_RATE
                    * self.personality_profile["sleep_energy_gain"]
                )
            else:
                if stat == "happiness" and self.is_happiness_recovering():
                    rate = HAPPINESS_RECOVERY_RATE

                rate *= self.personality_profile["stat_rates"].get(
                    stat,
                    1.0,
                )
            self.stats[stat] = clamp(self.stats[stat] + rate * dt)

    def _apply_sleep_food_cost(self):
        self.stats["food"] = clamp(self.stats["food"] - SLEEP_FOOD_COST)

    def _update_food_death_timer(self, dt):
        if self.stats["food"] > 0:
            self.food_death_timer = FOOD_DEATH_COUNTDOWN
            return

        self.food_death_timer = max(0, self.food_death_timer - dt)
        if self.food_death_timer <= 0:
            self.dead = True

    def _update_rest_timer(self, dt):
        self.rest_timer = max(0, self.rest_timer - dt)

    def _update_energy_sleep_state(self):
        if self.stats["energy"] <= 0:
            self.energy_sleeping = True
        elif (
            self.energy_sleeping
            and self.stats["energy"] >= ENERGY_SLEEP_WAKE_THRESHOLD
        ):
            self.energy_sleeping = False

    def is_resting(self):
        return self.rest_timer > 0

    def is_food_death_active(self):
        return self.stats["food"] <= 0 and not self.dead

    def is_energy_sleep_active(self):
        return self.energy_sleeping and not self.dead

    def is_sad(self):
        return self.stats["happiness"] <= 0 and not self.dead

    def is_happiness_recovering(self):
        return (
            self.stats["food"] >= HEALTHY_STAT_THRESHOLD
            and self.stats["energy"] >= HEALTHY_STAT_THRESHOLD
        )

    def is_sleeping(self):
        return not self.is_food_death_active() and (
            self.is_resting() or self.is_energy_sleep_active()
        )
