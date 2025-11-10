"""
Script de prueba para verificar que la API de PhotoRoom funciona correctamente
"""

import requests
import json
import os
from PIL import Image
import io

def test_photoroom_api():
    """Prueba la conexión y funcionamiento de la API de PhotoRoom"""
    
    # Cargar configuración
    config_path = "config.json"
    
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
            api_key = config.get("photoroom_api", {}).get("api_key")
            api_url = config.get("photoroom_api", {}).get("api_url", "https://sdk.photoroom.com/v1/segment")
    else:
        print("❌ No se encontró config.json")
        api_key = input("Ingresa tu API key de PhotoRoom: ")
        api_url = "https://sdk.photoroom.com/v1/segment"
    
    print("\n=== Prueba de API de PhotoRoom ===")
    print(f"API URL: {api_url}")
    print(f"API Key: {api_key[:20]}..." if len(api_key) > 20 else f"API Key: {api_key}")
    
    # Crear una imagen de prueba simple (un cuadrado rojo sobre fondo blanco)
    print("\n📸 Creando imagen de prueba...")
    test_image = Image.new('RGB', (200, 200), color='white')
    pixels = test_image.load()
    # Dibujar un cuadrado rojo en el centro
    for i in range(50, 150):
        for j in range(50, 150):
            pixels[i, j] = (255, 0, 0)
    
    # Guardar temporalmente
    test_image_path = "test_image.jpg"
    test_image.save(test_image_path)
    print("✅ Imagen de prueba creada")
    
    # Preparar la solicitud
    print("\n🌐 Enviando solicitud a PhotoRoom API...")
    
    headers = {
        "x-api-key": api_key
    }
    
    with open(test_image_path, 'rb') as f:
        files = {
            'image_file': ('test.jpg', f, 'image/jpeg')
        }
        
        try:
            response = requests.post(api_url, headers=headers, files=files)
            
            print(f"\n📊 Código de respuesta: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ ¡API funcionando correctamente!")
                
                # Guardar la imagen resultante
                result_image = Image.open(io.BytesIO(response.content))
                result_image.save("test_result.png")
                print("✅ Imagen procesada guardada como 'test_result.png'")
                
                # Verificar si tiene canal alpha (transparencia)
                if result_image.mode == 'RGBA':
                    print("✅ La imagen tiene canal alpha (transparencia)")
                else:
                    print("⚠️ La imagen no tiene canal alpha")
                
            elif response.status_code == 402:
                print("❌ Error: Créditos de API agotados")
                print("   Solución: Verifica tu plan o espera al siguiente ciclo de facturación")
                
            elif response.status_code == 429:
                print("❌ Error: Límite de tasa excedido")
                print("   Solución: Espera un momento antes de intentar de nuevo")
                
            elif response.status_code == 401:
                print("❌ Error: API key inválida")
                print("   Solución: Verifica que tu API key sea correcta")
                
            else:
                print(f"❌ Error desconocido: {response.status_code}")
                print(f"   Detalles: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("❌ Error de conexión")
            print("   Verifica tu conexión a internet")
            
        except Exception as e:
            print(f"❌ Error inesperado: {str(e)}")
    
    # Limpiar archivo temporal
    if os.path.exists(test_image_path):
        os.remove(test_image_path)
        print("\n🧹 Archivo temporal eliminado")
    
    print("\n=== Prueba completada ===")

if __name__ == "__main__":
    test_photoroom_api()