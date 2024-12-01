import json
import boto3
from datetime import datetime

# Cliente de DynamoDB
dynamodb = boto3.resource('dynamodb')
program_table = dynamodb.Table('t_carrera')
tokens_table = dynamodb.Table('t_tokens_acceso')

def validate_token_admin(token):
    """
    Valida si el token es válido y si el usuario es administrador.
    """
    response = tokens_table.get_item(Key={'token': token})
    if 'Item' not in response:
        raise Exception('Token no encontrado o inválido')

    token_data = response['Item']
    expires = token_data['expires']
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if now > expires:
        raise Exception('Token expirado')

    if token_data['role'] != 'admin':
        raise Exception('Acceso no autorizado. Solo los administradores pueden realizar esta acción.')

    return token_data

def lambda_handler(event, context):
    try:
        # Obtener token del encabezado
        headers = event.get('headers', {})
        token = headers.get('Authorization')
        if not token:
            raise Exception('Token de autorización no proporcionado.')

        # Validar token de administrador
        validate_token_admin(token)

        # Parsear el cuerpo de la solicitud
        if isinstance(event['body'], str):
            body = json.loads(event['body'])
        else:
            body = event['body']

        tenant_id = body.get('tenant_id')
        program_id = body.get('program_id')

        if not all([tenant_id, program_id]):
            raise Exception('Faltan campos requeridos: tenant_id y program_id.')

        # Eliminar el programa de DynamoDB
        response = program_table.delete_item(
            Key={
                'tenant_id': tenant_id,
                'carrera_id': program_id
            }
        )

        return {
            'statusCode': 200,
            'body': {'message': 'Programa eliminado exitosamente.'}
        }

    except Exception as e:
        return {
            'statusCode': 400,
            'body': {'error': str(e)}
        }
