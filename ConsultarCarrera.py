import json
import boto3
from datetime import datetime
import decimal

# Cliente de DynamoDB
dynamodb = boto3.resource('dynamodb')
program_table = dynamodb.Table('t_carrera')
tokens_table = dynamodb.Table('t_tokens_acceso')

def validate_token(token):
    """
    Valida si el token es válido.
    """
    response = tokens_table.get_item(Key={'token': token})
    if 'Item' not in response:
        raise Exception('Token no encontrado o inválido')

    token_data = response['Item']
    expires = token_data['expires']
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if now > expires:
        raise Exception('Token expirado')

    return token_data

def decimal_to_float(obj):
    """
    Convierte objetos Decimal a float para ser serializables en JSON.
    """
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    raise TypeError("Object of type %s is not JSON serializable" % type(obj).__name__)

def lambda_handler(event, context):
    try:
        # Obtener token del encabezado
        headers = event.get('headers', {})
        token = headers.get('Authorization')
        if not token:
            raise Exception('Token de autorización no proporcionado.')

        # Validar token
        validate_token(token)

        # Obtener datos del cuerpo de la solicitud
        if isinstance(event['body'], str):
            body = json.loads(event['body'])  # Decodificar JSON en diccionario
        else:
            body = event['body']

        tenant_id = body.get('tenant_id')
        program_id = body.get('program_id')

        if not all([tenant_id, program_id]):
            raise Exception('Faltan parámetros requeridos: tenant_id y program_id.')

        # Consultar el programa en DynamoDB
        response = program_table.get_item(
            Key={
                'tenant_id': tenant_id,
                'carrera_id': program_id
            }
        )

        if 'Item' not in response:
            raise Exception('Programa no encontrado.')

        # Convertir la respuesta a un formato serializable
        program_data = response['Item']

        return {
            'statusCode': 200,
            'body': program_data
        }

    except Exception as e:
        return {
            'statusCode': 400,
            'body': {'error': str(e)}
        }
