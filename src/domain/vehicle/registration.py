def normalize_registration_number(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = "".join(character for character in value.upper() if character.isalnum())
    return normalized or None
