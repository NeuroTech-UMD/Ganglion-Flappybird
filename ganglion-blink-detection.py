import time
import numpy as np
import keyboard # Added for keyboard control
from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds, BrainFlowError

# --- Configuration ---
BOARD_ID = BoardIds.GANGLION_NATIVE_BOARD # Or GANGLION_BOARD if using BLED112 Dongle
PARAMS = BrainFlowInputParams()
# PARAMS.serial_port = "/dev/cu.usbmodem11" # Uncomment if using serial
PARAMS.mac_address = "cc:46:26:d7:24:38"   # Use your Ganglion's MAC address
PARAMS.timeout = 15                       # Reduced timeout slightly

# --- EEG Processing Parameters ---
# VERY IMPORTANT: You WILL need to tune this threshold value!
# Start high (e.g., 100-200) and decrease if no blinks are detected.
# Increase if it triggers too easily on noise.
# Units are likely microvolts (uV) - check Brainflow docs for your board.
BLINK_THRESHOLD = 80.0 # uV - *** TUNE THIS VALUE ***

# Which EEG channel to monitor (0-indexed based on get_eeg_channels list)
# Ganglion usually has channels 1-4. get_eeg_channels returns indices [1, 2, 3, 4]
# So index 0 corresponds to the *first* EEG channel (BoardShim channel 1).
# Try channels near the front if possible for better blink detection.
EEG_CHANNEL_INDEX = 0 # Monitor the first EEG channel

# Cooldown period (in seconds) after a blink is detected to prevent rapid firing
COOLDOWN_PERIOD = 0.7

# --- Global State ---
last_blink_time = 0

def main():
    global last_blink_time # Allow modification of global variable

    BoardShim.enable_dev_board_logger()

    board = BoardShim(BOARD_ID, PARAMS)
    eeg_channels = [] # Initialize

    try:
        print("Preparing session...")
        board.prepare_session()
        print("Session prepared.")

        # Dynamically get EEG channel indices and sample rate
        eeg_channels = BoardShim.get_eeg_channels(BOARD_ID)
        sampling_rate = BoardShim.get_sampling_rate(BOARD_ID)
        print(f"Board: {BoardShim.get_board_descr(BOARD_ID)}")
        print(f"EEG Channels: {eeg_channels}")
        print(f"Sampling Rate: {sampling_rate} Hz")

        if not eeg_channels:
             raise BrainFlowError("Could not get EEG channels for this board.")
        if EEG_CHANNEL_INDEX >= len(eeg_channels):
            raise IndexError(f"Selected EEG_CHANNEL_INDEX {EEG_CHANNEL_INDEX} is out of bounds for available channels {eeg_channels}")

        # Map the logical index (0) to the actual board channel number
        target_channel = eeg_channels[EEG_CHANNEL_INDEX]
        print(f"Monitoring BrainFlow channel index: {target_channel} (Logical index {EEG_CHANNEL_INDEX})")


        print("Starting stream...")
        board.start_stream(450000, 'file://data.csv:a') # Start stream, optionally log to file
        print("Stream started. Waiting for data...")
        time.sleep(2) # Wait a bit for buffer to fill

        print("\n--- Ready to detect blinks! ---")
        print(f"--- Monitoring Channel {target_channel} for values exceeding +/-{BLINK_THRESHOLD} uV ---")
        print("--- Press Ctrl+C to stop ---")


        while True:
            # Get only new data since last call
            data = board.get_board_data()

            if data.shape[1] > 0:
                # Get data for the specific EEG channel we are monitoring
                # data[target_channel] accesses the row corresponding to our channel
                channel_data = data[target_channel]

                # Check if the *absolute* value of any new sample exceeds the threshold
                # We check absolute value because blinks can cause positive or negative spikes
                if np.any(np.abs(channel_data) > BLINK_THRESHOLD):
                    current_time = time.time()
                    # Check if cooldown period has passed
                    if current_time - last_blink_time > COOLDOWN_PERIOD:
                        print(f"Blink detected! Max value: {np.max(np.abs(channel_data)):.2f} uV. Pressing SPACE.")
                        try:
                            keyboard.press_and_release('space')
                            last_blink_time = current_time # Update last blink time
                        except Exception as key_err:
                             # May fail if window doesn't have focus or due to permissions
                             print(f"  > Warning: Could not press spacebar: {key_err}")
                    # else:
                    #    print("Blink detected within cooldown period, skipping.") # Optional: for debugging

            # Small sleep to prevent high CPU usage in the loop if no data arrives
            time.sleep(0.05) # 50 ms sleep

    except KeyboardInterrupt:
        print("\nCtrl+C detected. Stopping...")
    except BrainFlowError as e:
        print(f"BrainFlow Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        print("Releasing session...")
        if board.is_prepared():
            try:
                board.stop_stream()
                print("Stream stopped.")
            except BrainFlowError as e:
                print(f"Error stopping stream: {e}")
            try:
                board.release_session()
                print("Session released.")
            except BrainFlowError as e:
                print(f"Error releasing session: {e}")
        else:
             print("Board was not prepared, no session to release.")
        print("Exiting.")


if __name__ == "__main__":
    # IMPORTANT: You might need root/admin privileges for the keyboard library!
    # On Linux/macOS: sudo python your_script_name.py
    # On Windows: Run your terminal/IDE as Administrator
    main()