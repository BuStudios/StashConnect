from PIL import Image
import base64
import io

with Image.open("testing/files/glass.jpeg") as img:
    aspect_ratio = img.height / img.width
    new_height = int(512 * aspect_ratio)

    img = img.resize((512, new_height), Image.Resampling.LANCZOS)

    # basically saves the file to memory instead of a file
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")

    img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

print(img_base64[:300])