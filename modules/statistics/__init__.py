from fastapi import FastAPI
from modules.statistics.api_statistics import register_api_statistics_route

def configure_statistics_module(app: FastAPI):
    register_api_statistics_route(app)

