import boto3
import os
import time

def cleanup_sns_subscription(sns_client, region):
    print(f"[{region}] --- Iniciando limpeza de assinaturas do SNS")

    try:
        paginator = sns_client.get_paginator('list_topics')
        for page in paginator.paginate():
            for topic in page['Topics']:
                topic_arn = topic['TopicArn']
                print(f"[{region}] Excluindo tópico: {topic_arn}")
                try:
                    sns_client.delete_topic(TopicArn=topic_arn)
                except Exception as sns_e:
                    print(f"[{region}] Erro ao excluir tópico SNS {topic_arn}: {sns_e}")


def cleanup_sqs(sqs_client, region):
    print(f"[{region}] --- Iniciando limpeza de assinaturas do SNS")

    try:
        queues = sqs_client.list_queues()
        queue_urls = queue.get('QueueUrls', [])

        for queue_url in queue_urls:
            print(f"[{region}] Excluindo fila SQS: {queue_url}")
            try:
                sqs_client.delete_queue(QueueUrl=queue_url)
            except Exception as sqs_e:
                print(f"[{region}] Erro ao excluir fila SQS {queue_url}: {sqs_e}")
    except Exception as e:
        print(f"[{region}] Erro ao listar filas SQS: {e}")
    




def lambda_handler(event, context):
    target_regions_str = os.environ.get('TARGET_REGIONS', 'us-east-1,us-east-2')
    regions = [region.strip() for region in target_regions_str.split(',') if region.strip()]
    print(f"Variável TARGET_REGIONS recebida: {target_regions_str}")
    print(f"Iniciando processo de limpeza para as regiões: {regions}")

    for region in regions:
        print(f"\n================ PROCESSANDO REGIÃO: {region} ================")
        sns_client = boto3.client('sns', region_name=region)
        sqs_client = boto3.client('sqs', region_name=region)

        cleanup_sns(sns_client, region)
        cleanup_sqs(sqs_client, region)

result_message = f"Processo de limpeza de recursos concluído para as regiões: {regions}."
print(f"\n{result_message}")
return {'statusCode': 200, 'body': result_message}