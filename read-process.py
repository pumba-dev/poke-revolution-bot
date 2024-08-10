import ctypes
import psutil
import pymem
import pymem.process
from ctypes import wintypes
import time
import ctypes

# Definindo constantes
PROCESS_ALL_ACCESS = 0x1F0FFF

# Funções da API do Windows
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

OpenProcess = kernel32.OpenProcess
OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
OpenProcess.restype = wintypes.HANDLE

ReadProcessMemory = kernel32.ReadProcessMemory
ReadProcessMemory.argtypes = [
    wintypes.HANDLE,
    wintypes.LPCVOID,
    wintypes.LPVOID,
    ctypes.c_size_t,
    ctypes.POINTER(ctypes.c_size_t),
]
ReadProcessMemory.restype = wintypes.BOOL

WriteProcessMemory = kernel32.WriteProcessMemory
WriteProcessMemory.argtypes = [
    wintypes.HANDLE,
    wintypes.LPVOID,
    wintypes.LPCVOID,
    ctypes.c_size_t,
    ctypes.POINTER(ctypes.c_size_t),
]
WriteProcessMemory.restype = wintypes.BOOL

PROCESS_ALL_ACCESS = 0x1F0FFF

# Definição das funções da API do Windows
OpenProcess = ctypes.windll.kernel32.OpenProcess
ReadProcessMemory = ctypes.windll.kernel32.ReadProcessMemory
CloseHandle = ctypes.windll.kernel32.CloseHandle


def find_process_id_by_name(process_name):
    for proc in psutil.process_iter(["pid", "name"]):
        if proc.info["name"] == process_name:
            return proc.info["pid"]
    return None


def read_process_memory(pid, address, size):
    hProcess = OpenProcess(PROCESS_ALL_ACCESS, False, pid)
    if not hProcess:
        print("Não foi possível abrir o processo")
        return None

    buffer = ctypes.create_string_buffer(size)
    bytesRead = ctypes.c_size_t(0)

    if not ReadProcessMemory(
        hProcess, ctypes.c_void_p(address), buffer, size, ctypes.byref(bytesRead)
    ):
        print("Falha na leitura da memória")
        CloseHandle(hProcess)
        return None

    CloseHandle(hProcess)
    return buffer.raw


def search_bytes_in_memory(pid, start_address, end_address, byte_sequence):
    # Defina um tamanho de leitura adequado
    block_size = 4096
    byte_sequence = bytes(byte_sequence)
    address = start_address

    while address < end_address:
        size = min(block_size, end_address - address)
        data = read_process_memory(pid, address, size)
        if data:
            index = data.find(byte_sequence)
            if index != -1:
                print(f"Sequência encontrada no endereço: {hex(address + index)}")
        address += block_size


def get_enemy_pokemon_name(pid):
    start_address = 0x21BCD6C24E6  # Endereço de início para a pesquisa
    end_address = 0x21BCD6C251E  # Endereço de fim para a pesquisa
    byte_sequence = [
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x21,
        0x00,
        0x00,
        0x00,
        0x50,
        0x00,
        0x68,
        0x00,
        0x75,
        0x00,
        0x6D,
        0x00,
        0x61,
        0x00,
        0x65,
        0x00,
        0x72,
        0x00,
        0x76,
        0x00,
        0x61,
        0x00,
        0x20,
        0x00,
        0x20,
        0x00,
        0x20,
        0x00,
        0x20,
        0x00,
        0x5B,
        0x00,
        0x56,
        0x00,
        0x53,
        0x00,
        0x5D,
        0x00,
        0x20,
        0x00,
        0x20,
        0x00,
        0x20,
        0x00,
        0x20,
        0x00,
        0x57,
        0x00,
        0x69,
        0x00,
        0x6C,
        0x00,
        0x64,
        0x00,
        0x20,
        0x00,
        0x53,
        0x00,
        0x65,
        0x00,
        0x6E,
        0x00,
        0x74,
        0x00,
        0x72,
        0x00,
        0x65,
        0x00,
        0x74,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0xB0,
    ]
    search_bytes_in_memory(pid, start_address, end_address, byte_sequence)


def main():
    process_name = "PROClient.exe"
    pid = find_process_id_by_name(process_name)

    if not pid:
        print(f"Processo '{process_name}' não encontrado.")
        return

    print(f"Processo '{process_name}' encontrado com PID: {pid}")

    # Exemplo de endereço para leitura (você precisa saber os endereços específicos do jogo)
    addressList = [0x21B56ABA014]

    while True:
        for address in addressList:
            memory_data = read_process_memory(pid, address, 4)
            if memory_data:
                print(f"Hex:: 0x{address}: {memory_data}")
            time.sleep(1)


if __name__ == "__main__":
    main()
