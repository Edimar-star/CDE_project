import time

start_time = time.time()

# --- Aquí va tu código ---
time.sleep(2)  # Simula un código que tarda 123 segundos
# -------------------------

end_time = time.time()
total_time = end_time - start_time

minutes = int(total_time // 60)
seconds = int(total_time % 60)

print(f"El programa se ejecutó en {minutes}m y {seconds}s")