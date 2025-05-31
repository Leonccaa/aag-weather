from pydantic_settings import BaseSettings
from pydantic import BaseModel, Field
from enum import StrEnum


class WhichUnits(StrEnum):
    metric = 'metric'
    imperial = 'imperial'
    none = 'none'


class Thresholds(BaseModel):
    cloudy: float = -25
    very_cloudy: float = -15
    windy: float = 50
    very_windy: float = 75
    gusty: float = 100
    very_gusty: float = 125
    wet: int = 2200
    rainy: int = 1800


class Heater(BaseModel):
    # 雨盘加热（Rain Sensor Heater）相关
    rain_threshold_freq: float = Field(default=30.0, description="雨频判“湿”阈值 (Hz)")
    pwm_max: float = Field(default=70.0, description="湿态/下雨加热功率 (%)")
    pwm_mid: float = Field(default=40.0, description="中温加热功率 (盘面干燥，温度低于低温阈值时, %)")
    pwm_low: float = Field(default=15.0, description="低温轻度保温功率 (%)")
    hysteresis: float = Field(default=5.0, description="PWM 变化缓冲 (%)")
    
    # 环境温度阈值组
    low_temp: float = Field(default=0.0, description="最低保温温度 (°C)")
    low_delta: float = Field(default=6.0, description="低温缓冲区大小 (°C)")
    high_temp: float = Field(default=20.0, description="最高关闭温度 (°C)") # 修正拼写
    high_delta: float = Field(default=4.0, description="高温缓冲区大小 (°C)") # 修正拼写
    
    # 冲击加热（Impulse Heater）部分
    impulse_temp: float = Field(default=10.0, description="冲击加热触发温度 (°C)")
    impulse_duration: float = Field(default=60.0, description="冲击加热持续时间 (秒)")
    impulse_cycle: int = Field(default=600, description="冲击加热循环周期 (秒)")

    # 运行时初始状态 (min_power 用于 connect() 中的初始设置)
    min_power: float = Field(default=15, description="传感器连接时设置的初始PWM功率 (%)")


class Location(BaseModel):
    name: str = 'AAG CloudWatcher'
    elevation: float = 60.0  # meters
    latitude: float = 49.054  # degrees
    longitude: float = -122.82  # degrees
    timezone: str = 'America/Vancouver'

class Skytemp(BaseModel):
    K1: float = 33.0
    K2: float = 0.0
    K3: float = 0.0
    K4: float = 0.0
    K5: float = 0.0
    K6: float = 140.0
    K7: float = 40.0


class WeatherSettings(BaseSettings):
    serial_port: str = '/dev/ttyUSB0'
    safety_delay: float = 15  # minutes
    capture_delay: float = 30  # seconds
    num_readings: int = 10
    sq_reference: float = 19.6 # SQReference
    ignore_unsafe: bool | None = None  # None, otherwise can be a list, e.g. 'rain','cloud','gust','wind'
    verbose_logging: bool = False
    serial_port_open_delay_seconds: float = 1 # seconds
    solo_data_file_path: str = './'
    have_heater: bool = False
    thresholds: Thresholds = Thresholds()
    heater: Heater = Heater()
    location: Location = Location()
    skytemp: Skytemp = Skytemp()

    class Config:
        env_prefix = 'AAG_'
        env_file = 'config.env'
        env_nested_delimiter = '__'


class WeatherPlotter(BaseModel):
    ambient_temp: tuple[int, int] = (-5, 45)  # celsius
    cloudiness: tuple[int, int] = (-45, 5)
    wind: tuple[int, int] = (0, 50)  # kph
    rain: tuple[int, int] = (700, 7000)
    pwm: tuple[int, int] = (-5, 105)  # percent


