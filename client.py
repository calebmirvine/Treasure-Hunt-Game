import logging
import zlib
from struct import unpack, pack
from asyncio import run, StreamReader, StreamWriter, open_connection

from network_functions import (
    HOST,
    PORT,
    FORMAT_MAP,
    receive_decoded_string,
    is_empty_buffer,
    get_player_scores,
)


async def send_row_col_async(writer: StreamWriter) -> None:
    """
    Prompt user for Row and Column input. Validate in loop.
    After validated, pack and write to server.
    :param writer: StreamWriter
    :return: None
    """
    while True:
        row = input("Enter Row (0-15): ")
        col = input("Enter Column (0-15): ")
        if row == '' or col == '':
            print("Input cannot be empty. Please enter valid integers between 0 and 15.")
            continue
        try:
            row_int = int(row)
            col_int = int(col)
        except ValueError:
            print("Invalid input. Please enter integers between 0 and 15.")
            continue

        if 0 <= row_int <= 15 and 0 <= col_int <= 15:
            data = pack("!B", (row_int << 4) | col_int)
            writer.write(data)
            await writer.drain()
            break
        else:
            print("Invalid input. Please enter integers between 0 and 15.")
            continue


async def client_program() -> None:
    """
    Asyncio client program that connects to the server, receives player name.and sends row/column picks in a loop,
    Prints the current score and board after each pick.
    Now receives compressed board data using zlib.
    Displays error message if server is full.
    :return: None
    :raises: Exception if connection or communication fails
    """
    reader, writer = await open_connection(HOST, PORT)

    try:
        name = await receive_decoded_string(reader, '!H')
        if is_empty_buffer(name):
            print("Error: Server is full. Maximum 2 players allowed. Please try again later.")
            writer.close()
            await writer.wait_closed()
            return

        print("Player Name:", name)

        while True:
            await send_row_col_async(writer)

            resp = await reader.readexactly(FORMAT_MAP["!H"])
            if is_empty_buffer(resp):
                logging.error("Empty buffer response...")
                break

            score_data = unpack("!H", resp)[0]
            player1, player2 = get_player_scores(score_data)
            print(f"Current Scores - Player 1: {player1} || Player 2: {player2}")

            board_len_data = await reader.readexactly(FORMAT_MAP["!H"])
            if is_empty_buffer(board_len_data):
                logging.error("Empty buffer response...")
                break

            board_len = unpack("!H", board_len_data)[0]

            compressed_board = await reader.readexactly(board_len)
            if len(compressed_board) < board_len:
                logging.error("Failed to receive board...")
                break

            board_str = zlib.decompress(compressed_board).decode()
            print("\nCurrent Board:")
            print(board_str)
            print()

    except Exception as e:
        logging.error(f"Error in client_program: {e}")
    writer.close()
    await writer.wait_closed()


run(client_program())
