# backend/app/tools/general/__init__.py

from .calculator import calculator_tool
from .date_time import date_time_tool
from .weather import weather_tool

# Uncomment khi implement
# from .web_search import web_search_tool

general_tools_list = [
    calculator_tool,
    date_time_tool,
    weather_tool,
    # web_search_tool,
]

__all__ = [
    "calculator_tool",
    "date_time_tool",
    "weather_tool",
    "general_tools_list",
]