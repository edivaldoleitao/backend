from enum import Enum


class Categories(Enum):
    GPU = ("placa de vídeo", "https://www.kabum.com.br/hardware/placa-de-video-vga")
    CPU = ("processador", "https://www.kabum.com.br/hardware/processadores")
    RAM = ("memória RAM", "https://www.kabum.com.br/hardware/memoria-ram")
    MOTHERBOARD = ("placa mãe", "https://www.kabum.com.br/hardware/placas-mae")
    STORAGE = (
        "armazenamento",
        "https://www.kabum.com.br/hardware/ssd-2-5",
        "https://www.kabum.com.br/hardware/disco-rigido-hd",
    )
    MOUSE = ("mouse", "https://www.kabum.com.br/perifericos/-mouse-gamer")
    KEYBOARD = ("teclado", "https://www.kabum.com.br/perifericos/teclado-gamer")
    MONITOR = ("monitor", "https://www.kabum.com.br/computadores/monitores")
    COMPUTER = (
        "computador",
        "https://www.kabum.com.br/computadores/pc",
        "https://www.kabum.com.br/computadores/notebooks",
    )

    @property
    def query(self):
        return self.value[0]

    @property
    def url(self):
        return self.value[1]

    @property
    def url_2(self):
        if len(self.value) > 2:
            return self.value[2]
        return None
