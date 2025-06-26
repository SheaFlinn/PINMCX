import os
from PIL import Image, ImageDraw, ImageFont

# Create icons directory if it doesn't exist
icons_dir = 'static/icons'
os.makedirs(icons_dir, exist_ok=True)

# Define icon sizes
sizes = [
    (192, 192),
    (512, 512)
]

# Create MCX logo icon
def create_icon(size):
    width, height = size
    
    # Create a white background
    icon = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(icon)
    
    # Draw MCX logo (you can customize this to match your actual logo)
    # For now, we'll create a simple "MCX" text logo
    try:
        # Try to use a system font
        font = ImageFont.truetype("Arial.ttf", int(width * 0.4))
    except:
        # Fallback to default font if Arial is not available
        font = ImageFont.load_default()
    
    # Calculate text position
    text = "MCX"
    text_width, text_height = draw.textsize(text, font=font)
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    
    # Draw text
    draw.text((x, y), text, font=font, fill='#0d6efd')
    
    return icon

# Generate icons
for size in sizes:
    icon = create_icon(size)
    filename = f'icon-{size[0]}x{size[1]}.png'
    icon.save(os.path.join(icons_dir, filename))
    print(f'Created {filename}')

print('PWA icons generation complete!')
