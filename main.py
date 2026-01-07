"""
Mi Foto Carnet - Aplicación para preparación e impresión de fotos tipo carnet
Versión 1.3 - Con ajuste vertical manual y PhotoRoom API

Dependencias requeridas:
pip install PyQt6 opencv-python numpy requests pillow
"""

import sys
import os
import io
import json
import requests
from PyQt6.QtCore import QUrl, QObject, pyqtSlot, QSize, pyqtProperty, QRect, pyqtSignal, Qt, QSizeF
from PyQt6.QtGui import QGuiApplication, QImage, QPainter, QPageSize, QPageLayout, QPen, QColor
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
        self.centered_original = None
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
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
        
        # Nuevas variables para el ajuste manual
        self._manual_vertical_shift = 0
        self._isShowingPersonalData = False
        self._personalDataRatio = 0.2
        
        self.load_config()

    def load_config(self):
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        default_config = {
            "photoroom_api": {
                "api_key": "TU_API_KEY",
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
            else:
                self.photoroom_api_key = default_config["photoroom_api"]["api_key"]
                self.photoroom_api_url = default_config["photoroom_api"]["api_url"]
                self.app_settings = default_config["app_settings"]
                with open(config_path, 'w') as f:
                    json.dump(default_config, f, indent=2)
        except Exception as e:
            print(f"Error config: {str(e)}")
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
        self._brightness = 0
        self._contrast = 0
        self._saturation = 0
        self._manual_vertical_shift = 0 # Resetear shift
        return self.image is not None

    def detect_face(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 6, minSize=(50, 50))
        if len(faces) == 0:
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 4, minSize=(40, 40))
        
        valid_faces = []
        for (x, y, w, h) in faces:
            if 0.8 < h / w < 1.8:
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

        if top == 0: bottom = face_height
        elif bottom == height: top = height - face_height
        if left == 0: right = face_width
        elif right == width: left = width - face_width

        cropped_image = image[top:bottom, left:right]
        
        # Ajustar al canvas manteniendo aspect ratio
        canvas_ratio = canvas_width / canvas_height
        img_ratio = cropped_image.shape[1] / cropped_image.shape[0]

        if canvas_ratio > img_ratio:
            new_height = int(canvas_height)
            new_width = int(new_height * img_ratio)
        else:
            new_width = int(canvas_width)
            new_height = int(new_width / img_ratio)

        self.centered_image = cv2.resize(cropped_image, (new_width, new_height), interpolation=cv2.INTER_AREA)
        self.centered_original = self.centered_image.copy()
        
        self._isCentered = True
        self.isCenteredChanged.emit()
        self.background_removed_image = None
        self.mask = None
        self._manual_vertical_shift = 0 # Resetear shift al centrar nuevo
        
        # Generar imagen final
        self._updateFinalImage()
        return True
    
    @pyqtSlot(float)
    def addVerticalShift(self, dy):
        """Recibe el desplazamiento vertical desde el MouseArea de QML"""
        if self.centered_image is None:
            return
        self._manual_vertical_shift += dy
        self._updateFinalImage()

    def _updateFinalImage(self):
        """Pipeline central de procesamiento de imagen"""
        if self.centered_image is None:
            return

        # 1. Empezar desde la imagen base centrada (con o sin fondo removido)
        img = self.centered_image.copy()
        rows, cols, _ = img.shape

        # 2. Aplicar Desplazamiento Vertical Manual
        shift = int(self._manual_vertical_shift)
        if shift != 0:
            # Obtener color de fondo para rellenar huecos
            hex_color = self._backgroundColor.lstrip('#')
            rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            bgr_color = (rgb[2], rgb[1], rgb[0])
            
            shifted_img = np.full_like(img, bgr_color)
            
            if shift > 0: # Mover imagen hacia abajo (rellenar arriba)
                # Asegurarse de no salir de los límites
                copy_height = rows - shift
                if copy_height > 0:
                    shifted_img[shift:, :] = img[:copy_height, :]
            else: # Mover imagen hacia arriba (rellenar abajo)
                copy_height = rows + shift # shift es negativo
                if copy_height > 0:
                    shifted_img[:copy_height, :] = img[-shift:, :]
            
            img = shifted_img

        # 3. Aplicar Ajustes de Color (Brillo/Contraste)
        brightness = self._brightness
        contrast = self._contrast / 100.0
        
        if brightness != 0 or contrast != 0:
            img = cv2.convertScaleAbs(img, alpha=1 + contrast, beta=brightness)
        
        # 4. Aplicar Saturación
        if self._saturation != 0:
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(np.float32)
            saturation_scale = 1 + (self._saturation / 100.0)
            hsv[:, :, 1] = np.clip(hsv[:, :, 1] * saturation_scale, 0, 255)
            img = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

        # 5. Aplicar Recorte para Datos Personales
        if self._isShowingPersonalData:
            # La lógica original: desplazar hacia arriba cortando la parte superior
            # para dejar espacio negro abajo (que es parte del fondo del control QML o añadido aquí)
            # Nota: El código original creaba una imagen negra y pegaba la foto desplazada hacia arriba.
            shift_pixels = int(rows * self._personalDataRatio / 3.44)
            
            result_with_data = np.zeros_like(img) # Fondo negro por defecto
            
            # Copiar la imagen desplazada hacia arriba
            if shift_pixels < rows:
                result_with_data[:-shift_pixels, :] = img[shift_pixels:, :]
            
            img = result_with_data

        self.image = img
        self.imageChanged.emit()

    @pyqtSlot(result=bool)
    def removeBackgroundWithPhotoRoom(self):
        if self.centered_original is None or not self._isCentered:
            return False

        try:
            self.processingStatusChanged.emit("Procesando con PhotoRoom...")
            image = self.centered_original.copy()
            _, buffer = cv2.imencode('.jpg', image)
            
            headers = {"x-api-key": self.photoroom_api_key}
            files = {'image_file': ('image.jpg', buffer.tobytes(), 'image/jpeg')}
            
            response = requests.post(self.photoroom_api_url, headers=headers, files=files)
            
            if response.status_code == 200:
                response_image = Image.open(io.BytesIO(response.content))
                response_array = np.array(response_image)
                
                if response_array.shape[2] == 4:
                    alpha = response_array[:, :, 3]
                    rgb = response_array[:, :, :3]
                    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
                    
                    self.mask = alpha.astype(np.float32) / 255.0
                    mask_3 = np.stack([alpha, alpha, alpha], axis=-1)
                    
                    self.background_removed_image = np.where(mask_3 > 0, bgr, 0).astype(np.uint8)
                    
                    self.applyBackgroundColor() # Esto llamará a _updateFinalImage
                    self.processingStatusChanged.emit("Fondo eliminado")
                    return True
            return False
        except Exception as e:
            print(f"Error API: {str(e)}")
            self.processingStatusChanged.emit(f"Error: {str(e)}")
            return False

    def applyBackgroundColor(self):
        if self.background_removed_image is None or self.mask is None:
            return
        
        hex_color = self._backgroundColor.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        bgr_color = (rgb[2], rgb[1], rgb[0])
        
        result = np.full_like(self.background_removed_image, bgr_color)
        
        mask_3 = np.stack([self.mask, self.mask, self.mask], axis=-1)
        result = (self.background_removed_image * mask_3 + result * (1 - mask_3)).astype(np.uint8)
        
        self.centered_image = result
        self._updateFinalImage()

    @pyqtSlot()
    def applyImageAdjustments(self):
        self._updateFinalImage()

    @pyqtSlot(bool, float)
    def adjustImageForPersonalData(self, show_data, overlay_height_ratio):
        self._isShowingPersonalData = show_data
        self._personalDataRatio = overlay_height_ratio
        self._updateFinalImage()

    @pyqtSlot(float, float, result=bool)
    def adjustPrintLayout(self, canvas_width, canvas_height):
        if self.image is None or not self._isCentered or not self.current_photo_size:
            return False

        PAPER_WIDTH_MM = self.app_settings.get("paper_width_mm", 152)
        PAPER_HEIGHT_MM = self.app_settings.get("paper_height_mm", 102)
        MARGIN_SAFETY_MM = self.app_settings.get("margin_safety_mm", 5)
        USABLE_WIDTH_MM = PAPER_WIDTH_MM - (2 * MARGIN_SAFETY_MM)
        USABLE_HEIGHT_MM = PAPER_HEIGHT_MM - (2 * MARGIN_SAFETY_MM)
        
        DPI = self.app_settings.get("default_dpi", 300)
        MM_TO_PX = DPI / 25.4

        photo_width_cm, photo_height_cm = self.current_photo_size
        photo_width_mm = photo_width_cm * 10
        photo_height_mm = photo_height_cm * 10
        photo_width_px = photo_width_mm * MM_TO_PX
        photo_height_px = photo_height_mm * MM_TO_PX

        MARGIN_MM = self.app_settings.get("margin_between_photos_mm", 2)

        num_cols = int((USABLE_WIDTH_MM + MARGIN_MM) / (photo_width_mm + MARGIN_MM))
        if (num_cols * photo_width_mm) + ((num_cols - 1) * MARGIN_MM) > USABLE_WIDTH_MM: num_cols -= 1
        
        num_rows = int((USABLE_HEIGHT_MM + MARGIN_MM) / (photo_height_mm + MARGIN_MM))
        if (num_rows * photo_height_mm) + ((num_rows - 1) * MARGIN_MM) > USABLE_HEIGHT_MM: num_rows -= 1

        if photo_width_cm >= 5.0 or photo_height_cm >= 5.0:
            if photo_width_cm >= photo_height_cm: num_cols, num_rows = min(num_cols, 2), min(num_rows, 1)
            else: num_cols, num_rows = min(num_cols, 1), min(num_rows, 2)
        
        if photo_width_cm >= 6.0 or photo_height_cm >= 9.0: num_cols, num_rows = 1, 1
        
        MAX_PHOTOS = self.app_settings.get("max_photos_per_sheet", 8)
        if num_cols * num_rows > MAX_PHOTOS:
            if num_cols >= num_rows: num_cols = min(4, MAX_PHOTOS // 2); num_rows = min(2, MAX_PHOTOS // num_cols)
            else: num_cols = min(2, MAX_PHOTOS // 4); num_rows = min(4, MAX_PHOTOS // num_cols)

        if num_cols == 0 or num_rows == 0: return False

        total_width_mm = (photo_width_mm * num_cols) + (MARGIN_MM * (num_cols - 1))
        total_height_mm = (photo_height_mm * num_rows) + (MARGIN_MM * (num_rows - 1))

        start_x_mm = (PAPER_WIDTH_MM - total_width_mm) / 2
        start_y_mm = (PAPER_HEIGHT_MM - total_height_mm) / 2
        
        self.print_layout = []
        for row in range(num_rows):
            for col in range(num_cols):
                x_mm = start_x_mm + (col * (photo_width_mm + MARGIN_MM))
                y_mm = start_y_mm + (row * (photo_height_mm + MARGIN_MM))
                
                self.print_layout.append({
                    "x": x_mm * MM_TO_PX,
                    "y": y_mm * MM_TO_PX,
                    "width": photo_width_px,
                    "height": photo_height_px,
                    "x_canvas": x_mm,
                    "y_canvas": y_mm,
                    "width_canvas": photo_width_mm,
                    "height_canvas": photo_height_mm
                })

        self.printLayoutChanged.emit()
        return True

    @pyqtSlot()
    def clearLayout(self):
        self.print_layout = []
        self.printLayoutChanged.emit()

    @pyqtSlot(str, result=bool)
    def setCurrent_photo_size(self, size_str):
        try:
            parts = size_str.split(' - ')
            dim_str = parts[1] if len(parts) == 2 else size_str.replace(' - ', '')
            dims = dim_str.replace('cm', '').strip().split('x')
            
            w, h = float(dims[0]), float(dims[1])
            if self.current_photo_size and (self.current_photo_size[0] != w or self.current_photo_size[1] != h):
                self.print_layout = []
                self.printLayoutChanged.emit()
            
            self.current_photo_size = [w, h]
            return True
        except: return False

    @pyqtProperty("QVariantList", notify=printLayoutChanged)
    def layout(self): return self.print_layout

    @pyqtSlot(result=list)
    def getPrinters(self):
        return [p.printerName() for p in QPrinterInfo.availablePrinters()]

    @pyqtSlot(int)
    def setCurrentPrinter(self, index):
        printers = QPrinterInfo.availablePrinters()
        if 0 <= index < len(printers): self.current_printer = printers[index]

    @pyqtSlot()
    def printImage(self):
        if self.image is None or self.current_printer is None or not self.print_layout: return

        printer = QPrinter(self.current_printer)
        printer.setResolution(self.app_settings.get("default_dpi", 300))
        printer.setFullPage(True)
        
        page_size = QPageSize(QSizeF(152.0, 102.0), QPageSize.Unit.Millimeter)
        printer.setPageSize(page_size)
        printer.setPageOrientation(QPageLayout.Orientation.Landscape)

        painter = QPainter()
        if not painter.begin(printer): return

        qimage = self.cv_to_qimage(self.image)

        # Dibujar guías
        if self._showCutGuides:
            painter.setPen(QPen(QColor(0, 0, 0), 1))
            for l in self.print_layout:
                x, y, w, h = int(l["x"]), int(l["y"]), int(l["width"]), int(l["height"])
                g = 10
                painter.drawLine(x-g, y, x+g, y); painter.drawLine(x, y-g, x, y+g)
                painter.drawLine(x+w-g, y, x+w+g, y); painter.drawLine(x+w, y-g, x+w, y+g)
                painter.drawLine(x-g, y+h, x+g, y+h); painter.drawLine(x, y+h-g, x, y+h+g)
                painter.drawLine(x+w-g, y+h, x+w+g, y+h); painter.drawLine(x+w, y+h-g, x+w, y+h+g)

        # Dibujar fotos y textos
        for l in self.print_layout:
            rect = QRect(int(l["x"]), int(l["y"]), int(l["width"]), int(l["height"]))
            painter.drawImage(rect, qimage)
            
            if self._name or self._lastname or self._rut:
                t_h = l["height"] / 5
                t_rect = QRect(int(l["x"]), int(l["y"] + l["height"] - t_h), int(l["width"]), int(t_h))
                painter.fillRect(t_rect, Qt.GlobalColor.black)
                
                painter.setPen(Qt.GlobalColor.white)
                font = painter.font()
                font.setPixelSize(int(t_h / 3.5))
                font.setFamily("Arial")
                font.setBold(True)
                painter.setFont(font)
                
                lh = (t_h - t_h/8) / 3
                by = int(l["y"] + l["height"] - t_h + t_h/16)
                
                if self._name: painter.drawText(QRect(int(l["x"]), by, int(l["width"]), int(lh)), Qt.AlignmentFlag.AlignHCenter|Qt.AlignmentFlag.AlignVCenter, self._name)
                if self._lastname: painter.drawText(QRect(int(l["x"]), by+int(lh), int(l["width"]), int(lh)), Qt.AlignmentFlag.AlignHCenter|Qt.AlignmentFlag.AlignVCenter, self._lastname)
                if self._rut: painter.drawText(QRect(int(l["x"]), by+int(2*lh), int(l["width"]), int(lh)), Qt.AlignmentFlag.AlignHCenter|Qt.AlignmentFlag.AlignVCenter, self._rut)

        painter.end()

    def cv_to_qimage(self, cv_img):
        h, w, c = cv_img.shape
        return QImage(cv_img.data, w, h, 3*w, QImage.Format.Format_RGB888).rgbSwapped()

    # Propiedades
    @pyqtProperty(str, notify=nameChanged)
    def name(self): return self._name
    @name.setter
    def name(self, v): self._name = v; self.nameChanged.emit()

    @pyqtProperty(str, notify=lastnameChanged)
    def lastname(self): return self._lastname
    @lastname.setter
    def lastname(self, v): self._lastname = v; self.lastnameChanged.emit()

    @pyqtProperty(str, notify=rutChanged)
    def rut(self): return self._rut
    @rut.setter
    def rut(self, v): self._rut = v; self.rutChanged.emit()

    @pyqtProperty(bool, notify=isCenteredChanged)
    def isCentered(self): return self._isCentered

    @pyqtProperty(float, notify=brightnessChanged)
    def brightness(self): return self._brightness
    @brightness.setter
    def brightness(self, v): self._brightness = v; self.brightnessChanged.emit()

    @pyqtProperty(float, notify=contrastChanged)
    def contrast(self): return self._contrast
    @contrast.setter
    def contrast(self, v): self._contrast = v; self.contrastChanged.emit()

    @pyqtProperty(float, notify=saturationChanged)
    def saturation(self): return self._saturation
    @saturation.setter
    def saturation(self, v): self._saturation = v; self.saturationChanged.emit()

    @pyqtProperty(bool, notify=showCutGuidesChanged)
    def showCutGuides(self): return self._showCutGuides
    @showCutGuides.setter
    def showCutGuides(self, v): self._showCutGuides = v; self.showCutGuidesChanged.emit()

    @pyqtProperty(str, notify=backgroundColorChanged)
    def backgroundColor(self): return self._backgroundColor
    @backgroundColor.setter
    def backgroundColor(self, v): 
        self._backgroundColor = v; self.backgroundColorChanged.emit()
        if self.background_removed_image is not None: self.applyBackgroundColor()

class ImageProvider(QQuickImageProvider):
    def __init__(self, processor):
        super().__init__(QQuickImageProvider.ImageType.Image)
        self.processor = processor

    def requestImage(self, id, size):
        if id == "logo":
            try:
                p = os.path.join(os.path.dirname(__file__), "logo.png")
                if not os.path.exists(p): return QImage(), QSize()
                img = cv2.imread(p, cv2.IMREAD_UNCHANGED)
                if img is None: return QImage(), QSize()
                h, w = img.shape[:2]
                fmt = QImage.Format.Format_RGBA8888 if img.shape[2] == 4 else QImage.Format.Format_RGB888
                qimg = QImage(img.data, w, h, (4 if img.shape[2]==4 else 3)*w, fmt).rgbSwapped()
                return qimg, qimg.size()
            except: return QImage(), QSize()
        elif self.processor.image is None:
            return QImage(), QSize()
        else:
            h, w = self.processor.image.shape[:2]
            return QImage(self.processor.image.data, w, h, 3*w, QImage.Format.Format_RGB888).rgbSwapped(), QSize(w, h)

if __name__ == "__main__":
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()
    proc = ImageProcessor()
    engine.rootContext().setContextProperty("imageProcessor", proc)
    engine.addImageProvider("live", ImageProvider(proc))
    engine.load(QUrl.fromLocalFile(os.path.join(os.path.dirname(__file__), "main.qml")))
    if not engine.rootObjects(): sys.exit(-1)
    sys.exit(app.exec())