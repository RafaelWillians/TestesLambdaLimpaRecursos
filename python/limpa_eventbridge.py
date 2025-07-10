import boto3
import os
import time

def cleanup_eventbridge(, region):
    print(f"[{region}] --- Iniciando limpeza do EventBridge")

    # Excluir Regras do EventBridge
    try:
        