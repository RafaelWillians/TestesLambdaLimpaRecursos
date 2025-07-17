import boto3
import os
import time


# API Gateway v1
def cleanup_apiv1(apigateway_v1, region):
    print(f"[{region}] --- Iniciando limpeza do API Gateway (v1)")

    try:
        apilist = apigateway_v1.get_rest_apis(limit=500)
        if not apilist['items']:
            print(f"Nenhuma API REST encontrada.")

        for api in apilist.get('items', []):
            api_id = api['id']
            api_name = api.get('name', 'sem nome')
            print(f"[V1] Excluindo API: {api_name} (ID: {api_id})")

            # Exclusao dos stages
            try:
                stages = apigateway_v1.get_stages(restApiId=api_id)
                for stage in stages.get('item', []):
                    stage_name = stage['stageName']
                    print(f"[V1] Excluindo stage: {stage_name}")
                    try: 
                        apigateway_v1.delete_stage(restApiId=api_id, stageName=stage_name)
                    except Exception as stage_e:
                        print(f"[{region}] Erro ao excluir stage {stage_name}: {stage_e}")
            except Exception as stage_list_e:
                print(f"[{region}] Erro ao listar stages: {stage_list_e}")

            # Exclusao dos deployments
            deployments = apigateway_v1.get_deployments(restApiId=api_id)
            for deployment in deployments.get('items', []):
    
    except Exception as e:
        print(f"[{region}] Erro ao listar APIs: {e}")



# API Gateway v2
def cleanup_apiv2(apigateway_v2, region):
    print(f"[{region}] --- Iniciando limpeza do API Gateway (v2)")



def lambda_handler(event, context):
    target_regions_str = os.environ.get('TARGET_REGIONS', 'us-east-1,us-east-2')
    regions = [region.strip() for region in target_regions_str.split(',') if region.strip()]
    print(f"Variável TARGET_REGIONS recebida: {target_regions_str}")
    print(f"Iniciando limpeza para as regiões: {regions}")

    for region in regions:
        print(f"\n================ PROCESSANDO REGIÃO: {region} ================")
        apigateway_v1 = boto3.client('apigateway')
        apigateway_v2 = boto3.client('apigatewayv2')

        cleanup_apiv1(apigateway_v1, region)
        cleanup_apiv2(apigateway_v1, region)
    
    result_message = f"Processo de limpeza de recursos concluído para as regiões: {regions}"
    print(f"\n{result_message}")
    return {'statusCode': 200, 'body': result_message}