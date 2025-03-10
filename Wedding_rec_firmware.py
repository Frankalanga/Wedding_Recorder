import machine
import time
import uos
import sdcard

# Configuración del ADC externo (simulado como un pin ADC)
adc = machine.ADC(26)

# Configuración del switch
switch = machine.Pin(15, machine.Pin.IN, machine.Pin.PULL_UP)

# Configuración de la tarjeta SD
cs = machine.Pin(17, machine.Pin.OUT)
spi = machine.SPI(0, baudrate=1000000, polarity=0, phase=0, bits=8, firstbit=machine.SPI.MSB, sck=machine.Pin(18),
                  mosi=machine.Pin(19), miso=machine.Pin(16))
sd = sdcard.SDCard(spi, cs)
uos.mount(sd, "/sd")

# Parámetros de audio
sample_rate = 44100  # 44.1 kHz (calidad CD)
bits_per_sample = 16  # 16 bits por muestra
num_channels = 1  # Mono
duration = 10  # Duración de la grabación en segundos


# Función para generar el encabezado WAV
def generate_wav_header(data_size):
    byte_rate = sample_rate * num_channels * bits_per_sample // 8
    block_align = num_channels * bits_per_sample // 8
    header = bytearray()
    header.extend(b"RIFF")  # Chunk ID
    header.extend((data_size + 36).to_bytes(4, 'little'))  # Chunk Size
    header.extend(b"WAVE")  # Format
    header.extend(b"fmt ")  # Subchunk1 ID
    header.extend((16).to_bytes(4, 'little'))  # Subchunk1 Size
    header.extend((1).to_bytes(2, 'little'))  # Audio Format (PCM)
    header.extend((num_channels).to_bytes(2, 'little'))  # Number of Channels
    header.extend((sample_rate).to_bytes(4, 'little'))  # Sample Rate
    header.extend((byte_rate).to_bytes(4, 'little'))  # Byte Rate
    header.extend((block_align).to_bytes(2, 'little'))  # Block Align
    header.extend((bits_per_sample).to_bytes(2, 'little'))  # Bits per Sample
    header.extend(b"data")  # Subchunk2 ID
    header.extend((data_size).to_bytes(4, 'little'))  # Subchunk2 Size
    return header


# Función para grabar audio en formato WAV
def record_audio_wav(filename, duration):
    data_size = sample_rate * duration * num_channels * bits_per_sample // 8
    header = generate_wav_header(data_size)

    with open(filename, "wb") as f:
        f.write(header)  # Escribir el encabezado WAV
        start_time = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start_time) < duration * 1000:
            sample = adc.read_u16()  # Leer muestra del ADC
            f.write(sample.to_bytes(2, 'little'))  # Escribir los datos de audio


# Bucle principal
while True:
    if switch.value() == 0:  # Switch cerrado (circuito cerrado)
        print("Grabando...")
        filename = "/sd/recording_{}.wav".format(time.time())
        record_audio_wav(filename, duration)  # Graba durante 10 segundos
        print("Grabación guardada en {}".format(filename))
        time.sleep(1)  # Debounce