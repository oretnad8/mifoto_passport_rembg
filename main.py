"""
Mi Foto Carnet - Aplicación para preparación e impresión de fotos tipo carnet
Versión 1.2 - Con PhotoRoom API para remoción de fondo

Dependencias requeridas:
pip install PyQt6 opencv-python numpy requests pillow

PhotoRoom API se usa para eliminación precisa del fondo.
La configuración se carga desde config.json (se crea automáticamente si no existe).
"""

import sys
import os
import io
import base64
import json
import requests
from PyQt6.QtCore import QUrl, QObject, pyqtSlot, QSize, pyqtProperty, QRect, pyqtSignal, Qt, QSizeF
from PyQt6.QtGui import QGuiApplication, QImage, QPainter, QPageSize, QPageLayout, QTransform, QPen, QColor
from PyQt6.QtQml import QQmlApplicationEngine
from PyQt6.QtQuick import QQuickImageProvider
from PyQt6.QtPrintSupport import QPrinter, QPrinterInfo
import cv2
import numpy as np
from PIL import Image

class ImageProcessor(QObject):
    nameChanged = pyqtSignal()
    lastnameChanged = pyqtSignal()
    rutChanged = pyqtSignal()
    imageChanged = pyqtSignal()
    isCenteredChanged = pyqtSignal()
    printLayoutChanged = pyqtSignal()
    brightnessChanged = pyqtSignal()
    contrastChanged = pyqtSignal()
    saturationChanged = pyqtSignal()
    showCutGuidesChanged = pyqtSignal()
    backgroundColorChanged = pyqtSignal()
    processingStatusChanged = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.image = None
        self.original_image = None
        self.centered_image = None
        self.centered_original = None  # Para guardar la imagen centrada sin ajustes
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        self._name = ""
        self._lastname = ""
        self._rut = ""
        self._isCentered = False
        self.current_printer = None
        self.print_layout = []
        self.current_photo_size = None
        self._brightness = 0
        self._contrast = 0
        self._saturation = 0
        self._showCutGuides = False
        self._backgroundColor = "#FFFFFF"
        self.background_removed_image = None
        self.mask = None
        
        # Cargar configuración
        self.load_config()

    def load_config(self):
        """Carga la configuración desde config.json"""
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        
        # Configuración por defecto
        default_config = {
            "photoroom_api": {
                "api_key": "sandbox_sk_pr_default_17cd6ae01b3ecf6d6118892628decb627d2e65a4",
                "api_url": "https://sdk.photoroom.com/v1/segment"
            },
            "app_settings": {
                "default_dpi": 300,
                "paper_width_mm": 152,
                "paper_height_mm": 102,
                "margin_safety_mm": 5,
                "margin_between_photos_mm": 2,
                "max_photos_per_sheet": 8
            }
        }
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    self.photoroom_api_key = config.get("photoroom_api", {}).get("api_key", default_config["photoroom_api"]["api_key"])
                    self.photoroom_api_url = config.get("photoroom_api", {}).get("api_url", default_config["photoroom_api"]["api_url"])
                    self.app_settings = config.get("app_settings", default_config["app_settings"])
                    print(f"Configuración cargada desde {config_path}")
                    print(f"Modo API: {config.get('photoroom_api', {}).get('mode', 'sandbox')}")
            else:
                # Usar configuración por defecto
                self.photoroom_api_key = default_config["photoroom_api"]["api_key"]
                self.photoroom_api_url = default_config["photoroom_api"]["api_url"]
                self.app_settings = default_config["app_settings"]
                print("Usando configuración por defecto (archivo config.json no encontrado)")
                
                # Crear archivo de configuración por defecto
                with open(config_path, 'w') as f:
                    json.dump({
                        "photoroom_api": {
                            "api_key": self.photoroom_api_key,
                            "api_url": self.photoroom_api_url,
                            "mode": "sandbox",
                            "comment": "Para producción, cambia 'mode' a 'production' y actualiza la 'api_key'"
                        },
                        "app_settings": self.app_settings,
                        "image_processing": {
                            "face_detection_scale_factor": 1.1,
                            "face_detection_min_neighbors": 5,
                            "face_detection_min_size": [30, 30],
                            "face_crop_multiplier": 2.2
                        }
                    }, f, indent=2)
                    print(f"Archivo de configuración creado en {config_path}")
                    
        except Exception as e:
            print(f"Error al cargar configuración: {str(e)}")
            # Usar valores por defecto en caso de error
            self.photoroom_api_key = default_config["photoroom_api"]["api_key"]
            self.photoroom_api_url = default_config["photoroom_api"]["api_url"]
            self.app_settings = default_config["app_settings"]

    @pyqtSlot(str, result=bool)
    def loadImage(self, file_url):
        file_path = QUrl(file_url).toLocalFile()
        self.original_image = cv2.imread(file_path)
        self.image = self.original_image.copy()
        self.imageChanged.emit()
        self._isCentered = False
        self.isCenteredChanged.emit()
        self.background_removed_image = None
        self.mask = None
        # Resetear ajustes de imagen cuando se carga una nueva
        self._brightness = 0
        self._contrast = 0
        self._saturation = 0
        return self.image is not None

    def detect_face(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Intentar con diferentes clasificadores en orden de precisión
        faces = self.face_cascade.detectMultiScale(
            gray, 
            scaleFactor=1.3,  # Aumentar para ser más estricto
            minNeighbors=6,   # Aumentar para reducir falsos positivos
            minSize=(50, 50)  # Aumentar tamaño mínimo
        )
        
        if len(faces) == 0:
            # Segundo intento más permisivo
            faces = self.face_cascade.detectMultiScale(
                gray, 
                scaleFactor=1.1,
                minNeighbors=4,
                minSize=(40, 40)
            )
        
        # Filtrar por proporción (los rostros suelen ser más altos que anchos)
        valid_faces = []
        for (x, y, w, h) in faces:
            aspect_ratio = h / w
            if 0.8 < aspect_ratio < 1.8:  # Rostros tienen proporción cercana a 1:1.3
                valid_faces.append((x, y, w, h))
        
        return valid_faces if valid_faces else faces

    @pyqtSlot(float, float, float, float, result=bool)
    def centerFace(self, target_width, target_height, canvas_width, canvas_height):
        if self.original_image is None:
            return False

        image = self.original_image.copy()
        height, width = image.shape[:2]

        faces = self.detect_face(image)

        if len(faces) == 0:
            return False

        (x, y, w, h) = faces[0]
        face_center_x = x + w // 2
        face_center_y = y + h // 2

        face_height = int(h * 2.2)
        face_width = int(face_height * (target_width / target_height))

        top = max(0, face_center_y - face_height // 2)
        bottom = min(height, face_center_y + face_height // 2)
        left = max(0, face_center_x - face_width // 2)
        right = min(width, face_center_x + face_width // 2)

        if top == 0:
            bottom = face_height
        elif bottom == height:
            top = height - face_height

        if left == 0:
            right = face_width
        elif right == width:
            left = width - face_width

        cropped_image = image[top:bottom, left:right]

        canvas_aspect_ratio = canvas_width / canvas_height
        img_aspect_ratio = cropped_image.shape[1] / cropped_image.shape[0]

        if canvas_aspect_ratio > img_aspect_ratio:
            new_height = int(canvas_height)
            new_width = int(new_height * img_aspect_ratio)
        else:
            new_width = int(canvas_width)
            new_height = int(new_width / img_aspect_ratio)

        self.centered_image = cv2.resize(cropped_image, (new_width, new_height), interpolation=cv2.INTER_AREA)
        self.centered_original = self.centered_image.copy()  # Guardar copia sin ajustes
        self.image = self.centered_image.copy()
        self.imageChanged.emit()
        self._isCentered = True
        self.isCenteredChanged.emit()
        self.background_removed_image = None
        self.mask = None
        return True
    
    @pyqtSlot(result=bool)
    def removeBackgroundWithPhotoRoom(self):
        """Elimina el fondo usando la API de PhotoRoom"""
        if self.centered_original is None or not self._isCentered:
            print("No hay imagen centrada para procesar")
            self.processingStatusChanged.emit("No hay imagen centrada para procesar")
            return False

        try:
            self.processingStatusChanged.emit("Procesando imagen con PhotoRoom...")
            
            # Convertir la imagen OpenCV a bytes
            image = self.centered_original.copy()
            _, buffer = cv2.imencode('.jpg', image)
            image_bytes = buffer.tobytes()
            
            # Preparar la solicitud a la API de PhotoRoom
            url = self.photoroom_api_url
            headers = {
                "x-api-key": self.photoroom_api_key
            }
            
            files = {
                'image_file': ('image.jpg', image_bytes, 'image/jpeg')
            }
            
            # Hacer la solicitud a la API
            print("Enviando imagen a PhotoRoom API...")
            response = requests.post(url, headers=headers, files=files)
            
            if response.status_code == 200:
                # La respuesta es una imagen PNG con transparencia
                response_image = Image.open(io.BytesIO(response.content))
                
                # Convertir PIL Image a numpy array
                response_array = np.array(response_image)
                
                # Verificar si la imagen tiene canal alpha
                if response_array.shape[2] == 4:
                    # Extraer el canal alpha como máscara
                    alpha_channel = response_array[:, :, 3]
                    
                    # Extraer los canales RGB
                    rgb_image = response_array[:, :, :3]
                    
                    # Convertir RGB a BGR para OpenCV
                    bgr_image = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2BGR)
                    
                    # Crear máscara binaria desde el canal alpha
                    # Normalizar alpha a rango 0-1 para usar como máscara de mezcla
                    self.mask = alpha_channel.astype(np.float32) / 255.0
                    
                    # Crear imagen con fondo transparente (donde alpha = 0, poner negro)
                    self.background_removed_image = bgr_image.copy()
                    
                    # Donde el alpha es 0 (fondo), poner píxeles en negro
                    mask_3channel = np.stack([alpha_channel, alpha_channel, alpha_channel], axis=-1)
                    self.background_removed_image = np.where(mask_3channel > 0, bgr_image, 0).astype(np.uint8)
                    
                    # Aplicar el color de fondo seleccionado
                    self.applyBackgroundColor()
                    
                    print("Fondo eliminado exitosamente con PhotoRoom")
                    self.processingStatusChanged.emit("Fondo eliminado exitosamente")
                    return True
                else:
                    print("La imagen devuelta no tiene canal alpha")
                    self.processingStatusChanged.emit("Error: imagen sin transparencia")
                    return False
                    
            elif response.status_code == 402:
                print("Error: Créditos de API agotados")
                self.processingStatusChanged.emit("Error: Créditos de API agotados")
                return False
            elif response.status_code == 429:
                print("Error: Límite de tasa excedido")
                self.processingStatusChanged.emit("Error: Límite de tasa excedido. Intente más tarde")
                return False
            else:
                print(f"Error en la API: {response.status_code} - {response.text}")
                self.processingStatusChanged.emit(f"Error en la API: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"Error de red: {str(e)}")
            self.processingStatusChanged.emit(f"Error de conexión: {str(e)}")
            return False
        except Exception as e:
            print(f"Error inesperado: {str(e)}")
            self.processingStatusChanged.emit(f"Error inesperado: {str(e)}")
            return False

    def applyBackgroundColor(self):
        """Aplica el color de fondo seleccionado a la imagen sin fondo"""
        if self.background_removed_image is None or self.mask is None:
            return
        
        # Convertir color hex a BGR
        hex_color = self._backgroundColor.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        bgr_color = (rgb[2], rgb[1], rgb[0])  # Convertir RGB a BGR para OpenCV
        
        # Crear imagen con el nuevo fondo
        result = np.full_like(self.background_removed_image, bgr_color)
        
        # La máscara es de punto flotante (0-1) desde PhotoRoom
        if self.mask.dtype == np.float32 or self.mask.dtype == np.float64:
            # Expandir la máscara a 3 canales
            mask_3channel = np.stack([self.mask, self.mask, self.mask], axis=-1)
            
            # Mezclar suavemente usando la máscara como alpha
            result = (self.background_removed_image * mask_3channel + 
                     result * (1 - mask_3channel)).astype(np.uint8)
        else:
            # Para máscaras binarias (compatibilidad)
            mask_3channel = np.stack([self.mask, self.mask, self.mask], axis=-1)
            result = np.where(mask_3channel > 0, self.background_removed_image, result)
        
        # Actualizar la imagen centrada
        self.centered_image = result
        
        # Aplicar ajustes de brillo, contraste y saturación
        self.applyImageAdjustments()

    @pyqtSlot()
    def applyImageAdjustments(self):
        """Aplica los ajustes de brillo, contraste y saturación"""
        if self.centered_image is None:
            return
        
        image = self.centered_image.copy()
        
        # Aplicar brillo y contraste
        # brightness: -100 to 100
        # contrast: -100 to 100
        brightness = self._brightness
        contrast = self._contrast / 100.0
        
        # Ajustar brillo y contraste
        if brightness != 0 or contrast != 0:
            image = cv2.convertScaleAbs(image, alpha=1 + contrast, beta=brightness)
        
        # Aplicar saturación
        if self._saturation != 0:
            # Convertir a HSV
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV).astype(np.float32)
            
            # Ajustar saturación
            saturation_scale = 1 + (self._saturation / 100.0)
            hsv[:, :, 1] = np.clip(hsv[:, :, 1] * saturation_scale, 0, 255)
            
            # Convertir de vuelta a BGR
            image = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
        
        self.image = image
        self.imageChanged.emit()

    @pyqtSlot(bool, float)
    def adjustImageForPersonalData(self, show_data, overlay_height_ratio):
        if self.centered_image is None or not self._isCentered:
            return

        # Primero aplicar los ajustes de imagen
        self.applyImageAdjustments()

        if show_data:
            shift = int(self.image.shape[0] * overlay_height_ratio / 3.44)
            black_image = np.zeros_like(self.image)
            black_image[:-shift, :] = self.image[shift:, :]
            self.image = black_image

        self.imageChanged.emit()

    @pyqtSlot(float, float, result=bool)
    def adjustPrintLayout(self, canvas_width, canvas_height):
        if self.image is None or not self._isCentered or not self.current_photo_size:
            print("No se puede ajustar: imagen no centrada o tamaño no seleccionado")
            return False

        # Dimensiones del papel en milímetros (15.2 x 10.2 cm)
        PAPER_WIDTH_MM = self.app_settings.get("paper_width_mm", 152)
        PAPER_HEIGHT_MM = self.app_settings.get("paper_height_mm", 102)

        # MÁRGENES DE SEGURIDAD PARA LA IMPRESORA (5mm en cada borde)
        MARGIN_SAFETY_MM = self.app_settings.get("margin_safety_mm", 5)
        
        # Área útil del papel considerando márgenes de seguridad
        USABLE_WIDTH_MM = PAPER_WIDTH_MM - (2 * MARGIN_SAFETY_MM)  # 142 mm
        USABLE_HEIGHT_MM = PAPER_HEIGHT_MM - (2 * MARGIN_SAFETY_MM)  # 92 mm

        # Convertir mm a píxeles para 300 DPI
        DPI = self.app_settings.get("default_dpi", 300)
        MM_TO_PX = DPI / 25.4

        # Calcular dimensiones del papel en píxeles
        paper_width_px = PAPER_WIDTH_MM * MM_TO_PX
        paper_height_px = PAPER_HEIGHT_MM * MM_TO_PX

        # Obtener dimensiones de la foto seleccionada en cm y convertir a mm
        photo_width_cm, photo_height_cm = self.current_photo_size
        photo_width_mm = photo_width_cm * 10
        photo_height_mm = photo_height_cm * 10

        # Convertir dimensiones de la foto a píxeles
        photo_width_px = photo_width_mm * MM_TO_PX
        photo_height_px = photo_height_mm * MM_TO_PX

        # Margen entre fotos en mm
        MARGIN_MM = self.app_settings.get("margin_between_photos_mm", 2)
        margin_px = MARGIN_MM * MM_TO_PX

        # Calcular cuántas fotos caben teóricamente en el área útil
        num_cols = int((USABLE_WIDTH_MM + MARGIN_MM) / (photo_width_mm + MARGIN_MM))
        total_width_needed = (num_cols * photo_width_mm) + ((num_cols - 1) * MARGIN_MM)
        if total_width_needed > USABLE_WIDTH_MM:
            num_cols -= 1
        
        num_rows = int((USABLE_HEIGHT_MM + MARGIN_MM) / (photo_height_mm + MARGIN_MM))
        total_height_needed = (num_rows * photo_height_mm) + ((num_rows - 1) * MARGIN_MM)
        if total_height_needed > USABLE_HEIGHT_MM:
            num_rows -= 1

        # RESTRICCIONES ESPECIALES
        # Para fotos de 5x5 cm o más grandes: máximo 2 copias
        if photo_width_cm >= 5.0 or photo_height_cm >= 5.0:
            if photo_width_cm >= photo_height_cm:
                # Foto más ancha, poner 2 en horizontal
                num_cols = min(num_cols, 2)
                num_rows = min(num_rows, 1)
            else:
                # Foto más alta, poner 2 en vertical
                num_cols = min(num_cols, 1)
                num_rows = min(num_rows, 2)
        
        # Para fotos de 6x9 cm: solo 1 copia
        if photo_width_cm >= 6.0 or photo_height_cm >= 9.0:
            num_cols = 1
            num_rows = 1
        
        # LÍMITE MÁXIMO: configurado en app_settings
        MAX_PHOTOS = self.app_settings.get("max_photos_per_sheet", 8)
        total_photos = num_cols * num_rows
        if total_photos > MAX_PHOTOS:
            # Ajustar para no exceder el máximo de fotos
            if num_cols > 4:
                num_cols = 4
                num_rows = min(2, MAX_PHOTOS // 4)
            elif num_rows > 4:
                num_rows = 4
                num_cols = min(2, MAX_PHOTOS // 4)
            else:
                # Buscar la mejor distribución para el máximo de fotos
                if num_cols * num_rows > MAX_PHOTOS:
                    if num_cols >= num_rows:
                        num_cols = min(4, MAX_PHOTOS // 2)
                        num_rows = min(2, MAX_PHOTOS // num_cols)
                    else:
                        num_cols = min(2, MAX_PHOTOS // 4)
                        num_rows = min(4, MAX_PHOTOS // num_cols)

        print(f"=== Configuración de impresión ===")
        print(f"Papel: {PAPER_WIDTH_MM}x{PAPER_HEIGHT_MM}mm (15.2x10.2 cm)")
        print(f"Área útil: {USABLE_WIDTH_MM}x{USABLE_HEIGHT_MM}mm (con márgenes de seguridad)")
        print(f"Foto seleccionada: {photo_width_mm:.1f}x{photo_height_mm:.1f}mm ({photo_width_cm}x{photo_height_cm} cm)")
        print(f"Distribución: {num_cols} columnas x {num_rows} filas = {num_cols * num_rows} fotos")

        if num_cols == 0 or num_rows == 0:
            print("Error: La foto es demasiado grande para el papel")
            return False

        # Calcular el espacio total ocupado por las fotos
        total_width_mm = (photo_width_mm * num_cols) + (MARGIN_MM * (num_cols - 1))
        total_height_mm = (photo_height_mm * num_rows) + (MARGIN_MM * (num_rows - 1))

        # Convertir a píxeles
        total_width_px = total_width_mm * MM_TO_PX
        total_height_px = total_height_mm * MM_TO_PX

        # Centrar el bloque de fotos en el papel (considerando toda el área, no solo el área útil)
        start_x_mm = (PAPER_WIDTH_MM - total_width_mm) / 2
        start_y_mm = (PAPER_HEIGHT_MM - total_height_mm) / 2
        
        start_x_px = start_x_mm * MM_TO_PX
        start_y_px = start_y_mm * MM_TO_PX

        # Crear el layout de las fotos
        self.print_layout = []
        for row in range(num_rows):
            for col in range(num_cols):
                # Posición en mm
                x_mm = start_x_mm + (col * (photo_width_mm + MARGIN_MM))
                y_mm = start_y_mm + (row * (photo_height_mm + MARGIN_MM))
                
                # Posición en píxeles
                x_px = x_mm * MM_TO_PX
                y_px = y_mm * MM_TO_PX

                # Guardar las posiciones y dimensiones
                self.print_layout.append({
                    "x": x_px,
                    "y": y_px,
                    "width": photo_width_px,
                    "height": photo_height_px,
                    # Valores para el canvas de visualización (en mm)
                    "x_canvas": x_mm,
                    "y_canvas": y_mm,
                    "width_canvas": photo_width_mm,
                    "height_canvas": photo_height_mm
                })

        print(f"Layout creado exitosamente con {len(self.print_layout)} fotos")
        print(f"Posición inicial: {start_x_mm:.1f}, {start_y_mm:.1f} mm")
        self.printLayoutChanged.emit()
        return True

    @pyqtSlot()
    def clearLayout(self):
        """Limpia el layout de impresión actual"""
        self.print_layout = []
        self.printLayoutChanged.emit()

    @pyqtSlot(str, result=bool)
    def setCurrent_photo_size(self, size_str):
        try:
            # Extraer las dimensiones del string
            parts = size_str.split(' - ')
            if len(parts) == 2:
                dimensions = parts[1].replace('cm', '').strip().split('x')
            else:
                # Para los tamaños sin nombre (que empiezan con " - ")
                dimensions = size_str.replace(' - ', '').replace('cm', '').strip().split('x')
            
            width = float(dimensions[0])
            height = float(dimensions[1])
            
            # Si el tamaño cambió, limpiar el layout
            if self.current_photo_size and (self.current_photo_size[0] != width or self.current_photo_size[1] != height):
                self.print_layout = []
                self.printLayoutChanged.emit()
            
            self.current_photo_size = [width, height]
            print(f"Tamaño de foto establecido: {width}x{height} cm")
            return True
        except Exception as e:
            print(f"Error al parsear tamaño: {str(e)}")
            return False

    @pyqtProperty("QVariantList", notify=printLayoutChanged)
    def layout(self):
        return self.print_layout

    @pyqtSlot(result=list)
    def getPrinters(self):
        return [printer.printerName() for printer in QPrinterInfo.availablePrinters()]

    @pyqtSlot(int)
    def setCurrentPrinter(self, index):
        printers = QPrinterInfo.availablePrinters()
        if 0 <= index < len(printers):
            self.current_printer = printers[index]

    @pyqtSlot()
    def printImage(self):
        if self.image is None or self.current_printer is None or not self.print_layout:
            print("No se puede imprimir: falta imagen, impresora o layout")
            return

        printer = QPrinter(self.current_printer)
        printer.setResolution(self.app_settings.get("default_dpi", 300))  # DPI desde configuración
        printer.setFullPage(True)
        
        # Obtener el nombre de la impresora para aplicar configuración específica
        printer_name = self.current_printer.printerName().lower()
        print(f"Imprimiendo en: {self.current_printer.printerName()}")
        
        # Configurar tamaño de página
        if "dnp" in printer_name or "ds620" in printer_name or "dp-ds620" in printer_name:
            page_size = QPageSize(QSizeF(4.0, 6.0), QPageSize.Unit.Inch)
            printer.setFullPage(True)
            printer.setPageOrientation(QPageLayout.Orientation.Portrait)
            print("Configuración DNP DS620A: 4x6 pulgadas (Portrait)")
        elif "mitsubishi" in printer_name or "cp-k60" in printer_name or "k60" in printer_name:
            page_size = QPageSize(QSizeF(152.0, 102.0), QPageSize.Unit.Millimeter)
            printer.setPageSize(page_size)
            printer.setPageOrientation(QPageLayout.Orientation.Landscape)
            print("Configuración Mitsubishi: 152x102 mm (Landscape)")
        else:
            page_size = QPageSize(QSizeF(152.0, 102.0), QPageSize.Unit.Millimeter)
            printer.setPageSize(page_size)
            printer.setPageOrientation(QPageLayout.Orientation.Landscape)
            print("Configuración genérica: 152x102 mm (Landscape)")
        
        # Obtener el tamaño real del área de impresión en píxeles
        page_rect = printer.pageRect(QPrinter.Unit.DevicePixel)
        print(f"Área de impresión: {page_rect.width()}x{page_rect.height()} píxeles")

        painter = QPainter()
        if not painter.begin(printer):
            print("Error al iniciar la impresión")
            return

        # Convertir imagen OpenCV a QImage
        qimage = self.cv_to_qimage(self.image)

        # Dibujar guías de corte si están habilitadas
        if self._showCutGuides:
            pen = QPen(QColor(0, 0, 0), 1)  # Línea negra fina
            painter.setPen(pen)
            
            for layout in self.print_layout:
                # Guías de corte en las esquinas
                guide_length = 10  # Longitud de las guías en píxeles
                
                x = int(layout["x"])
                y = int(layout["y"])
                w = int(layout["width"])
                h = int(layout["height"])
                
                # Esquina superior izquierda
                painter.drawLine(x - guide_length, y, x + guide_length, y)
                painter.drawLine(x, y - guide_length, x, y + guide_length)
                
                # Esquina superior derecha
                painter.drawLine(x + w - guide_length, y, x + w + guide_length, y)
                painter.drawLine(x + w, y - guide_length, x + w, y + guide_length)
                
                # Esquina inferior izquierda
                painter.drawLine(x - guide_length, y + h, x + guide_length, y + h)
                painter.drawLine(x, y + h - guide_length, x, y + h + guide_length)
                
                # Esquina inferior derecha
                painter.drawLine(x + w - guide_length, y + h, x + w + guide_length, y + h)
                painter.drawLine(x + w, y + h - guide_length, x + w, y + h + guide_length)

        # Dibujar cada foto en su posición
        for layout in self.print_layout:
            target_rect = QRect(
                int(layout["x"]), 
                int(layout["y"]), 
                int(layout["width"]), 
                int(layout["height"])
            )
            
            # Dibujar la imagen escalada al tamaño correcto
            painter.drawImage(target_rect, qimage)
            
            # Si hay datos personales, agregar el recuadro negro con texto
            if self._name or self._lastname or self._rut:
                text_height = layout["height"] / 5
                text_rect = QRect(
                    int(layout["x"]),
                    int(layout["y"] + layout["height"] - text_height),
                    int(layout["width"]),
                    int(text_height)
                )
                
                # Dibujar recuadro negro
                painter.fillRect(text_rect, Qt.GlobalColor.black)
                
                # Configurar texto blanco
                painter.setPen(Qt.GlobalColor.white)
                font = painter.font()
                font.setPixelSize(int(text_height / 3.5))
                font.setFamily("Arial")
                font.setBold(True)
                font.setWeight(800)
                painter.setFont(font)
                
                # Calcular posiciones del texto
                text_margin = text_height / 8
                line_height = (text_height - text_margin) / 3
                base_y = int(layout["y"] + layout["height"] - text_height + text_margin / 2)
                
                # Dibujar cada línea de texto
                if self._name:
                    painter.drawText(
                        QRect(
                            int(layout["x"]),
                            base_y,
                            int(layout["width"]),
                            int(line_height)
                        ),
                        Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
                        self._name
                    )
                
                if self._lastname:
                    painter.drawText(
                        QRect(
                            int(layout["x"]),
                            base_y + int(line_height),
                            int(layout["width"]),
                            int(line_height)
                        ),
                        Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
                        self._lastname
                    )
                
                if self._rut:
                    painter.drawText(
                        QRect(
                            int(layout["x"]),
                            base_y + int(2 * line_height),
                            int(layout["width"]),
                            int(line_height)
                        ),
                        Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
                        self._rut
                    )

        painter.end()
        print("Impresión enviada a la cola de impresión")

    def cv_to_qimage(self, cv_img):
        height, width, channel = cv_img.shape
        bytes_per_line = 3 * width
        return QImage(cv_img.data, width, height, bytes_per_line, QImage.Format.Format_RGB888).rgbSwapped()

    # Propiedades existentes
    @pyqtProperty(str, notify=nameChanged)
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if self._name != value:
            self._name = value
            self.nameChanged.emit()

    @pyqtProperty(str, notify=lastnameChanged)
    def lastname(self):
        return self._lastname

    @lastname.setter
    def lastname(self, value):
        if self._lastname != value:
            self._lastname = value
            self.lastnameChanged.emit()

    @pyqtProperty(str, notify=rutChanged)
    def rut(self):
        return self._rut

    @rut.setter
    def rut(self, value):
        if self._rut != value:
            self._rut = value
            self.rutChanged.emit()

    @pyqtProperty(bool, notify=isCenteredChanged)
    def isCentered(self):
        return self._isCentered

    # Nuevas propiedades para ajustes de imagen
    @pyqtProperty(float, notify=brightnessChanged)
    def brightness(self):
        return self._brightness

    @brightness.setter
    def brightness(self, value):
        if self._brightness != value:
            self._brightness = value
            self.brightnessChanged.emit()

    @pyqtProperty(float, notify=contrastChanged)
    def contrast(self):
        return self._contrast

    @contrast.setter
    def contrast(self, value):
        if self._contrast != value:
            self._contrast = value
            self.contrastChanged.emit()

    @pyqtProperty(float, notify=saturationChanged)
    def saturation(self):
        return self._saturation

    @saturation.setter
    def saturation(self, value):
        if self._saturation != value:
            self._saturation = value
            self.saturationChanged.emit()

    @pyqtProperty(bool, notify=showCutGuidesChanged)
    def showCutGuides(self):
        return self._showCutGuides

    @showCutGuides.setter
    def showCutGuides(self, value):
        if self._showCutGuides != value:
            self._showCutGuides = value
            self.showCutGuidesChanged.emit()

    @pyqtProperty(str, notify=backgroundColorChanged)
    def backgroundColor(self):
        return self._backgroundColor

    @backgroundColor.setter
    def backgroundColor(self, value):
        if self._backgroundColor != value:
            self._backgroundColor = value
            self.backgroundColorChanged.emit()
            # Si ya hay una imagen con fondo removido, aplicar el nuevo color
            if self.background_removed_image is not None:
                self.applyBackgroundColor()

class ImageProvider(QQuickImageProvider):
    def __init__(self, processor):
        super().__init__(QQuickImageProvider.ImageType.Image)
        self.processor = processor

    def requestImage(self, id: str, requested_size: QSize) -> tuple[QImage, QSize]:
        if id == "logo":
            try:
                logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
                if not os.path.exists(logo_path):
                    print(f"Error: Logo file not found at {logo_path}")
                    return QImage(), QSize()
                
                logo = cv2.imread(logo_path, cv2.IMREAD_UNCHANGED)
                if logo is None:
                    print(f"Error: Failed to load logo from {logo_path}")
                    return QImage(), QSize()
                
                height, width = logo.shape[:2]
                bytes_per_line = 4 * width if logo.shape[2] == 4 else 3 * width
                
                if logo.shape[2] == 4:  # If the image has an alpha channel
                    qimg = QImage(logo.data, width, height, bytes_per_line, QImage.Format.Format_RGBA8888).rgbSwapped()
                else:
                    qimg = QImage(logo.data, width, height, bytes_per_line, QImage.Format.Format_RGB888).rgbSwapped()
                
                if requested_size.isValid():
                    qimg = qimg.scaled(requested_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                
                return qimg, qimg.size()
            except Exception as e:
                print(f"Error loading logo: {str(e)}")
                return QImage(), QSize()
        elif self.processor.image is None:
            return QImage(), QSize()
        else:
            height, width, channel = self.processor.image.shape
            bytes_per_line = 3 * width
            qimg = QImage(self.processor.image.data, width, height, bytes_per_line, QImage.Format.Format_RGB888).rgbSwapped()
            return qimg, QSize(width, height)

if __name__ == "__main__":
    app = QGuiApplication(sys.argv)
    
    engine = QQmlApplicationEngine()
    
    imageProcessor = ImageProcessor()
    engine.rootContext().setContextProperty("imageProcessor", imageProcessor)
    
    imageProvider = ImageProvider(imageProcessor)
    engine.addImageProvider("live", imageProvider)
    
    qml_file = os.path.join(os.path.dirname(__file__), "main.qml")
    engine.load(QUrl.fromLocalFile(qml_file))
    
    if not engine.rootObjects():
        print("Error: Failed to load QML file")
        sys.exit(-1)
    
    sys.exit(app.exec())