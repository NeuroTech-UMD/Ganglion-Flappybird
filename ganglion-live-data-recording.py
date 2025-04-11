from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
import keyboard
import numpy as np
import time

POLL_TIME = 0.1

def check_key_press(seconds):
    start_time = time.time()
    key_pressed = 0
    while time.time() - start_time < seconds:
        if keyboard.is_pressed(hotkey="space"):  # Check if ANY key is pressed in each loop
            key_pressed = 1
        if keyboard.is_pressed(hotkey='esc'):
            return 2
        time.sleep(POLL_TIME/10) # Small pause
    if key_pressed == 1:
        print("KYS")
    return key_pressed    

def main():
    BoardShim.enable_dev_board_logger()

    params = BrainFlowInputParams()
    #params.serial_port = "/dev/cu.usbmodem11"
    params.mac_address = "cc:46:26:d7:24:38" # Removed .upper() and kept lowercase
    params.timeout = 30 # Added timeout
    board = BoardShim(BoardIds.GANGLION_NATIVE_BOARD, params) # Changed to GANGLION_BOARD
    eeg_data = []
    keyboard_data = []
    try: # Added try-except block for error handling
        board.prepare_session()
        board.start_stream()
        while True:
            keypress = check_key_press(POLL_TIME)
            if keypress == 2:
                break
            keyboard_data.append(keypress)
            # data = board.get_current_board_data (256) # get latest 256 packages or less, doesnt remove them from internal buffer
            data = board.get_board_data()  # get all data and remove it from internal buffer
            eeg_data.append(data)
        board.stop_stream()
        arr = np.array(eeg_data)
        keyboard_data = np.array(keyboard_data)
        np.savez_compressed(f"eeg_data_{int(time.time())}.npz", eeg_data=arr, keyboard_data=keyboard_data)
        if board.is_prepared(): # Ensure session is released even if error occurs
            board.release_session()

    except Exception as e:
        print(f"Error: {e}") # Print specific error message
        board.stop_stream()
        arr = np.array(eeg_data)
        keyboard_data = np.array(keyboard_data)
        np.savez_compressed(f"eeg_data_{int(time.time())}.npz", eeg_data=arr, keyboard_data=keyboard_data)
        if board.is_prepared(): # Ensure session is released even if error occurs
            board.release_session()

if __name__ == "__main__":
    main()
