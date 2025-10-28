import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import textwrap
from typing import List, Tuple

class TextToImageConverter:
    def __init__(self, 
                 font_size: int = 12,
                 line_spacing: int = 2,
                 padding: int = 20,
                 border_width: int = 3,
                 max_width: int = 1200,          # per-column content width in pixels
                 background_color: str = 'white',
                 text_color: str = 'black',
                 border_color: str = 'black',
                 filename_color: str = 'blue',
                 column_spacing: int = 24,       # spacing between columns
                 section_spacing: int = 12):     # vertical spacing between file sections
        
        self.font_size = font_size
        self.line_spacing = line_spacing
        self.padding = padding
        self.border_width = border_width
        self.max_width = max_width
        self.background_color = background_color
        self.text_color = text_color
        self.border_color = border_color
        self.filename_color = filename_color
        self.column_spacing = column_spacing
        self.section_spacing = section_spacing
        
        # Try to load a monospace font
        try:
            self.font = ImageFont.truetype("DejaVuSansMono.ttf", font_size)
            self.header_font = ImageFont.truetype("DejaVuSansMono-Bold.ttf", font_size + 2)
        except:
            try:
                self.font = ImageFont.truetype("consolas.ttf", font_size)
                self.header_font = ImageFont.truetype("consolab.ttf", font_size + 2)
            except:
                try:
                    self.font = ImageFont.truetype("courier.ttf", font_size)
                    self.header_font = ImageFont.truetype("courbd.ttf", font_size + 2)
                except:
                    self.font = ImageFont.load_default()
                    self.header_font = ImageFont.load_default()

    def _char_width(self) -> int:
        bbox = self.font.getbbox('M')
        return bbox[2] - bbox[0]

    def get_text_files(self, folder_path: str) -> List[Path]:
        """Recursively find all text files in the given folder."""
        text_extensions = {
            '.txt', '.java', '.php', '.css', '.xml', '.json',
            '.js', '.py', '.html', '.htm', '.c', '.cpp', '.h',
            '.hpp', '.cs', '.sql', '.md', '.yml', '.yaml', '.ini'
        }
        folder = Path(folder_path)
        text_files = []
        for file_path in folder.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in text_extensions:
                text_files.append(file_path)
        return sorted(text_files)

    def read_file_content(self, file_path: Path) -> str:
        """Read file content with proper encoding handling."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    return f.read()
            except Exception as e:
                return f"Error reading file: {str(e)}"

    def _wrap_text_by_pixels(self, text: str, available_text_width_px: int) -> Tuple[int, int, list]:
        """
        Wraps text into lines that fit available_text_width_px using monospaced font heuristics.
        Returns (content_width, total_height, wrapped_lines).
        """
        char_w = self._char_width()
        # Ensure at least 8 chars per line to avoid degenerate layout
        chars_per_line = max(8, int(available_text_width_px // max(1, char_w)))

        lines = text.split('\n')
        wrapped_lines = []
        for line in lines:
            if len(line) <= chars_per_line:
                wrapped_lines.append(line)
            else:
                wrapped_lines.extend(textwrap.wrap(line, width=chars_per_line, replace_whitespace=False))

        line_height = self.font_size + self.line_spacing
        height = len(wrapped_lines) * line_height + self.padding * 2
        content_width = chars_per_line * char_w + self.padding * 2
        return content_width, height, wrapped_lines

    def create_file_section(self, file_path: Path, content: str, content_width_px: int = None, chars_per_line: int = None) -> Image.Image:
        """
        Create an image section for a single file.
        - If content_width_px is provided, wrap text to fit that width (recommended for columns).
        - Else, if chars_per_line is provided, wrap by characters and compute width.
        - Else, default to chars_per_line=100 behavior.
        """
        if content_width_px is not None:
            available_text_width = max(1, content_width_px - self.padding * 2)
            content_w, text_height, wrapped_lines = self._wrap_text_by_pixels(content, available_text_width)
            # Total width includes borders
            total_content_width = content_width_px + self.border_width * 2
            text_area_width = content_width_px
        else:
            # Fallback: derive width from chars_per_line
            if chars_per_line is None:
                chars_per_line = 100
            char_w = self._char_width()
            available_text_width = chars_per_line * char_w
            content_w, text_height, wrapped_lines = self._wrap_text_by_pixels(content, available_text_width)
            total_content_width = min(content_w, self.max_width) + self.border_width * 2
            text_area_width = min(content_w, self.max_width)

        # Add space for filename header
        header_height = self.font_size + 10
        total_height = text_height + header_height + self.border_width * 2

        # Create image
        img = Image.new('RGB', (total_content_width, total_height), self.background_color)
        draw = ImageDraw.Draw(img)

        # Draw border
        draw.rectangle([0, 0, total_content_width - 1, total_height - 1],
                       outline=self.border_color, width=self.border_width)

        # Draw filename header (use relative path string if provided)
        rel_path_str = str(file_path)
        draw.text((self.padding + self.border_width, self.border_width + 5),
                  f"📄 {rel_path_str}", fill=self.filename_color, font=self.header_font)

        # Separator line
        y_separator = header_height + self.border_width
        draw.line([(self.border_width, y_separator),
                   (total_content_width - self.border_width, y_separator)],
                  fill=self.border_color, width=1)

        # Draw text content
        y_offset = y_separator + self.padding
        line_height = self.font_size + self.line_spacing
        for line in wrapped_lines:
            draw.text((self.padding + self.border_width, y_offset),
                      line, fill=self.text_color, font=self.font)
            y_offset += line_height

        return img

    def combine_images_vertically(self, images: List[Image.Image]) -> Image.Image:
        """Combine multiple images vertically into one."""
        if not images:
            return Image.new('RGB', (100, 100), self.background_color)
        max_width = max(img.width for img in images)
        total_height = sum(img.height for img in images) + self.section_spacing * (len(images) - 1)
        combined = Image.new('RGB', (max_width, total_height), self.background_color)
        y = 0
        for i, img in enumerate(images):
            combined.paste(img, (0, y))
            y += img.height
            if i < len(images) - 1:
                y += self.section_spacing
        return combined

    def combine_images_in_columns(self, images: List[Image.Image], columns: int,
                                  balance_columns: bool = True) -> Image.Image:
        """
        Arrange images in N columns.
        - If balance_columns=True, uses a greedy 'masonry' layout to minimize total height.
        - If False, preserves order: fills column 0 top-to-bottom, then column 1, etc.
        """
        if not images:
            return Image.new('RGB', (100, 100), self.background_color)
        if columns <= 1:
            return self.combine_images_vertically(images)

        # Determine column width (use the max width; ideally all sections have same width)
        col_width = max(img.width for img in images)

        # Prepare columns
        cols = [{'height': 0, 'imgs': []} for _ in range(columns)]

        if balance_columns:
            # Greedy placement to the shortest column
            for img in images:
                target = min(cols, key=lambda c: c['height'])
                target['imgs'].append(img)
                # Add section height + spacing (except not after last, handled later)
                target['height'] += img.height + self.section_spacing
            # Adjust heights by removing last spacing in each column
            for c in cols:
                if c['imgs']:
                    c['height'] -= self.section_spacing
        else:
            # Preserve order across columns
            for idx, img in enumerate(images):
                c = cols[idx % columns]
                c['imgs'].append(img)
            # Compute heights
            for c in cols:
                if c['imgs']:
                    c['height'] = sum(i.height for i in c['imgs']) + self.section_spacing * (len(c['imgs']) - 1)

        total_width = columns * col_width + (columns - 1) * self.column_spacing
        total_height = max(c['height'] for c in cols) if cols else 0
        total_height = max(1, total_height)  # avoid zero height

        combined = Image.new('RGB', (total_width, total_height), self.background_color)

        # Paste columns
        x = 0
        for c in cols:
            y = 0
            for i, img in enumerate(c['imgs']):
                combined.paste(img, (x, y))
                y += img.height
                if i < len(c['imgs']) - 1:
                    y += self.section_spacing
            x += col_width + self.column_spacing

        return combined

    def convert_folder_to_image(self, folder_path: str, output_path: str, 
                                chars_per_line: int = 100,
                                columns: int = 1,
                                balance_columns: bool = True,
                                output_format: str = 'PNG') -> None:
        """
        Convert all text files in a folder to a single image.
        - columns: number of columns (1 = original single column)
        - balance_columns: when columns > 1, balance heights (True) or preserve order (False)
        - For columns > 1, per-column content width uses self.max_width
        """
        print(f"Scanning folder: {folder_path}")
        text_files = self.get_text_files(folder_path)
        if not text_files:
            print("No text files found!")
            return
        print(f"Found {len(text_files)} text files")

        images = []
        for i, file_path in enumerate(text_files, 1):
            print(f"Processing {i}/{len(text_files)}: {file_path}")
            try:
                content = self.read_file_content(file_path)
                relative_path = file_path.relative_to(Path(folder_path))
                if columns > 1:
                    # Use fixed per-column content width for consistent columns
                    img = self.create_file_section(relative_path, content, content_width_px=self.max_width)
                else:
                    img = self.create_file_section(relative_path, content, content_width_px=None, chars_per_line=chars_per_line)
                images.append(img)
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
                continue

        if not images:
            print("No images created!")
            return

        print("Combining images...")
        if columns > 1:
            final_image = self.combine_images_in_columns(images, columns=columns, balance_columns=balance_columns)
        else:
            final_image = self.combine_images_vertically(images)

        print(f"Saving to: {output_path}")
        if output_format.upper() == 'PNG':
            final_image.save(output_path, format='PNG', optimize=True)
        elif output_format.upper() in ('TIFF', 'TIF'):
            final_image.save(output_path, format='TIFF', compression='tiff_lzw')
        else:
            final_image.save(output_path, format=output_format.upper())
        print(f"Image saved successfully! Dimensions: {final_image.width}x{final_image.height}")

def main():
    """Interactive usage"""
    converter = TextToImageConverter(
        font_size=10,
        line_spacing=1,
        padding=15,
        border_width=2,
        max_width=700,          # per-column content width
        column_spacing=24,
        section_spacing=12
    )

    folder_path = input("Enter the folder path to scan: ").strip() or "."
    if not os.path.exists(folder_path):
        print(f"Error: Folder '{folder_path}' does not exist!")
        return

    output_path = input("Enter output image path (default: output.png): ").strip() or "output.png"

    # Columns
    try:
        columns = int(input("Number of columns (default: 1): ").strip() or "1")
    except ValueError:
        columns = 1

    # Preserve order or balance
    bal = input("Balance column heights? y/N (default: y): ").strip().lower()
    balance_columns = (bal != 'n')

    # Only used for single column mode
    try:
        chars_per_line = int(input("Characters per line (single-column only, default: 120): ") or "120")
    except ValueError:
        chars_per_line = 120

    # Format
    fmt = input("Output format PNG/TIFF (default: PNG): ").strip().upper() or 'PNG'

    converter.convert_folder_to_image(
        folder_path, 
        output_path, 
        chars_per_line=chars_per_line,
        columns=columns,
        balance_columns=balance_columns,
        output_format=fmt
    )

if __name__ == "__main__":
    main()