from asyncio import StreamReader, StreamWriter
from socket import socket
from struct import unpack, pack

HOST = ''  # IP address of server (StreamReader)
PORT = 12345  # Port to listen on (StreamWriter)
FORMAT_MAP = {
    '!H': 2,  # 2 bytes for unsigned short
    '!B': 1,  # 1 byte for unsigned char
}
OUT_OF_BOUNDS = 0b1100000000000000  # Bit 15 and 14 set constant to indicate out of bounds error


def is_empty_buffer(byte: str | int | bytes) -> bool:
    """
    Check if a buffer is empty (empty bytes, empty string, or 0).

    :param byte: The data to check
    :return bool: True if empty, False otherwise
    """
    return byte == b'' or byte == '' or byte == 0


def byte_segment_to_space(data: int) -> tuple[int, int]:
    """
    Extract row and column from a packed byte.
    Row is stored in upper 4 bits (bits 7-4), column in lower 4 bits (bits 3-0).
    Uses bit masking: 0b11110000  for row, 0b1111 for column.

    :param data: Packed byte containing row and column (row << 4 | col)
    :return int: Tuple of (row, col) where both are in range [0-15]
    :raises ValueError: if data is negative
    """
    if data < 0: raise ValueError("data must be >= 0")
    return ((data & 0b11110000) >> 4), (data & 0b1111)


def score_into_byte(score: int) -> int:
    """
    Mask score to fit in 7 bits (max value 127).

    :param score: Player's score (should be non-negative)
    :return: The Score masked to 7 bits as an integer
    :raises ValueError: if score is negative
    """
    if score < 0: raise ValueError("score must be >= 0")
    return score & 0b1111111


def get_player_scores(byte: int) -> tuple[int, int]:
    """
    Extract both player scores from a packed 2 byte integer.
    Player 1 score is in bits 14-8 (7 bits), Player 2 score is in bits 6-0 (7 bits).
    Uses bit masks: 0b11111110000000 for player 1, 0b1111111 for player 2.

    :param byte: Packed integer containing both scores (player1 << 7 | player2)
    :return: Tuple of (player1_score, player2_score)
    :raises ValueError: if byte is negative
    """
    if byte < 0: raise ValueError("byte must be >= 0")
    return (byte & 0b11111110000000) >> 7, byte & 0b1111111


def receive(sc: socket, size: int) -> bytes:
    """
    Receive exactly 'size' bytes from a socket.
    Loops until all bytes are received or connection is closed.

    :param sc: Socket to receive from
    :param size: Number of bytes to receive
    :return: Bytes received
    :raises ValueError: if size is negative or sc is None
    """
    if size < 0: raise ValueError("size must be >= 0")
    if sc is None: raise ValueError("sc must be a socket")
    data = b''
    while len(data) < size:
        curr_data = sc.recv(size - len(data))
        if is_empty_buffer(curr_data):
            return data
        data += curr_data
    return data


async def receive_decoded_string(reader: StreamReader, flag: str) -> str:
    """
    Receive a length and a string from reader asyncio StreamReader.
    First receives the length, based on the flag, then receives and decodes that given length in bytes.
    This length allows us to know exactly how much data to read.
    :param reader: asyncio StreamReader to read from
    :param flag: format flag for the length prefix
    :return: Decoded string, or empty string if insufficient data received
    :raises ValueError: if flag is not a valid format flag or length prefix is not two bytes
    :raises ValueError: if reader is None
    """
    if type(flag) != str: raise ValueError("flag must be a string")
    if flag not in FORMAT_MAP: raise ValueError("flag must be a valid format flag")
    if len(flag) != 2: raise ValueError("flag must be a two character format flag")
    if reader is None: raise ValueError("reader must be a asyncio StreamReader")

    exp_len = FORMAT_MAP.get(flag)
    recv_len = await reader.readexactly(exp_len)
    if len(recv_len) < exp_len:
        return ''
    str_len = unpack(flag, recv_len)[0]
    recv_str = await reader.readexactly(str_len)
    if len(recv_str) < str_len:
        return ''
    return recv_str.decode()


def validate_row_col(row: str | int, col: str | int) -> bool:
    """
    Validate that row and column are within valid range [0-15] and valid integers.
    Accepts both string and int inputs, if not valid integers, returns False.
    :param row: Row value as string or int
    :param col: Column value as string or int
    :return: True if both values are integers in range [0-15], False otherwise
    :raises ValueError: if row or col is not an int
    """
    try:
        row_int = int(row)
        col_int = int(col)
    except (TypeError, ValueError):
        return False
    return 0 <= row_int <= 15 and 0 <= col_int <= 15


def send_row_col(writer: StreamWriter) -> None:
    """
    Prompt user for Row and Column input, validate, pack and send to server.
    :param writer: asyncio StreamWriter
    :return: None
    :raises ValueError: if input is invalid or packing fails
    """
    while True:
        row = input("Enter Row (0-15): ")
        col = input("Enter Column (0-15): ")
        if row == '' or col == '':
            print("Input cannot be empty. Please enter valid integers between 0 and 15.")
            continue
        if validate_row_col(row, col):
            pack_and_write_data(writer, "!B", (int(row) << 4) | int(col))
            break
        else:
            print("Invalid input. Please enter integers between 0 and 15.")
            continue


async def pack_and_write_data(writer: StreamWriter, flag: str, data: int) -> None:
    """
    Pack integer data with the given format flag and send write with asyncio StreamWriter.
    :param writer: asyncio StreamWriter to write packed data to
    :param flag: format flag for sizing packing
    :param data: Integer data to pack and send
    :return: None
    :raises ValueError: if packing or writing fails
    """
    try:
        packed_data = pack(flag, data)
        writer.write(packed_data)
        await writer.drain()
    except Exception as e:
        raise ValueError(f"Failed to pack and write data: {e}")


async def encode_and_write_data(writer: StreamWriter, flag: str, string: str) -> None:
    """
    Encode and send a string with length prefix for efficiency.
    First sends the length of the string, packed according to flag, then sends encoded string.
    The length prefix allows the receiver to know exactly how many bytes to read, allowing for efficient buffering.

    :param writer: asyncio StreamWriter to write data
    :param flag: format flag for the length prefix (i.e. '!H' for 2 byte unsigned short)
    :param string: String data to encode and send
    :return: None
    :raises ValueError: if encoding or writing fails
    """
    try:
        length_data = pack(flag, len(string))
        writer.write(length_data)
        writer.write(string.encode())
        await writer.drain()
    except Exception as e:
        raise ValueError(f"Failed to write and send data: {e}")
