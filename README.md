# txt2img
Converts text files to a single image (useful for DeepSeek OCR prompt input)

# Required dependencies

`pip install Pillow`

# Usage

Simple (create a `txt2img.py` file with following code): 
```
from TextToImageConverter import TextToImageConverter

converter = TextToImageConverter()
converter.convert_folder_to_image("./", "output.png")
```

Customized (create a `txt2img.py` file with following code): 
```
from TextToImageConverter import TextToImageConverter

converter = TextToImageConverter()
converter.convert_folder_to_image("./", "output2.png", columns=4, balance_columns=False)
```

Advanced (create a `txt2img.py` file with following code): 
```
from TextToImageConverter import TextToImageConverter

converter = TextToImageConverter(
    font_size=12,
    line_spacing=2,
    padding=20,
    border_width=3,
    max_width=1500,
    background_color='white',
    text_color='black',
    border_color='black',
    filename_color='blue'
)
converter.convert_folder_to_image("./", "result.tiff", columns=4, output_format='TIFF', chars_per_line=100, balance_columns=False,)
```

# Run script

`python txt2img.py`


