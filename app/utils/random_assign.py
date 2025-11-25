import random
from typing import Iterable, List, Tuple


def random_assign(
    participants: Iterable[Tuple[int, List[int]]]
) -> List[Tuple[int, int]]:
    """
    Assign each giver to a receiver ensuring:
    - no one gets themselves
    - respect exclude_list

    participants: iterable of tuples (giver_id, user_id, exclude_list)
    """
    givers = list(participants)
    receivers = [user_id for user_id, _ in givers]

    for _ in range(1000):
        random.shuffle(receivers)
        if _is_valid(givers, receivers):
            return [
                (giver_user_id, receiver)
                for (giver_user_id, _), receiver in zip(givers, receivers, strict=True)
            ]

    raise RuntimeError("Не удалось выполнить жеребьёвку. Попробуйте позже.")


def _is_valid(
    givers: List[Tuple[int, List[int]]], receivers: List[int]
) -> bool:
    for (giver_user_id, exclude), receiver in zip(givers, receivers, strict=True):
        if giver_user_id == receiver:
            return False
        if receiver in (exclude or []):
            return False
    return True

