import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Dialogs
import QtQuick.Controls.Material 2.15

ApplicationWindow {
    visible: true
    width: 1366
    height: 800
    title: "Mi Foto carnet"

    Material.theme: Material.Light
    Material.accent: Material.Blue

    FileDialog {
        id: fileDialog
        title: "Seleccionar fotografia"
        nameFilters: ["Archivos de imagen (*.jpg *.png *.bmp)"]
        onAccepted: {
            if (imageProcessor.loadImage(fileDialog.selectedFile)) {
                imageView.source = ""
                imageView.source = "image://live/image"
            }
        }
    }

    RowLayout {
        anchors.fill: parent
        spacing: 16

        // Área principal (cambia con las pestañas)
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            TabBar {
                id: tabBar
                Layout.fillWidth: true
                Layout.preferredHeight: 50
                background: Rectangle {
                    color: Material.gray
                }

                TabButton {
                    text: "Edición"
                    width: implicitWidth
                }
                TabButton {
                    text: "Preparación"
                    width: implicitWidth
                }
                TabButton {
                    text: "Ajustes"
                    width: implicitWidth
                }
                TabButton {
                    text: "Acerca de"
                    width: implicitWidth
                }
            }

            StackLayout {
                currentIndex: tabBar.currentIndex
                Layout.fillWidth: true
                Layout.fillHeight: true

                // Pestaña 1: Edición
                Item {
                    Pane {
                        id: imagePane
                        anchors.fill: parent
                        Material.elevation: 4

                        Item {
                            id: imageContainer
                            anchors.fill: parent

                            Image {
                                id: imageView
                                anchors.centerIn: parent
                                fillMode: Image.PreserveAspectFit
                                width: Math.min(parent.width, sourceSize.width)
                                height: Math.min(parent.height, sourceSize.height)
                                cache: false
                                source: "image://live/image"

                                Connections {
                                    target: imageProcessor
                                    function onImageChanged() {
                                        imageView.source = ""
                                        imageView.source = "image://live/image"
                                    }
                                }
                            }

                            Rectangle {
                                id: textOverlay
                                visible: textVisibilitySwitch.checked
                                anchors.bottom: imageView.bottom
                                anchors.horizontalCenter: imageView.horizontalCenter
                                width: imageView.paintedWidth
                                height: imageView.paintedHeight / 5
                                color: "black"

                                Column {
                                    anchors.fill: parent
                                    anchors.margins: 8
                                    spacing: 0

                                    Text {
                                        text: nameField.text
                                        color: "white"
                                        font.pixelSize: 32
                                        font.family: "Arial"
                                        font.bold: true
                                        width: parent.width
                                        horizontalAlignment: Text.AlignHCenter
                                        elide: Text.ElideRight
                                    }
                                    Text {
                                        text: lastNameField.text
                                        color: "white"
                                        font.pixelSize: 32
                                        font.family: "Arial"
                                        font.bold: true
                                        width: parent.width
                                        horizontalAlignment: Text.AlignHCenter
                                        elide: Text.ElideRight
                                    }
                                    Text {
                                        text: rutField.text
                                        color: "white"
                                        font.pixelSize: 32
                                        font.family: "Arial"
                                        font.bold: true
                                        width: parent.width
                                        horizontalAlignment: Text.AlignHCenter
                                        elide: Text.ElideRight
                                    }
                                }
                            }
                        }
                    }
                }

                // Pestaña 2: Preparación
                Item {
                    Pane {
                        id: canvasPane
                        anchors.fill: parent
                        padding: 10
                        Material.elevation: 4

                        Rectangle {
                            id: printCanvas
                            anchors.centerIn: parent
                            // Mantener proporción 152:102 (15.2cm x 10.2cm)
                            width: Math.min(parent.width * 0.95, parent.height * 0.95 * (152/102))
                            height: width * (102/152)
                            border.color: "black"
                            border.width: 2
                            color: "white"

                            // Factor de escala: convertir mm a píxeles del canvas
                            property real scaleFactor: width / 152

                            // Texto informativo
                            Text {
                                anchors.top: parent.top
                                anchors.left: parent.left
                                anchors.margins: 10
                                text: "Papel: 15.2 x 10.2 cm"
                                color: "#666"
                                font.pixelSize: 12
                            }

                            // Dibujar guías de corte si están habilitadas
                            Repeater {
                                visible: imageProcessor.showCutGuides
                                model: imageProcessor.layout
                                delegate: Item {
                                    property real photoX: modelData.x_canvas * printCanvas.scaleFactor
                                    property real photoY: modelData.y_canvas * printCanvas.scaleFactor
                                    property real photoWidth: modelData.width_canvas * printCanvas.scaleFactor
                                    property real photoHeight: modelData.height_canvas * printCanvas.scaleFactor

                                    // Guías de corte (líneas en cruz)
                                    Rectangle {
                                        x: photoX - 10
                                        y: photoY
                                        width: 20
                                        height: 1
                                        color: "black"
                                    }
                                    Rectangle {
                                        x: photoX
                                        y: photoY - 10
                                        width: 1
                                        height: 20
                                        color: "black"
                                    }
                                    // Esquina superior derecha
                                    Rectangle {
                                        x: photoX + photoWidth - 10
                                        y: photoY
                                        width: 20
                                        height: 1
                                        color: "black"
                                    }
                                    Rectangle {
                                        x: photoX + photoWidth
                                        y: photoY - 10
                                        width: 1
                                        height: 20
                                        color: "black"
                                    }
                                    // Esquina inferior izquierda
                                    Rectangle {
                                        x: photoX - 10
                                        y: photoY + photoHeight
                                        width: 20
                                        height: 1
                                        color: "black"
                                    }
                                    Rectangle {
                                        x: photoX
                                        y: photoY + photoHeight - 10
                                        width: 1
                                        height: 20
                                        color: "black"
                                    }
                                    // Esquina inferior derecha
                                    Rectangle {
                                        x: photoX + photoWidth - 10
                                        y: photoY + photoHeight
                                        width: 20
                                        height: 1
                                        color: "black"
                                    }
                                    Rectangle {
                                        x: photoX + photoWidth
                                        y: photoY + photoHeight - 10
                                        width: 1
                                        height: 20
                                        color: "black"
                                    }
                                }
                            }

                            Repeater {
                                model: imageProcessor.layout
                                delegate: Item {
                                    // Usar las coordenadas del canvas (en mm) y convertir a píxeles del canvas
                                    x: modelData.x_canvas * printCanvas.scaleFactor
                                    y: modelData.y_canvas * printCanvas.scaleFactor
                                    width: modelData.width_canvas * printCanvas.scaleFactor
                                    height: modelData.height_canvas * printCanvas.scaleFactor

                                    Rectangle {
                                        anchors.fill: parent
                                        color: "transparent"
                                        border.color: "#888"
                                        border.width: 1
                                    }

                                    Image {
                                        id: photoImage
                                        anchors.fill: parent
                                        source: imageProcessor.isCentered ? "image://live/image" : ""
                                        cache: false
                                        smooth: true
                                        fillMode: Image.Stretch  // Stretch para mantener el tamaño exacto
                                    }

                                    Rectangle {
                                        visible: textVisibilitySwitch.checked && (nameField.text || lastNameField.text || rutField.text)
                                        anchors.bottom: parent.bottom
                                        width: parent.width
                                        height: parent.height / 5
                                        color: "black"

                                        Column {
                                            anchors.fill: parent
                                            anchors.margins: parent.height * 0.03
                                            spacing: 0

                                            Text {
                                                text: nameField.text
                                                color: "white"
                                                font.pixelSize: Math.max(6, parent.height * 0.28)
                                                font.family: "Arial"
                                                font.bold: true
                                                width: parent.width
                                                horizontalAlignment: Text.AlignHCenter
                                                elide: Text.ElideRight
                                            }
                                            Text {
                                                text: lastNameField.text
                                                color: "white"
                                                font.pixelSize: Math.max(6, parent.height * 0.28)
                                                font.family: "Arial"
                                                font.bold: true
                                                width: parent.width
                                                horizontalAlignment: Text.AlignHCenter
                                                elide: Text.ElideRight
                                            }
                                            Text {
                                                text: rutField.text
                                                color: "white"
                                                font.pixelSize: Math.max(6, parent.height * 0.28)
                                                font.family: "Arial"
                                                font.bold: true
                                                width: parent.width
                                                horizontalAlignment: Text.AlignHCenter
                                                elide: Text.ElideRight
                                            }
                                        }
                                    }
                                }
                            }

                            // Mensaje cuando no hay layout
                            Label {
                                anchors.centerIn: parent
                                text: imageProcessor.isCentered ? 
                                      "Presione 'Ajustar hoja' para preparar la impresión" :
                                      "Primero centre una imagen en la pestaña de Edición"
                                visible: imageProcessor.layout.length === 0
                                color: "#666"
                                font.pixelSize: 14
                            }

                            // Contador de fotos
                            Text {
                                anchors.bottom: parent.bottom
                                anchors.right: parent.right
                                anchors.margins: 10
                                text: imageProcessor.layout.length > 0 ? 
                                      "Fotos: " + imageProcessor.layout.length :
                                      ""
                                color: "#666"
                                font.pixelSize: 12
                            }
                        }

                        Label {
                            anchors.centerIn: parent
                            text: "Ajuste una imagen en la pestaña de Edición primero"
                            visible: !imageProcessor.isCentered && imageProcessor.layout.length === 0
                            color: "#666"
                        }
                    }
                }

                // Pestaña 3: Ajustes
                Item {
                    Pane {
                        anchors.fill: parent
                        Material.elevation: 4
                        
                        ScrollView {
                            anchors.fill: parent
                            contentWidth: availableWidth
                            
                            ColumnLayout {
                                width: parent.width
                                spacing: 20
                                
                                Label {
                                    text: "Configuración de Imagen"
                                    font.pixelSize: 24
                                    font.bold: true
                                    Layout.alignment: Qt.AlignHCenter
                                }
                                
                                Rectangle {
                                    Layout.preferredHeight: 1
                                    Layout.fillWidth: true
                                    color: "#ddd"
                                }
                                
                                // Controles de ajuste de imagen
                                GridLayout {
                                    columns: 2
                                    columnSpacing: 20
                                    rowSpacing: 15
                                    Layout.alignment: Qt.AlignHCenter
                                    Layout.maximumWidth: 600
                                    
                                    Label {
                                        text: "Brillo:"
                                        font.pixelSize: 14
                                        Layout.alignment: Qt.AlignRight
                                    }
                                    
                                    RowLayout {
                                        Slider {
                                            id: brightnessSlider
                                            from: -100
                                            to: 100
                                            value: 0
                                            Layout.preferredWidth: 300
                                            onValueChanged: imageProcessor.brightness = value
                                        }
                                        Label {
                                            text: Math.round(brightnessSlider.value)
                                            font.pixelSize: 12
                                            Layout.preferredWidth: 40
                                        }
                                    }
                                    
                                    Label {
                                        text: "Contraste:"
                                        font.pixelSize: 14
                                        Layout.alignment: Qt.AlignRight
                                    }
                                    
                                    RowLayout {
                                        Slider {
                                            id: contrastSlider
                                            from: -100
                                            to: 100
                                            value: 0
                                            Layout.preferredWidth: 300
                                            onValueChanged: imageProcessor.contrast = value
                                        }
                                        Label {
                                            text: Math.round(contrastSlider.value)
                                            font.pixelSize: 12
                                            Layout.preferredWidth: 40
                                        }
                                    }
                                    
                                    Label {
                                        text: "Saturación:"
                                        font.pixelSize: 14
                                        Layout.alignment: Qt.AlignRight
                                    }
                                    
                                    RowLayout {
                                        Slider {
                                            id: saturationSlider
                                            from: -100
                                            to: 100
                                            value: 0
                                            Layout.preferredWidth: 300
                                            onValueChanged: imageProcessor.saturation = value
                                        }
                                        Label {
                                            text: Math.round(saturationSlider.value)
                                            font.pixelSize: 12
                                            Layout.preferredWidth: 40
                                        }
                                    }
                                }
                                
                                Button {
                                    text: "Aplicar Ajustes de Imagen"
                                    Layout.alignment: Qt.AlignHCenter
                                    Layout.preferredHeight: 48
                                    Layout.preferredWidth: 250
                                    highlighted: true
                                    onClicked: {
                                        imageProcessor.applyImageAdjustments()
                                        // Reajustar para datos personales si están visibles
                                        imageProcessor.adjustImageForPersonalData(textVisibilitySwitch.checked, 0.2)
                                    }
                                    enabled: imageProcessor.isCentered
                                }
                                
                                Button {
                                    text: "Restablecer Ajustes"
                                    Layout.alignment: Qt.AlignHCenter
                                    Layout.preferredHeight: 40
                                    Layout.preferredWidth: 200
                                    onClicked: {
                                        brightnessSlider.value = 0
                                        contrastSlider.value = 0
                                        saturationSlider.value = 0
                                        imageProcessor.brightness = 0
                                        imageProcessor.contrast = 0
                                        imageProcessor.saturation = 0
                                        imageProcessor.applyImageAdjustments()
                                        imageProcessor.adjustImageForPersonalData(textVisibilitySwitch.checked, 0.2)
                                    }
                                }
                                
                                Rectangle {
                                    Layout.preferredHeight: 1
                                    Layout.fillWidth: true
                                    color: "#ddd"
                                }
                                
                                Label {
                                    text: "Configuración de Impresión"
                                    font.pixelSize: 20
                                    font.bold: true
                                    Layout.alignment: Qt.AlignHCenter
                                }
                                
                                GridLayout {
                                    columns: 2
                                    columnSpacing: 20
                                    rowSpacing: 15
                                    Layout.alignment: Qt.AlignHCenter
                                    Layout.maximumWidth: 600
                                    
                                    Label {
                                        text: "Impresora:"
                                        font.pixelSize: 14
                                        Layout.alignment: Qt.AlignRight
                                    }
                                    
                                    ComboBox {
                                        id: printerComboBox
                                        Layout.preferredWidth: 350
                                        Layout.preferredHeight: 48
                                        model: imageProcessor.getPrinters()
                                        onCurrentIndexChanged: imageProcessor.setCurrentPrinter(currentIndex)
                                    }
                                    
                                    Label {
                                        text: "Guías de corte:"
                                        font.pixelSize: 14
                                        Layout.alignment: Qt.AlignRight
                                    }
                                    
                                    Switch {
                                        id: cutGuidesSwitch
                                        checked: false
                                        onCheckedChanged: imageProcessor.showCutGuides = checked
                                    }
                                }
                                
                                Button {
                                    text: "Aplicar Configuración de Impresión"
                                    Layout.alignment: Qt.AlignHCenter
                                    Layout.preferredHeight: 48
                                    Layout.preferredWidth: 250
                                    highlighted: true
                                    Material.background: Material.Green
                                    onClicked: {
                                        console.log("Configuración de impresión aplicada")
                                    }
                                }
                                
                                Rectangle {
                                    Layout.preferredHeight: 1
                                    Layout.fillWidth: true
                                    color: "#ddd"
                                }
                                
                                Label {
                                    text: "Información del Sistema"
                                    font.pixelSize: 16
                                    font.bold: true
                                    Layout.alignment: Qt.AlignHCenter
                                }
                                
                                Label {
                                    text: "Papel: 15.2 x 10.2 cm (6 x 4 pulgadas)"
                                    font.pixelSize: 14
                                    Layout.alignment: Qt.AlignHCenter
                                }
                                
                                Label {
                                    text: "Resolución: 300 DPI"
                                    font.pixelSize: 14
                                    Layout.alignment: Qt.AlignHCenter
                                }
                                
                                Label {
                                    text: "Margen entre fotos: 2 mm"
                                    font.pixelSize: 14
                                    Layout.alignment: Qt.AlignHCenter
                                }
                            }
                        }
                    }
                }

                // Pestaña 4: Acerca de
                Item {
                    Pane {
                        anchors.fill: parent
                        Material.elevation: 4
                        
                        ColumnLayout {
                            anchors.centerIn: parent
                            spacing: 20
                            
                            Label {
                                text: "Mi Foto Carnet"
                                font.pixelSize: 28
                                font.bold: true
                                Layout.alignment: Qt.AlignHCenter
                            }
                            
                            Label {
                                text: "Versión 1.0"
                                font.pixelSize: 18
                                Layout.alignment: Qt.AlignHCenter
                            }
                            
                            Rectangle {
                                Layout.preferredHeight: 1
                                Layout.fillWidth: true
                                color: "#ddd"
                            }
                            
                            Label {
                                text: "Software para preparación e impresión\nde fotografías tipo carnet"
                                font.pixelSize: 16
                                horizontalAlignment: Text.AlignHCenter
                                Layout.alignment: Qt.AlignHCenter
                            }
                            
                            Label {
                                text: "• Detección automática de rostros\n• Múltiples tamaños internacionales\n• Impresión optimizada en papel 15.2x10.2 cm\n• Datos personales opcionales\n• Cambio de fondo con IA (MediaPipe)\n• Ajustes de imagen profesionales\n• Guías de corte para recorte preciso"
                                font.pixelSize: 14
                                color: "#666"
                                Layout.alignment: Qt.AlignHCenter
                            }
                            
                            Rectangle {
                                Layout.preferredHeight: 1
                                Layout.fillWidth: true
                                color: "#ddd"
                            }
                            
                            Label {
                                text: "Tecnologías utilizadas:"
                                font.pixelSize: 14
                                font.bold: true
                                Layout.alignment: Qt.AlignHCenter
                            }
                            
                            Label {
                                text: "OpenCV, MediaPipe Selfie Segmentation, PyQt6"
                                font.pixelSize: 12
                                color: "#666"
                                Layout.alignment: Qt.AlignHCenter
                            }
                        }
                    }
                }
            }
        }

        // Panel lateral (siempre visible)
        Pane {
            id: sidePanel
            Layout.fillHeight: true
            Layout.preferredWidth: parent.width / 4
            Material.elevation: 4

            ColumnLayout {
                anchors.fill: parent
                spacing: 16

                Image {
                    id: logoImage
                    source: "image://live/logo"
                    Layout.alignment: Qt.AlignHCenter
                    Layout.preferredWidth: sidePanel.width - 128
                    Layout.preferredHeight: width * (sourceSize.height / sourceSize.width)
                    fillMode: Image.PreserveAspectFit
                    onStatusChanged: {
                        if (status === Image.Error) {
                            console.log("Error loading logo")
                            source = ""
                        }
                    }
                }

                StackLayout {
                    currentIndex: tabBar.currentIndex
                    Layout.fillWidth: true
                    Layout.fillHeight: true

                    // Controles para la pestaña Edición
                    ColumnLayout {
                        spacing: 16

                        Button {
                            text: "Cargar Imagen"
                            Layout.fillWidth: true
                            Layout.preferredHeight: 48
                            highlighted: true
                            onClicked: fileDialog.open()
                        }

                        Button {
                            text: "Centrar Rostro"
                            Layout.fillWidth: true
                            Layout.preferredHeight: 48
                            onClicked: {
                                var size = sizeComboBox.currentText.split(' - ')[1].split('x')
                                var width = parseFloat(size[0])
                                var height = parseFloat(size[1])
                                imageProcessor.centerFace(width, height, imagePane.width, imagePane.height)
                            }
                        }

                        Label { 
                            text: "Tamaños"
                            font.bold: true
                            font.pixelSize: 16
                        }

                        ComboBox {
                            id: sizeComboBox
                            model: [
                                "Fotocarnet - 3.0cm x 4.0cm",
                                "Estados Unidos - 5.0cm x 5.0cm",
                                "Europa - 3.5cm x 4.5cm",
                                "Italia - 4.0cm x 4.0cm",
                                "China - 3.3cm x 4.8cm",
                                "Brasil - 5.0cm x 7.0cm",
                                "Nautica - 3.0cm x 3.5cm",
                                "Emiratos Árabes - 4.0cm x 6.0cm",
                                "Finlandia - 3.6cm x 4.7cm",
                                "Japón - 3.5cm x 4.6cm",
                                "Nicaragua - 4.0cm x 5.0cm",
                                "India - 3.5cm x 3.5cm",
                                " - 2.5cm x 2.5cm",
                                " - 2.0cm x 2.0cm",
                                " - 2.0cm x 2.3cm",
                                " - 2.0cm x 2.5cm",
                                " - 2.5cm x 2.5cm",
                                " - 2.5cm x 2.9cm",
                                " - 2.5cm x 3.5cm",
                                " - 2.6cm x 3.2cm",
                                " - 2.8cm x 2.8cm",
                                " - 3.0cm x 2.0cm",
                                " - 3.0cm x 3.0cm",
                                " - 3.0cm x 4.5cm",
                                " - 3.0cm x 5.0cm",
                                " - 3.2cm x 2.6cm",
                                " - 3.2cm x 3.6cm",
                                " - 3.5cm x 4.3cm",
                                " - 3.8cm x 4.6cm",
                                " - 4.0cm x 3.5cm",
                                " - 4.0cm x 4.5cm",
                                " - 4.3cm x 3.2cm",
                                " - 4.3cm x 5.5cm",
                                " - 4.5cm x 4.5cm",
                                " - 5.0cm x 3.5cm",
                                " - 5.0cm x 4.0cm",
                                " - 6.0cm x 9.0cm",
                            ]
                            Layout.fillWidth: true
                            Layout.preferredHeight: 48
                            
                            Component.onCompleted: {
                                // Inicializar el tamaño al cargar
                                imageProcessor.setCurrent_photo_size(currentText)
                            }
                            
                            onCurrentTextChanged: {
                                // Actualizar el tamaño de foto en el procesador
                                imageProcessor.setCurrent_photo_size(currentText)
                                
                                // Si hay una imagen centrada, re-centrarla con el nuevo tamaño
                                if (imageProcessor.isCentered && imageProcessor.image) {
                                    var parts = currentText.split(' - ')
                                    var sizeStr = parts.length > 1 ? parts[1] : parts[0]
                                    var dimensions = sizeStr.replace('cm', '').trim().split('x')
                                    var width = parseFloat(dimensions[0])
                                    var height = parseFloat(dimensions[1])
                                    imageProcessor.centerFace(width, height, imagePane.width, imagePane.height)
                                    
                                    // Limpiar el layout anterior cuando se cambia el tamaño
                                    imageProcessor.print_layout = []
                                    imageProcessor.printLayoutChanged.emit()
                                }
                            }
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 5

                            Label { 
                                text: "Insertar datos personales"
                                font.bold: true
                                font.pixelSize: 16
                                Layout.fillWidth: true
                            }

                            Switch {
                                id: textVisibilitySwitch
                                checked: false
                                onCheckedChanged: {
                                    imageProcessor.adjustImageForPersonalData(checked, 0.2)
                                }
                            }
                        }

                        TextField {
                            id: nameField
                            Layout.fillWidth: true
                            Layout.preferredHeight: 48
                            placeholderText: "Nombres"
                            onTextChanged: imageProcessor.name = text
                        }

                        TextField {
                            id: lastNameField
                            Layout.fillWidth: true
                            Layout.preferredHeight: 48
                            placeholderText: "Apellidos"
                            onTextChanged: imageProcessor.lastname = text
                        }

                        TextField {
                            id: rutField
                            Layout.fillWidth: true
                            Layout.preferredHeight: 48
                            placeholderText: "RUT"
                            onTextChanged: imageProcessor.rut = text
                        }

                        // Selector de color de fondo
                        Label {
                            text: "Color de fondo:"
                            font.bold: true
                            font.pixelSize: 14
                        }

                        Row {
                            spacing: 10
                            Layout.alignment: Qt.AlignHCenter

                            Repeater {
                                model: [
                                    { color: "#FFFFFF", name: "Blanco" },
                                    { color: "#E0E0E0", name: "Gris" },
                                    { color: "#87CEEB", name: "Azul" },
                                    { color: "#FF6B6B", name: "Rojo" }
                                ]
                                
                                delegate: Rectangle {
                                    width: 40
                                    height: 40
                                    radius: 20
                                    color: modelData.color
                                    border.width: imageProcessor.backgroundColor === modelData.color ? 3 : 1
                                    border.color: imageProcessor.backgroundColor === modelData.color ? Material.accent : "#666"
                                    
                                    MouseArea {
                                        anchors.fill: parent
                                        cursorShape: Qt.PointingHandCursor
                                        onClicked: {
                                            imageProcessor.backgroundColor = modelData.color
                                        }
                                    }
                                }
                            }
                        }

                        Button {
                            text: "Cambiar Fondo"
                            Layout.fillWidth: true
                            Layout.preferredHeight: 48
                            Material.background: Material.Purple
                            onClicked: {
                                if (imageProcessor.removeBackgroundWithU2Net()) {
                                    console.log("Fondo cambiado exitosamente")
                                } else {
                                    console.log("Error al cambiar el fondo")
                                }
                            }
                            enabled: imageProcessor.isCentered
                        }
                    }

                    // Controles para la pestaña Preparación
                    ColumnLayout {
                        spacing: 16

                        Label {
                            text: "Preparación de Impresión"
                            font.bold: true
                            font.pixelSize: 18
                            Layout.alignment: Qt.AlignHCenter
                        }

                        Rectangle {
                            Layout.preferredHeight: 1
                            Layout.fillWidth: true
                            color: "#ddd"
                        }

                        Button {
                            text: "Ajustar hoja"
                            Layout.fillWidth: true
                            Layout.preferredHeight: 48
                            highlighted: true
                            onClicked: {
                                if (imageProcessor.adjustPrintLayout(printCanvas.width, printCanvas.height)) {
                                    console.log("Layout ajustado correctamente")
                                } else {
                                    console.log("Error al ajustar layout")
                                }
                            }
                            enabled: imageProcessor.isCentered
                        }

                        Label {
                            text: imageProcessor.layout.length > 0 ? 
                                  "✓ " + imageProcessor.layout.length + " fotos preparadas" :
                                  "Sin fotos preparadas"
                            color: imageProcessor.layout.length > 0 ? "green" : "#666"
                            font.pixelSize: 14
                            Layout.alignment: Qt.AlignHCenter
                        }

                        Rectangle {
                            Layout.preferredHeight: 1
                            Layout.fillWidth: true
                            color: "#ddd"
                        }

                        Button {
                            text: "Imprimir"
                            Layout.fillWidth: true
                            Layout.preferredHeight: 48
                            highlighted: true
                            Material.background: Material.Green
                            onClicked: {
                                imageProcessor.printImage()
                                console.log("Enviando a imprimir...")
                            }
                            enabled: imageProcessor.isCentered && 
                                    printerComboBox.currentIndex !== -1 && 
                                    imageProcessor.layout.length > 0
                        }

                        Rectangle {
                            Layout.preferredHeight: 1
                            Layout.fillWidth: true
                            color: "#ddd"
                        }

                        // Información del tamaño actual
                        ColumnLayout {
                            spacing: 8
                            
                            Label {
                                text: "Información:"
                                font.bold: true
                                font.pixelSize: 14
                            }
                            
                            Label {
                                text: "Tamaño: " + sizeComboBox.currentText
                                font.pixelSize: 12
                                color: "#666"
                                wrapMode: Text.WordWrap
                                Layout.fillWidth: true
                            }
                            
                            Label {
                                text: "Papel: 15.2 x 10.2 cm"
                                font.pixelSize: 12
                                color: "#666"
                            }
                            
                            Label {
                                text: imageProcessor.showCutGuides ? 
                                      "✓ Guías de corte habilitadas" :
                                      "✗ Guías de corte deshabilitadas"
                                font.pixelSize: 12
                                color: imageProcessor.showCutGuides ? "green" : "#666"
                            }
                        }

                        Item {
                            Layout.fillHeight: true
                        }
                    }

                    // Controles para la pestaña Ajustes
                    Item {
                        Label {
                            anchors.centerIn: parent
                            text: "Ver pestaña de Ajustes"
                            color: "#666"
                        }
                    }

                    // Controles para la pestaña Acerca de
                    Item {
                        Label {
                            anchors.centerIn: parent
                            text: "Ver pestaña Acerca de"
                            color: "#666"
                        }
                    }
                }
            }
        }
    }
}