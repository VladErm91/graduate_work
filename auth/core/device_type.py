from core.config import DEVICES
from user_agents import parse


def get_device_type(user_agent: str) -> str:
    user_agent = parse(user_agent)
    if user_agent.is_pc:
        return DEVICES[0]
    if user_agent.is_mobile or user_agent.is_tablet:
        return DEVICES[1]
    return DEVICES[2]
