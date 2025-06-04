"""Wrapper around trophy utilities for core app use."""
from trophies.utils import check_and_award_trophies


def award_login_trophies(user):
    """Award trophies related to login events."""
    check_and_award_trophies(user)
