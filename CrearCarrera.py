import json
import boto3
from datetime import datetime

# Cliente de DynamoDB
dynamodb = boto3.resource('dynamodb')
program_table = dynamodb.Table('t_carrera')  # Tabla para carreras
tokens_table = dynamodb.Table('t_tokens_acceso')  # Tabla para validación de tokens

def validate_token(token):
    """
    Valida el token enviado en la solicitud.
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
        raise Exception('Acceso no autorizado. Solo los administradores pueden crear programas.')

    return token_data

def lambda_handler(event, context):
    try:
        # Obtener token del encabezado
        headers = event.get('headers', {})
        token = headers.get('Authorization')
        if not token:
            raise Exception('Token de autorización no proporcionado.')

        # Validar token
        validate_token(token)

        # Procesar cuerpo de la solicitud
        if isinstance(event['body'], str):
            body = json.loads(event['body'])
        else:
            body = event['body']

        tenant_id = body.get('tenant_id')
        program_id = body.get('program_id')
        program_name = body.get('program_name')
        credits_required = body.get('credits_required')
        courses_by_level = body.get('courses_by_level')

        if not all([tenant_id, program_id, program_name, credits_required, courses_by_level]):
            raise Exception('Faltan campos requeridos en el cuerpo de la solicitud.')

        # Crear entrada para DynamoDB
        program_data = {
            'tenant_id': tenant_id,
            'carrera_id': program_id,
            'program_name': program_name,
            'credits_required': credits_required,
            'courses_by_level': courses_by_level,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }

        # Guardar en DynamoDB
        program_table.put_item(Item=program_data)

        # Respuesta exitosa
        return {
            'statusCode': 200,
            'body': {
                'message': 'Programa creado exitosamente.',
                'program_id': program_id
            }
        }

    except Exception as e:
        return {
            'statusCode': 400,
            'body': {'error': str(e)}
        }
