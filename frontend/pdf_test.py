# pdf_test.py

import os
import logging
from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT  # Ensure TA_LEFT is imported
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Image,
    Paragraph,
    Spacer,
    ListFlowable,
    ListItem,
    KeepTogether
)
from reportlab.lib.units import inch
from io import BytesIO
import pandas as pd
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from bs4 import BeautifulSoup, NavigableString

def html_to_flowables(html_content, styles, base_indent=20, indent_increment=20):
    """
    Converts an HTML string into a list of ReportLab flowables.
    Handles headings, paragraphs, images, lists, and tables.

    Parameters:
    - html_content (str): The HTML content to parse.
    - styles (StyleSheet1): ReportLab stylesheet for styling.
    - base_indent (int): Base indentation for lists.
    - indent_increment (int): Indentation increment per nesting level.

    Returns:
    - List of ReportLab flowables.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    flowables = []

    def parse_list(list_tag, level=0):
        """
        Recursively parses <ul> or <ol> tags and returns a ListFlowable object.
        """
        items = []
        for li in list_tag.find_all('li', recursive=False):
            # Extract text without including text from nested lists
            li_text = li.get_text(separator=' ', strip=True)
            p = Paragraph(li_text, styles['ListItem'])

            # Check for nested lists within the current <li>
            nested_ul = li.find(['ul', 'ol'], recursive=False)
            if nested_ul:
                # Recursive call to handle nested lists
                nested_list = parse_list(nested_ul, level=level+1)
                # Combine Paragraph and nested list using KeepTogether to maintain layout
                list_item_flowables = [p, Spacer(1, 2), nested_list]
                list_item = ListItem(
                    KeepTogether(list_item_flowables),
                    leftIndent=base_indent + (level * indent_increment)
                )
            else:
                list_item = ListItem(
                    p,
                    leftIndent=base_indent + (level * indent_increment)
                )
            items.append(list_item)

        bullet_type = 'bullet' if list_tag.name == 'ul' else '1'
        return ListFlowable(
            items,
            bulletType=bullet_type,
            start='1' if list_tag.name == 'ol' else None,
            leftIndent=base_indent + (level * indent_increment),
            bulletFontName='Helvetica',
            bulletFontSize=10,
            bulletOffsetY=3
        )

    def parse_element(element, flowables_list=None):
        if flowables_list is None:
            flowables_list = flowables

        if isinstance(element, NavigableString):
            text = element.strip()
            if text:
                logging.debug(f"Adding paragraph: {text}")
                para = Paragraph(text, styles['CustomParagraph'])
                flowables_list.append(para)
            return

        if not hasattr(element, 'name'):
            # If the element doesn't have a name (e.g., comments), skip it
            return

        if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            style_name = f'CustomHeading{element.name[1]}'
            para = Paragraph(element.get_text(), styles.get(style_name, styles['CustomParagraph']))
            logging.debug(f"Adding {element.name}: {element.get_text()}")
            flowables_list.append(para)

        elif element.name == 'p':
            para = Paragraph(element.decode_contents(), styles['CustomParagraph'])
            logging.debug(f"Adding paragraph: {element.get_text()}")
            flowables_list.append(para)

        elif element.name == 'img':
            src = element.get('src')
            alt = element.get('alt', '')
            width = element.get('width', None)
            height = element.get('height', None)

            # Resolve the image path relative to the HTML content if necessary
            if not os.path.isabs(src):
                # Assuming the HTML content is in the current directory
                src = os.path.join(os.getcwd(), src)

            try:
                img = Image(src)
                if width:
                    img.drawWidth = float(width)
                if height:
                    img.drawHeight = float(height)
                flowables_list.append(img)
                flowables_list.append(Spacer(1, 0.2 * inch))
                logging.debug(f"Added image: {src}")
            except Exception as e:
                # If image loading fails, add alt text
                logging.warning(f"Failed to load image {src}: {e}")
                para = Paragraph(f"[Image: {alt}]", styles['CustomParagraph'])
                flowables_list.append(para)

        elif element.name in ['ul', 'ol']:
            # Parse the list and append the ListFlowable
            parsed_list = parse_list(element)
            flowables_list.append(parsed_list)
            flowables_list.append(Spacer(1, 0.1 * inch))
            logging.debug(f"Added list: {element.name}")

        elif element.name == 'br':
            flowables_list.append(Spacer(1, 0.1 * inch))
            logging.debug("Added line break")

        elif element.name in ['div', 'section', 'article']:
            for child in element.children:
                parse_element(child, flowables_list)

        elif element.name == 'table':
            # Simplistic table rendering
            data = []
            for row in element.find_all('tr'):
                row_data = []
                for cell in row.find_all(['td', 'th']):
                    row_data.append(cell.get_text())
                data.append(row_data)
            table = Table(data, hAlign='LEFT')
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), '#d3d3d3'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
            ]))
            # Alternate row colors
            for i in range(1, len(data)):
                bg_color = colors.whitesmoke if i % 2 != 0 else colors.lightgrey
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, i), (-1, i), bg_color),
                ]))
            flowables_list.append(table)
            flowables_list.append(Spacer(1, 0.2 * inch))
            logging.debug("Added table")

        else:
            # For any other tags, process children
            for child in element.children:
                parse_element(child, flowables_list)

    # **Important**: Traverse the soup and parse each top-level element
    for elem in soup.contents:
        parse_element(elem)

    return flowables

def generate_pdf(category_name, category_description, items_df, logo_filename):
    """
    Generates a PDF report for a given category with a table of items.

    Parameters:
    - category_name (str): The name of the category.
    - category_description (str): An HTML description of the category.
    - items_df (pd.DataFrame): DataFrame containing item details.
    - logo_filename (str): Filename of the logo image to include.

    Returns:
    - bytes: The generated PDF as a byte string.
    """

    # Remove redundant columns if they exist
    columns_to_remove = ['category_id', 'id']  # Adjust based on actual column names
    items_df = items_df.drop(columns=[col for col in columns_to_remove if col in items_df.columns], errors='ignore')

    # Replace 'quantity' column name with 'qty' if it exists
    if 'quantity' in items_df.columns:
        items_df = items_df.rename(columns={'quantity': 'qty'})

    # Create a BytesIO buffer to receive PDF data
    buffer = BytesIO()

    # Define the PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=LETTER,
        rightMargin=20,
        leftMargin=20,
        topMargin=20,
        bottomMargin=20,
    )

    elements = []

    # Register Helvetica font (optional, as it's usually available by default)
    # Uncomment the following lines if you have a custom font file
    # pdfmetrics.registerFont(TTFont('Helvetica', 'Helvetica.ttf'))

    # Define Styles
    styles = getSampleStyleSheet()

    # Added: Define CustomParagraph Style
    styles.add(ParagraphStyle(
        name='CustomParagraph',
        parent=styles['BodyText'],
        alignment=TA_LEFT,
        fontSize=12,
        leading=14,
        spaceAfter=10
    ))

    # Added: Define CustomHeading1 to CustomHeading6 Styles
    for i in range(1, 7):
        styles.add(ParagraphStyle(
            name=f'CustomHeading{i}',
            parent=styles['Heading1'],
            alignment=TA_LEFT,
            fontSize=18 - (i * 2),  # Example: h1 is larger than h2, etc.
            leading=22 - (i * 2),
            spaceAfter=10,
            fontName='Helvetica-Bold'
        ))

    styles.add(ParagraphStyle(
        name='CenterTitle',
        # alignment=TA_LEFT,  # Changed to left alignment to maintain consistency
        alignment=1,  # Center alignment
        fontSize=24,
        leading=28,
        spaceAfter=20
    ))
    styles.add(ParagraphStyle(
        name='TableHeader',
        alignment=TA_LEFT,  # Changed to left alignment
        fontSize=10,
        leading=12,
        fontName='Helvetica-Bold'
    ))
    styles.add(ParagraphStyle(
        name='TableCell',
        alignment=TA_LEFT,  # Changed to left alignment
        fontSize=10,
        leading=12
    ))
    styles.add(ParagraphStyle(
        name='NotesSubtitle',
        alignment=TA_LEFT,  # Left alignment
        fontSize=14,
        leading=16,
        fontName='Helvetica-Bold',
        spaceBefore=20,
        spaceAfter=10
    ))
    styles.add(ParagraphStyle(
        name='Description',
        alignment=TA_LEFT,  # Left alignment
        fontSize=12,
        leading=14
    ))
    styles.add(ParagraphStyle(
        name='ListItem',
        parent=styles['BodyText'],
        alignment=TA_LEFT,
        leftIndent=0,
        spaceAfter=5
    ))

    # Function to convert snake_case to Title Case
    def snake_to_title(snake_str):
        components = snake_str.split('_')
        return ' '.join(x.capitalize() for x in components)

    # Convert column headers from snake_case to Title Case
    formatted_columns = [snake_to_title(col) for col in items_df.columns]

    # Replace "Quantity" with "Qty" in the formatted column headers
    formatted_columns = ['Qty' if col.lower() == 'quantity' else col for col in formatted_columns]

    # Prepare Table Data
    data = [formatted_columns]  # Header row

    # Convert DataFrame rows to lists with string representation
    for _, row in items_df.iterrows():
        data.append([str(item) for item in row])

    # Define minimum column widths (in points)
    # Adjust these values based on your specific data and desired layout
    min_col_widths = {
        'Name': 110,
        'Updated At': 140,
        'Created At': 140,
        'Qty': 50,
        'Description': 200,
        # Add other columns with their minimum widths as needed
    }

    # Calculate column widths before converting to Paragraphs
    col_widths = []
    max_width = doc.width
    num_cols = len(formatted_columns)

    for idx, col in enumerate(formatted_columns):
        # Calculate the width of the header
        header_text = col
        header_width = pdfmetrics.stringWidth(header_text, 'Helvetica-Bold', 14)

        # Calculate the maximum width of the column based on content
        content_widths = [
            pdfmetrics.stringWidth(str(cell), 'Helvetica', 10) for cell in items_df.iloc[:, idx]
        ]
        max_content_width = max(content_widths) if content_widths else 0

        # Determine the maximum width needed for the column
        max_col_width = max(header_width, max_content_width)

        # Apply minimum width if specified
        if col in min_col_widths:
            max_col_width = max(max_col_width, min_col_widths[col])

        # Add padding
        col_width = max_col_width + 20  # 20 points padding
        col_widths.append(col_width)

    # Adjust column widths if total exceeds document width
    total_col_width = sum(col_widths)
    if total_col_width > doc.width:
        scale_factor = doc.width / total_col_width
        col_widths = [width * scale_factor for width in col_widths]

    # Convert all cells to Paragraphs to allow text wrapping
    for i in range(len(data)):
        for j in range(len(data[i])):
            # Avoid re-processing if already a Paragraph
            if isinstance(data[i][j], Paragraph):
                continue
            if i == 0:
                # Apply TableHeader style to headers
                p = Paragraph(data[i][j], styles['TableHeader'])
            else:
                # Apply TableCell style to other cells
                p = Paragraph(data[i][j], styles['TableCell'])
            data[i][j] = p

    # Create Table with Paragraphs
    table = Table(data, colWidths=col_widths, repeatRows=1, hAlign='CENTER')
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),  # Header background
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),  # Header text color
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Horizontal alignment for all cells
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Vertical alignment for all cells
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Header font
        ('FONTSIZE', (0, 0), (-1, 0), 14),  # Header font size
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ])
    table.setStyle(table_style)

    # Alternate row colors
    for i in range(1, len(data)):
        if i % 2 == 0:
            bg_color = colors.lightgrey
        else:
            bg_color = colors.whitesmoke
        table_style.add('BACKGROUND', (0, i), (-1, i), bg_color)
    table.setStyle(table_style)

    # Add Logo
    logo_path = logo_filename

    try:
        logo = Image(logo_path)
        logo.drawHeight = 50  # Adjust as needed
        logo.drawWidth = 100   # Adjust as needed
        logo.hAlign = 'LEFT'
        elements.append(logo)
    except Exception as e:
        # If logo loading fails, skip adding the logo or add placeholder text
        logging.warning(f"Failed to load logo {logo_path}: {e}")
        placeholder_para = Paragraph("[Logo Image]", styles['CustomParagraph'])
        elements.append(placeholder_para)
        elements.append(Spacer(1, 0.2 * inch))

    # Add Category Name
    elements.append(Spacer(1, 12))
    category_para = Paragraph(category_name, styles['CenterTitle'])
    elements.append(category_para)
    elements.append(Spacer(1, 24))

    # Add Table
    elements.append(table)
    elements.append(Spacer(1, 24))

    # Add "Notes:" Subtitle
    notes_subtitle = Paragraph("Notes:", styles['NotesSubtitle'])
    elements.append(notes_subtitle)

    # Add Category Description (HTML Rendering)
    if category_description:
        # Parse HTML and convert to flowables
        description_flowables = html_to_flowables(category_description, styles)
        if description_flowables:
            elements.extend(description_flowables)
            logging.debug("Added category_description flowables")
        else:
            logging.warning("No flowables generated from category_description")

    # Build PDF
    doc.build(elements)

    # Get PDF data
    pdf = buffer.getvalue()
    buffer.close()

    return pdf

# Example Usage
if __name__ == "__main__":
    # Sample DataFrame
    data = {
        'name': ['Widget A', 'Widget B', 'Widget C', 'Widget D'],
        'updated_at': ['2023-10-01 10:00', '2023-10-02 11:30', '2023-10-03 09:15', '2023-10-04 14:45'],
        'created_at': ['2023-09-25 08:00', '2023-09-26 09:30', '2023-09-27 10:45', '2023-09-28 12:00'],
        'quantity': [100, 150, 200, 250],  # This will be displayed as 'Qty' in the PDF
        'description': [
            'A high-quality widget that does many things.',
            'Another widget with a longer description that needs to wrap within the table cell to prevent overflow.',
            'Short desc.',
            'This widget has an intentionally long description to test how the table handles text wrapping and prevents overflow into adjacent columns.'
        ]
    }
    items_df = pd.DataFrame(data)

    # Parameters
    category_name = "Widget Category"
    category_description = """
    <p>This category includes various widgets that are essential for your daily tasks. Each widget is designed to provide optimal performance and reliability.</p>
    <h3>Features:</h3>
    <ul>
        <li>Supports headings</li>
        <li>Paragraphs and text formatting</li>
        <li>Images</li>
        <li>Lists
            <ul>
                <li>Nested list item 1</li>
                <li>Nested list item 2</li>
            </ul>
        </li>
        <li>Tables</li>
    </ul>
    <p>Ensure that all widgets are regularly maintained to guarantee their longevity and effectiveness.</p>
    """
    logo_filename = "frontend/logo.png"  # Ensure this file exists in the same directory

    # Generate PDF
    try:
        pdf_bytes = generate_pdf(category_name, category_description, items_df, logo_filename)
        # Save to file
        output_pdf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "category_report.pdf")
        with open(output_pdf_path, "wb") as f:
            f.write(pdf_bytes)
        print(f"PDF generated successfully and saved to {output_pdf_path}")
    except Exception as e:
        print(f"An error occurred while generating the PDF: {e}")
