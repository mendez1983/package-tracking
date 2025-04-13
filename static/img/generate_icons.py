from PIL import Image, ImageDraw, ImageFont
import os

# Asegurarse de que existe el directorio de iconos
icons_dir = os.path.join(os.path.dirname(__file__), 'icons')
os.makedirs(icons_dir, exist_ok=True)

# Tamaños requeridos para los íconos
sizes = [72, 96, 128, 144, 152, 192, 384, 512]

# Colores
background_color = (52, 152, 219)  # Azul (#3498db)
text_color = (255, 255, 255)       # Blanco

for size in sizes:
    # Crear imagen cuadrada con fondo azul
    img = Image.new('RGB', (size, size), color=background_color)
    draw = ImageDraw.Draw(img)
    
    # Dibujar un círculo blanco en el centro
    center = size // 2
    radius = size // 3
    draw.ellipse((center - radius, center - radius, center + radius, center + radius), fill=text_color)
    
    # Dibujar una "P" en el centro (si el tamaño es suficientemente grande)
    if size >= 96:
        try:
            # Intentar cargar una fuente, o usar la fuente por defecto
            try:
                font_size = size // 3
                font = ImageFont.truetype("arial.ttf", font_size)
            except IOError:
                font = ImageFont.load_default()
            
            # Calcular posición de texto
            text = "P"
            text_width = font_size // 2  # Aproximación
            text_height = font_size
            position = (center - text_width, center - text_height // 2)
            
            # Dibujar texto
            draw.text(position, text, fill=background_color, font=font)
        except Exception as e:
            print(f"No se pudo añadir texto al ícono de {size}x{size}: {e}")
    
    # Guardar la imagen
    img.save(os.path.join(icons_dir, f'icon-{size}x{size}.png'))
    print(f"Ícono de {size}x{size} generado")

print("Todos los íconos han sido generados exitosamente.") 