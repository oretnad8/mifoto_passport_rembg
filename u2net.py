import torch
import torch.nn as nn
import torch.nn.functional as F

# Definición completa del modelo U-2-Net
class U2NET(nn.Module):
    def __init__(self, in_channels, out_channels):
        super(U2NET, self).__init__()

        self.encoder1 = self._encoder_block(in_channels, 64)
        self.encoder2 = self._encoder_block(64, 128)
        self.encoder3 = self._encoder_block(128, 256)
        self.encoder4 = self._encoder_block(256, 512)
        self.encoder5 = self._encoder_block(512, 512)

        self.middle = self._bottleneck_block(512, 512)

        self.decoder5 = self._decoder_block(512, 512)
        self.decoder4 = self._decoder_block(512, 256)
        self.decoder3 = self._decoder_block(256, 128)
        self.decoder2 = self._decoder_block(128, 64)
        self.decoder1 = self._decoder_block(64, out_channels)

    def _encoder_block(self, in_channels, out_channels):
        block = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, stride=1, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, stride=1, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2)
        )
        return block

    def _bottleneck_block(self, in_channels, out_channels):
        block = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, stride=1, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, stride=1, padding=1),
            nn.ReLU(inplace=True)
        )
        return block

    def _decoder_block(self, in_channels, out_channels):
        block = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, stride=1, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, stride=1, padding=1),
            nn.ReLU(inplace=True)
        )
        return block

    def forward(self, x):
        # Encoder
        e1 = self.encoder1(x)
        e2 = self.encoder2(e1)
        e3 = self.encoder3(e2)
        e4 = self.encoder4(e3)
        e5 = self.encoder5(e4)

        # Middle
        m = self.middle(e5)

        # Decoder
        d5 = self.decoder5(m)
        d4 = self.decoder4(d5 + e5)
        d3 = self.decoder3(d4 + e4)
        d2 = self.decoder2(d3 + e3)
        d1 = self.decoder1(d2 + e2)

        return d1


# Cargar el modelo U-2-Net desde un archivo
def load_model(model_path):
    device = torch.device('cpu')  # Cargar en CPU
    model = U2NET(3, 1)  # Imagen RGB como entrada, máscara binaria como salida
    model.load_state_dict(torch.load(model_path, map_location=device), strict=False)  # Cargar los pesos con strict=False
    model.eval()  # Configurar el modelo en modo evaluación
    return model
