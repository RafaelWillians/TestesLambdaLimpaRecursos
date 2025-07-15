# Teste Lambda Limpa-Recursos

## Python
* [Limpa Security Groups e Keypairs](/python/sg_keypair/limpa_sg_keypair.py)
* [Limpa vários recursos](/python/limpa_tudo/limpa_tudo.py)
* [Limpa SQS e SNS](/python/sqs_sns/limpa_sqs_sns.py)
* [Limpa EventBridge](/python/eventbridge/limpa_eventbridge.py)

## TODO

Criar scripts para limpar
* EventBridge (regras primeiro, depois barramentos, exceto as de Lambdas de limpeza e exceto o barramento default)
* Elastic Beanstalk(talvez ambos ambientes e aplicacoes)
* IPs elásticos
* Buckets S3 (primeiro políticas de buckets, para entao excluir buckets)
* CloudWatch (grupos de logs exceto das Lambdas de limpeza)
* Orçamentos do Budgets (executar somente no final de cada curso)
* IAM (Políticas, Funções, talvez usuários também)


## Criado com AWS Repo Template

Repo template for use with AWS CLI, compatible with Codespaces, GitPod and DevContainer extension (for VSCode).

Template de repositório para usar com AWS CLI, compatível com Codespaces, GitPod e extensão DevContainer (para VSCode).

## Extensões
* AWS CLI
* Draw.io Integration
* Git Graph
* Git-log
* GitHub Actions
* Github Markdown Preview
* Hashicorp Terraform
* Live Server
* GitHub CLI