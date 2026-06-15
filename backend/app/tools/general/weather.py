# backend/app/tools/general/weather.py
from langchain_core.tools import tool
from typing import Dict, Any
import logging
import os
import requests
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


@tool
def weather_tool(city: str = "Hanoi") -> Dict[str, Any]:
    """
    Lấy thông tin thời tiết (sử dụng OpenWeatherMap)
    """
    api_key = os.getenv("OPENWEATHER_API_KEY")
    
    if not api_key:
        return {
            "status": "info",
            "answer": f"Thời tiết tại **{city}**: \nHiện tại chưa có API key. Bạn có thể cung cấp API key OpenWeatherMap để tôi lấy dữ liệu thời tiết thực tế.",
            "note": "Cần cấu hình OPENWEATHER_API_KEY trong .env"
        }

    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=vi"
        response = requests.get(url, timeout=8)
        
        if response.status_code != 200:
            return {"status": "error", "message": f"Không tìm thấy thông tin thời tiết cho thành phố: {city}"}

        data = response.json()
        
        weather_desc = data['weather'][0]['description']
        temp = data['main']['temp']
        feels_like = data['main']['feels_like']
        humidity = data['main']['humidity']
        wind_speed = data['wind']['speed']

        answer = f"""
**Thời tiết tại {city.title()}**

🌡️ Nhiệt độ: **{temp}°C** (cảm giác như {feels_like}°C)
☁️ Trạng thái: **{weather_desc.capitalize()}**
💧 Độ ẩm: **{humidity}%**
🌬️ Tốc độ gió: **{wind_speed} m/s**
        """

        return {
            "status": "success",
            "answer": answer.strip(),
            "source": "weather"
        }

    except Exception as e:
        logger.error(f"Weather Tool Error: {e}")
        return {
            "status": "error",
            "message": f"Không thể lấy thông tin thời tiết cho {city}. Vui lòng thử lại sau."
        }