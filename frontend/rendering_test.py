from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, ListFlowable, ListItem, Table, TableStyle
)
from reportlab.lib.units import inch
from bs4 import BeautifulSoup, NavigableString
import os

def html_to_flowables(html_content):
    """
    Converts an HTML string into a list of ReportLab flowables.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    styles = getSampleStyleSheet()
    flowables = []

    # Define base indentation and indentation increment per nesting level
    base_indent = 20  # points
    indent_increment = 20  # points per level

    # Custom styles
    styles.add(ParagraphStyle(
        name='CustomHeading1',
        parent=styles['Heading1'],
        alignment=TA_LEFT,
        spaceAfter=14
    ))
    styles.add(ParagraphStyle(
        name='CustomHeading2',
        parent=styles['Heading2'],
        alignment=TA_LEFT,
        spaceAfter=12
    ))
    styles.add(ParagraphStyle(
        name='CustomParagraph',
        parent=styles['BodyText'],
        alignment=TA_JUSTIFY,
        spaceAfter=10
    ))
    styles.add(ParagraphStyle(
        name='ListItem',
        parent=styles['BodyText'],
        alignment=TA_LEFT,
        leftIndent=0,
        spaceAfter=5
    ))

    def parse_list(list_tag, styles, level=0):
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
                nested_list = parse_list(nested_ul, styles, level=level+1)
                list_item = ListItem(
                    [p, Spacer(0, 2), nested_list],
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
                para = Paragraph(text, styles['CustomParagraph'])
                flowables_list.append(para)
            return

        if not hasattr(element, 'name'):
            # If the element doesn't have a name (e.g., comments), skip it
            return

        if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            style_name = f'CustomHeading{element.name[1]}'
            para = Paragraph(element.get_text(), styles[style_name])
            flowables_list.append(para)

        elif element.name == 'p':
            para = Paragraph(element.decode_contents(), styles['CustomParagraph'])
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
            except Exception as e:
                # If image loading fails, add alt text
                para = Paragraph(f"[Image: {alt}]", styles['CustomParagraph'])
                flowables_list.append(para)

        elif element.name in ['ul', 'ol']:
            # Parse the list and append the ListFlowable
            parsed_list = parse_list(element, styles)
            flowables_list.append(parsed_list)
            flowables_list.append(Spacer(1, 0.1 * inch))

        elif element.name == 'br':
            flowables_list.append(Spacer(1, 0.1 * inch))

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
                ('GRID', (0, 0), (-1, -1), 1, 'black'),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ]))
            flowables_list.append(table)
            flowables_list.append(Spacer(1, 0.2 * inch))

        else:
            # For any other tags, process children
            for child in element.children:
                parse_element(child, flowables_list)

    # Start parsing from the body or the entire document
    body = soup.body if soup.body else soup
    for elem in body.children:
        parse_element(elem)

    return flowables

def render_html_to_pdf(html_string, output_path):
    """
    Renders an HTML string to a PDF file using ReportLab.
    """
    # Create a PDF buffer
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=72, leftMargin=72,
        topMargin=72, bottomMargin=18
    )

    # Convert HTML to flowables
    story = html_to_flowables(html_string)

    # Build the PDF
    doc.build(story)

# Example Usage
if __name__ == "__main__":
    sample_html = """
    <html>
    <body>
        <h1>Welcome to ReportLab PDF</h1>
        <p>This PDF is generated from an HTML string using ReportLab.</p>
        <h2>Features</h2>
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
        <p>Here is an image:</p>
        <img src="path_to_image.jpg" alt="Sample Image" width="200" height="100"/>
        <h2>Sample Table</h2>
        <table>
            <tr>
                <th>Item</th><th>Quantity</th><th>Price</th>
            </tr>
            <tr>
                <td>Apples</td><td>10</td><td>$1.00</td>
            </tr>
            <tr>
                <td>Oranges</td><td>5</td><td>$0.80</td>
            </tr>
        </table>
    </body>
    </html>
    """

    output_pdf = "output.pdf"
    render_html_to_pdf(sample_html, output_pdf)
    print(f"PDF generated successfully at {output_pdf}")
