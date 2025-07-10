def cleanup_sg(ec2_client, region):
    print(f"[{region}] --- Iniciando limpeza de grupos de segurança EC2")

    try:
        sgs = ec2_client.describe_security_groups()
        print(f"[{region}] Encontrado {len(sgs['SecurityGroups'])} grupos de segurança")
        for sg in sgs['SecurityGroups']:
            group_id = sg['GroupId']
            group_name = sg['GroupName']

            if group_name != 'default':
                try:
                    ec2_client.delete_security_group(GroupId=group_id)
                    print(f"[{region}] Grupo deletado: {group_id} ({group_name})")
                except Exception as sg_e:
                    print(f"[{region}] Erro ao deletar grupo {group_id}: {sg_e}")
            else:
                print(f"[{region}] Ignorando grupo default: {group_id}")
    except Exception as e:
        print(f"[{region}] Erro ao listar grupos: {e}")

def cleanup_keypair(ec2_client, region):
    print(f"[{region}] --- Iniciando limpeza de pares de chave EC2")

    try:
        keys = ec2_client.describe_key_pairs()
        print(f"[{region}] Encontrado {len(keys['KeyPairs'])} pares de chave")
        for key in keys['KeyPairs']:
            key_name = key['KeyName']
            try:
                ec2_client.delete_key_pair(KeyName=key_name)
                print(f"[{region}] Par de chave deletado: {key_name}")
            except Exception as e:
                print(f"[{region}] Erro ao deletar par de chave {key_name}: {e}")
    except Exception as e:
        print(f"[{region}] Erro ao listar pares de chaves: {e}")

def lambda_handler(event, context):
    target_regions_str = os.environ.get('TARGET_REGIONS', 'us-east-1,us-east-2')
    regions = [region.strip() for region in target_regions_str.split(',') if region.strip()]
    print(f"Variável TARGET_REGIONS recebida: {target_regions_str}")
    print(f"Iniciando processo de limpeza para as regiões: {regions}")

    for region in regions:
        print(f"\n================ PROCESSANDO REGIÃO: {region} ================")
        ec2_client = boto3.client('ec2', region_name=region)

        cleanup_keypair(ec2_client, region)  # agora antes
        cleanup_sg(ec2_client, region)

    result_message = f"Processo de limpeza concluído para as regiões: {regions}."
    print(f"\n{result_message}")
    return {'statusCode': 200, 'body': result_message}
