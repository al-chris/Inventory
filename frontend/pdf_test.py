# pdf_test.py

import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Image,
    Paragraph,
    Spacer,
)
from reportlab.lib.units import inch
from io import BytesIO
import pandas as pd
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def generate_pdf(category_name, category_description, items_df, logo_filename):
    """
    Generates a PDF report for a given category with a table of items.

    Parameters:
    - category_name (str): The name of the category.
    - category_description (str): A description of the category.
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
    styles.add(ParagraphStyle(
        name='CenterTitle',
        alignment=1,  # Center alignment
        fontSize=24,
        leading=28,
        spaceAfter=20
    ))
    styles.add(ParagraphStyle(
        name='TableHeader',
        alignment=1,  # Center alignment
        fontSize=10,
        leading=12,
        fontName='Helvetica-Bold'
    ))
    styles.add(ParagraphStyle(
        name='TableCell',
        alignment=1,  # Center alignment
        fontSize=10,
        leading=12
    ))
    styles.add(ParagraphStyle(
        name='NotesSubtitle',
        alignment=0,  # Left alignment
        fontSize=14,
        leading=16,
        fontName='Helvetica-Bold',
        spaceBefore=20,
        spaceAfter=10
    ))
    styles.add(ParagraphStyle(
        name='Description',
        alignment=0,  # Left alignment
        fontSize=12,
        leading=14
    ))

    # Function to convert snake_case to Title Case
    def snake_to_title(snake_str):
        components = snake_str.split('_')
        return ' '.join(x.capitalize() for x in components)

    # Convert column headers from snake_case to Title Case
    formatted_columns = [snake_to_title(col) for col in items_df.columns]

    # Replace "Quantity" with "Qty" in the formatted column headers
    formatted_columns = ['Qty' if col == 'Quantity' else col for col in formatted_columns]

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

    # Create Table
    table = Table(data, colWidths=col_widths, repeatRows=1, hAlign='CENTER')

    # Define Table Style
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

    # Apply the style to the table
    table.setStyle(table_style)

    # Alternate row colors
    for i in range(1, len(data)):
        if i % 2 == 0:
            bg_color = colors.lightgrey
        else:
            bg_color = colors.whitesmoke
        table_style.add('BACKGROUND', (0, i), (-1, i), bg_color)

    # Allow text wrapping in cells by converting all cells to Paragraphs
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

    # Re-create the table with Paragraphs
    table = Table(data, colWidths=col_widths, repeatRows=1, hAlign='CENTER')
    table.setStyle(table_style)

    # Add Logo
    # current_dir = os.path.dirname(os.path.abspath(__file__))
    # logo_path = os.path.join(current_dir, logo_filename)

    # if not os.path.exists(logo_path):
    #     raise FileNotFoundError(f"Logo file '{logo_filename}' not found in the current directory.")
    logo_path = logo_filename

    logo = Image(logo_path)
    logo.drawHeight = 50  # Adjust as needed
    logo.drawWidth = 50   # Adjust as needed
    logo.hAlign = 'LEFT'
    elements.append(logo)

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

    # Add Category Description
    description_para = Paragraph(category_description, styles['Description'])
    elements.append(description_para)

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
    category_description = (
        "This category includes various widgets that are essential for your daily tasks. "
        "Each widget is designed to provide optimal performance and reliability."
    )
    logo_filename = "logo.png"  # Ensure this file exists in the same directory

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
