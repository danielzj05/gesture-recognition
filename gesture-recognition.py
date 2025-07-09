import serial
import time
import keyboard

arduino = serial.Serial('COM3', 250000, timeout=0.05)
time.sleep(2)

print("Press keys 1-5 to select LED. Use ↑ / ↓ to adjust brightness. Press Esc to quit.")

selected_led = None
last_selected_led = None
last_command_time = 0
command_delay = 0.1  # 100 ms delay between commands

try:
    while True:
        now = time.time()

        # Only check LED selection if no arrow key is being held
        for key in ['1', '2', '3', '4', '5']:
            if keyboard.is_pressed(key) and not (keyboard.is_pressed('up') or keyboard.is_pressed('down')):
                selected_led = key
                break  # pick only one key at a time

        # Send LED selection once
        if selected_led and selected_led != last_selected_led:
            print(f"Selecting LED {selected_led}")
            arduino.write(selected_led.encode())
            last_selected_led = selected_led
            time.sleep(0.01)

        # Send brightness changes every delay interval
        if now - last_command_time > command_delay:
            if keyboard.is_pressed('up'):
                print("Increasing brightness")
                arduino.write(b'U')
                last_command_time = now
            elif keyboard.is_pressed('down'):
                print("Decreasing brightness")
                arduino.write(b'D')
                last_command_time = now

        # Optional: read Arduino response
        try:
            response = arduino.readline().decode().strip()
            if response:
                print("Arduino:", response)
        except:
            pass

        if keyboard.is_pressed('esc'):
            break

except KeyboardInterrupt:
    print("\nExiting.")
finally:
    arduino.close()