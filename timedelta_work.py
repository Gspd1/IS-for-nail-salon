from datetime import timedelta


def timedelta_to_string(timedelta_value: timedelta) -> str:
    hours, minutes, seconds = str(timedelta_value).split(":")

    hours = f"0{hours}" if len(hours) == 1 else hours
    minutes = f"0{minutes}" if len(minutes) == 1 else minutes

    return f"{hours}:{minutes}"
