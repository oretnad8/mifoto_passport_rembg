# Mi Foto Carnet - Aplicación de Fotos tipo Carnet con IA

## Descripción
Aplicación profesional para preparación e impresión de fotografías tipo carnet con eliminación inteligente de fondo usando la API de PhotoRoom.

## Características principales
- ✅ Detección automática de rostros con OpenCV
- ✅ Eliminación profesional de fondo con PhotoRoom API
- ✅ Cambio de color de fondo (blanco, gris, azul, rojo)
- ✅ Múltiples tamaños internacionales de foto carnet
- ✅ Ajustes de imagen (brillo, contraste, saturación)
- ✅ Datos personales opcionales (nombre, apellido, RUT)
- ✅ Optimización automática para papel 15.2x10.2 cm
- ✅ Guías de corte para recorte preciso
- ✅ Vista previa de impresión

## Instalación

### 1. Requisitos previos
- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Ejecutar la aplicación
```bash
python main.py
```

## Uso de la aplicación

### Pestaña Edición
1. **Cargar Imagen**: Selecciona una fotografía desde tu computadora
2. **Centrar Rostro**: Detecta y centra automáticamente el rostro
3. **Seleccionar Tamaño**: Elige el formato de foto carnet deseado
4. **Cambiar Fondo**: 
   - Selecciona el color de fondo deseado
   - Presiona "Cambiar Fondo" para eliminar el fondo actual con IA
5. **Datos Personales** (opcional): 
   - Activa el switch para incluir datos
   - Ingresa nombre, apellido y RUT

### Pestaña Preparación
1. **Ajustar hoja**: Optimiza la distribución de fotos en el papel
2. **Vista previa**: Visualiza cómo quedarán las fotos en el papel
3. **Imprimir**: Envía el trabajo a la impresora seleccionada

### Pestaña Ajustes
- **Ajustes de imagen**: Modifica brillo, contraste y saturación
- **Configuración de impresión**: Selecciona impresora y activa guías de corte

## API de PhotoRoom

Esta aplicación utiliza la API de PhotoRoom para eliminación profesional de fondos.

### Configuración actual
- **API Key**: Configurada como sandbox (desarrollo)
- **Límite**: 100 llamadas por mes en modo sandbox

### Para usar tu propia API Key
1. Obtén una API key en [PhotoRoom API](https://www.photoroom.com/api)
2. Reemplaza la key en `main.py`:
```python
self.photoroom_api_key = "tu_api_key_aqui"
```

## Tamaños de foto disponibles
- Fotocarnet estándar (3x4 cm)
- Estados Unidos (5x5 cm)
- Europa (3.5x4.5 cm)
- Italia (4x4 cm)
- China (3.3x4.8 cm)
- Brasil (5x7 cm)
- Y más de 30 formatos internacionales

## Solución de problemas

### Error "Créditos de API agotados"
- La API key sandbox tiene un límite de 100 llamadas mensuales
- Considera actualizar a una cuenta de pago para más llamadas

### Error de conexión a la API
- Verifica tu conexión a internet
- Asegúrate de que la API key sea válida

### La detección de rostro no funciona
- Asegúrate de que la foto tenga buena iluminación
- El rostro debe estar claramente visible y de frente
- Evita fotos con múltiples rostros

## Estructura del proyecto
```
mi-foto-carnet/
├── main.py           # Lógica principal de la aplicación
├── main.qml          # Interfaz de usuario
├── requirements.txt  # Dependencias del proyecto
├── README.md        # Este archivo
└── logo.png         # Logo de la aplicación (opcional)
```

## Tecnologías utilizadas
- **PyQt6**: Framework de interfaz gráfica
- **OpenCV**: Procesamiento de imágenes y detección de rostros
- **PhotoRoom API**: Eliminación inteligente de fondos
- **NumPy**: Manipulación de arrays de imágenes
- **Pillow**: Procesamiento adicional de imágenes

## Notas sobre impresión
- Optimizado para papel fotográfico de 15.2x10.2 cm (6x4 pulgadas)
- Resolución de impresión: 300 DPI
- Compatible con impresoras DNP DS620A y Mitsubishi CP-K60
- Máximo 8 copias por hoja (dependiendo del tamaño)

## Licencia
Proyecto de uso personal/educativo. La API de PhotoRoom requiere licencia propia.

## Soporte
Para problemas o sugerencias, verifica que todas las dependencias estén correctamente instaladas y que la API key de PhotoRoom sea válida.