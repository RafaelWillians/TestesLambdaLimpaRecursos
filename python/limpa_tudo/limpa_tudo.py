import boto3
import os
import time

# Funções de limpeza para cada serviço
# Cada função usa try/except para que um erro em um serviço não pare a execução inteira


# Erro provavelmente esta na linha 167 para baixo. Se nao tiver vpcs, da return e sai e nao exclui grupos de seg.
# Considerar criar funcao apenas para excluir os sgs e criar tambem para par de chaves


def cleanup_ec2(ec2_client, region):
    print(f"[{region}] --- Iniciando limpeza de EC2 ---")
    
    # Terminar Instâncias EC2
    try:
        paginator = ec2_client.get_paginator('describe_instances')
        instance_ids = []
        for page in paginator.paginate(Filters=[{'Name': 'instance-state-name', 'Values': ['pending', 'running', 'stopping', 'stopped']}]):
            for reservation in page['Reservations']:
                for instance in reservation['Instances']:
                    instance_ids.append(instance['InstanceId'])
        
        if instance_ids:
            print(f"[{region}] Encontradas instâncias EC2 para terminar: {instance_ids}")
            ec2_client.terminate_instances(InstanceIds=instance_ids)
        else:
            print(f"[{region}] Nenhuma instância EC2 ativa encontrada.")
    except Exception as e:
        print(f"[{region}] Erro ao limpar instâncias EC2: {e}")

    # Excluir Volumes EBS não utilizados
    try:
        volumes = ec2_client.describe_volumes(Filters=[{'Name': 'status', 'Values': ['available']}])['Volumes']
        if volumes:
            for volume in volumes:
                print(f"[{region}] Excluindo volume EBS 'available': {volume['VolumeId']}")
                ec2_client.delete_volume(VolumeId=volume['VolumeId'])
        else:
            print(f"[{region}] Nenhum volume EBS 'available' encontrado.")
    except Exception as e:
        print(f"[{region}] Erro ao limpar volumes EBS: {e}")

    # Liberar Elastic IPs não associados
    try:
        addresses = ec2_client.describe_addresses()['Addresses']
        eips_to_release = [addr['AllocationId'] for addr in addresses if 'AssociationId' not in addr]
        if eips_to_release:
            for alloc_id in eips_to_release:
                print(f"[{region}] Liberando Elastic IP não associado: {alloc_id}")
                ec2_client.release_address(AllocationId=alloc_id)
        else:
            print(f"[{region}] Nenhum Elastic IP não associado encontrado.")
    except Exception as e:
        print(f"[{region}] Erro ao limpar Elastic IPs: {e}")

def cleanup_autoscaling(autoscaling_client, region):
    print(f"[{region}] --- Iniciando limpeza de Auto Scaling Groups ---")
    try:
        paginator = autoscaling_client.get_paginator('describe_auto_scaling_groups')
        for page in paginator.paginate():
            for asg in page['AutoScalingGroups']:
                asg_name = asg['AutoScalingGroupName']
                print(f"[{region}] Excluindo Auto Scaling Group: {asg_name}")
                # ForceDelete=True termina as instâncias do grupo também
                autoscaling_client.delete_auto_scaling_group(AutoScalingGroupName=asg_name, ForceDelete=True)
    except Exception as e:
        print(f"[{region}] Erro ao limpar Auto Scaling Groups: {e}")

def cleanup_elb(elbv2_client, region):
    print(f"[{region}] --- Iniciando limpeza de Load Balancers (v2) ---")
    try:
        # Excluir Load Balancers
        lbs = elbv2_client.describe_load_balancers()['LoadBalancers']
        if lbs:
            for lb in lbs:
                lb_arn = lb['LoadBalancerArn']
                print(f"[{region}] Excluindo Load Balancer: {lb_arn}")
                elbv2_client.delete_load_balancer(LoadBalancerArn=lb_arn)
        else:
            print(f"[{region}] Nenhum Load Balancer v2 encontrado.")

        # Pausa para garantir que os LBs sejam removidos antes de excluir os Target Groups
        time.sleep(15)

        # Excluir Target Groups
        tgs = elbv2_client.describe_target_groups()['TargetGroups']
        if tgs:
            for tg in tgs:
                tg_arn = tg['TargetGroupArn']
                print(f"[{region}] Excluindo Target Group: {tg_arn}")
                elbv2_client.delete_target_group(TargetGroupArn=tg_arn)
        else:
            print(f"[{region}] Nenhum Target Group encontrado.")
    except Exception as e:
        print(f"[{region}] Erro ao limpar Load Balancers/Target Groups: {e}")

def cleanup_rds(rds_client, region):
    print(f"[{region}] --- Iniciando limpeza de RDS ---")
    try:
        dbs = rds_client.describe_db_instances()['DBInstances']
        if dbs:
            for db in dbs:
                db_id = db['DBInstanceIdentifier']
                print(f"[{region}] Excluindo instância RDS: {db_id}")
                rds_client.delete_db_instance(DBInstanceIdentifier=db_id, SkipFinalSnapshot=True, DeleteAutomatedBackups=True)
        else:
            print(f"[{region}] Nenhuma instância RDS encontrada.")
    except Exception as e:
        print(f"[{region}] Erro ao limpar RDS: {e}")

def cleanup_lambda(lambda_client, region):
    print(f"[{region}] --- Iniciando limpeza de Funções Lambda ---")
    try:
        # Evitar que a própria função se delete
        self_function_name = os.environ.get('AWS_LAMBDA_FUNCTION_NAME')
        paginator = lambda_client.get_paginator('list_functions')
        for page in paginator.paginate():
            for func in page['Functions']:
                func_name = func['FunctionName']
                if func_name == self_function_name:
                    print(f"[{region}] Ignorando a própria função de limpeza: {func_name}")
                    continue
                # Checa se possui a tag RafaelInstrutor, se tiver nao exclui a Lambda
                try:
                    tags = lambda_client.list_tags(Resource=func['FunctionArn']).get('Tags', {})
                    if tags.get('Criador') == 'RafaelInstrutor':
                        print(f"[{region}] Ignorando função protegida por tag: {func_name} (Owner=Rafa)")
                        continue
                except Exception as tag_e:
                    print(f"[{region}] Erro ao obter tags da função {func_name}: {tag_e}")                

                print(f"[{region}] Excluindo função Lambda: {func_name}")
                lambda_client.delete_function(FunctionName=func_name)
    except Exception as e:
        print(f"[{region}] Erro ao limpar Funções Lambda: {e}")

def cleanup_dynamodb(dynamodb_client, region):
    print(f"[{region}] --- Iniciando limpeza de DynamoDB ---")
    try:
        paginator = dynamodb_client.get_paginator('list_tables')
        for page in paginator.paginate():
            for table_name in page['TableNames']:
                print(f"[{region}] Excluindo tabela DynamoDB: {table_name}")
                dynamodb_client.delete_table(TableName=table_name)
    except Exception as e:
        print(f"[{region}] Erro ao limpar tabelas DynamoDB: {e}")

def cleanup_vpc_components(ec2_client, region):
    print(f"[{region}] --- Iniciando limpeza de componentes de VPC (NAT Gateways, etc) ---")
    # Limpeza em ordem de dependência

    # NAT Gateways
    try:
        nats = ec2_client.describe_nat_gateways(Filters=[{'Name': 'state', 'Values': ['available', 'pending']}])['NatGateways']
        if nats:
            for nat in nats:
                print(f"[{region}] Excluindo NAT Gateway: {nat['NatGatewayId']}")
                ec2_client.delete_nat_gateway(NatGatewayId=nat['NatGatewayId'])
        else:
            print(f"[{region}] Nenhum NAT Gateway encontrado.")
    except Exception as e:
        print(f"[{region}] Erro ao limpar NAT Gateways: {e}")
    
    # Pausa para NAT GWs terminarem
    if nats:
        print(f"[{region}] Aguardando 60s para NAT Gateways serem excluídos...")
        time.sleep(60)

    # VPCs (exceto a default)
    try:
        vpcs = ec2_client.describe_vpcs(Filters=[{'Name': 'is-default', 'Values': ['false']}])['Vpcs']
        # Erro provavelmente esta aqui na linha abaixo. Se nao tiver vpcs, da return e sai e nao exclui grupos de seg.
        # Considerar criar funcao apenas para excluir os sgs e criar tambem para par de chaves
        if not vpcs:
            print(f"[{region}] Nenhuma VPC não-padrão encontrada para limpar.")
            return

        for vpc_data in vpcs:
            vpc_id = vpc_data['VpcId']
            print(f"[{region}] Iniciando limpeza profunda para VPC não-padrão: {vpc_id}")

            # Internet Gateways
            igws = ec2_client.describe_internet_gateways(Filters=[{'Name': 'attachment.vpc-id', 'Values': [vpc_id]}])['InternetGateways']
            for igw in igws:
                print(f"[{region}] Desanexando e excluindo Internet Gateway: {igw['InternetGatewayId']}")
                ec2_client.detach_internet_gateway(InternetGatewayId=igw['InternetGatewayId'], VpcId=vpc_id)
                ec2_client.delete_internet_gateway(InternetGatewayId=igw['InternetGatewayId'])

            # Subnets
            subnets = ec2_client.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])['Subnets']
            for subnet in subnets:
                print(f"[{region}] Excluindo Subnet: {subnet['SubnetId']}")
                ec2_client.delete_subnet(SubnetId=subnet['SubnetId'])
            
            # Security Groups (não-padrão)
            # sgs = ec2_client.describe_security_groups(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])['SecurityGroups']
            # for sg in sgs:
            #     if sg['GroupName'] != 'default':
            #         print(f"[{region}] Excluindo Security Group: {sg['GroupId']}")
            #         # Tentar remover regras de dependência pode ser complexo, a exclusão pode falhar se houver dependências.
            #         try:
            #             ec2_client.delete_security_group(GroupId=sg['GroupId'])
            #         except Exception as sg_e:
            #             print(f"[{region}] Falha ao excluir SG {sg['GroupId']} (pode ter dependências): {sg_e}")

            # Finalmente, a VPC
            print(f"[{region}] Tentando excluir a VPC: {vpc_id}")
            ec2_client.delete_vpc(VpcId=vpc_id)

    except Exception as e:
        print(f"[{region}] Erro ao limpar VPCs e seus componentes: {e}")

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

def lambda_handler(event, context):
    target_regions_str = os.environ.get('TARGET_REGIONS', 'us-east-1,us-east-2')
    regions = [region.strip() for region in target_regions_str.split(',') if region.strip()]

    print(f"Iniciando processo de limpeza para as regiões: {regions}")

    for region in regions:
        print(f"\n================ PROCESSANDO REGIÃO: {region} ================")
        ec2_client = boto3.client('ec2', region_name=region)
        autoscaling_client = boto3.client('autoscaling', region_name=region)
        elbv2_client = boto3.client('elbv2', region_name=region)
        rds_client = boto3.client('rds', region_name=region)
        lambda_client = boto3.client('lambda', region_name=region)
        dynamodb_client = boto3.client('dynamodb', region_name=region)

        # A ordem da limpeza é importante para resolver dependências
        cleanup_ec2(ec2_client, region)
        cleanup_autoscaling(autoscaling_client, region)
        cleanup_elb(elbv2_client, region)
        cleanup_rds(rds_client, region)
        cleanup_lambda(lambda_client, region)
        cleanup_dynamodb(dynamodb_client, region)
        # Limpeza de VPCs e componentes por último, pois dependem que outros recursos sejam removidos
        cleanup_vpc_components(ec2_client, region)
        cleanup_keypair(ec2_client, region)
        cleanup_sg(ec2_client, region)

    result_message = f"Processo de limpeza de recursos concluído para as regiões: {regions}."
    print(f"\n{result_message}")
    return {'statusCode': 200, 'body': result_message}
